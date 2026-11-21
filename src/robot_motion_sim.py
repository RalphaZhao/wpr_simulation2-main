#!/usr/bin/env python3
"""
Robot motion simulator - converts cmd_vel to Gazebo twist updates
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Pose
from nav_msgs.msg import Odometry
import math

def euler_to_quaternion(roll, pitch, yaw):
    """Convert Euler angles to quaternion"""
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    
    q = [0] * 4
    q[3] = cy * cp * cr + sy * sp * sr  # w
    q[0] = cy * cp * sr - sy * sp * cr  # x
    q[1] = sy * cp * sr + cy * sp * cr  # y
    q[2] = sy * cp * cr - cy * sp * sr  # z
    
    return q

class RobotMotionSim(Node):
    def __init__(self):
        super().__init__('robot_motion_sim')
        
        # Robot state (odometry calculation)
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        # Velocity commands from cmd_vel
        self.vx = 0.0
        self.vy = 0.0
        self.vtheta = 0.0
        
        # Timing
        self.last_update = None
        
        # Create subscribers and publishers
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        self.odom_pub = self.create_publisher(
            Odometry, '/odom', 10)
        
        # Publisher for Gazebo entity pose (using Gazebo native topics)
        # Gazebo Sim expects pose updates on /model/<model_name>/pose topic
        self.gazebo_pose_pub = self.create_publisher(
            Pose, '/model/wpb_home/pose', 10)
        
        # Publisher for velocity commands to Gazebo
        self.gazebo_vel_pub = self.create_publisher(
            Twist, '/model/wpb_home/cmd_vel', 10)
        
        # Also publish to /cmd_vel for Gazebo's planar_move plugin
        self.cmd_vel_pub = self.create_publisher(
            Twist, '/cmd_vel', 10)
        
        # Timer for publishing odometry
        self.timer = self.create_timer(0.05, self.publish_odom_and_velocity)  # 20Hz
        
        self.counter = 0
        
        self.get_logger().info('Robot motion simulator started')
        self.get_logger().info('  - Subscribing to: /cmd_vel')
        self.get_logger().info('  - Publishing to: /odom, /model/wpb_home/pose, /model/wpb_home/cmd_vel, /cmd_vel')
    
    def cmd_vel_callback(self, msg):
        """Handle velocity commands from keyboard or other source"""
        self.vx = msg.linear.x
        self.vy = msg.linear.y
        self.vtheta = msg.angular.z
        
        current_time = self.get_clock().now()
        
        # Initialize on first callback
        if self.last_update is None:
            self.get_logger().info(f'[CMD] First cmd_vel: vx={self.vx:.2f}, vtheta={self.vtheta:.2f}')
            self.last_update = current_time
            return
        
        # Calculate dt from last update
        dt = (current_time - self.last_update).nanoseconds / 1e9
        self.last_update = current_time
        
        # Skip updates with invalid dt
        if dt <= 0:
            return
        
        # Clamp dt
        if dt > 2.0:
            dt = 2.0
        
        # Update odometry based on kinematics
        if abs(self.vtheta) < 0.001:
            # Pure translation
            self.x += self.vx * math.cos(self.theta) * dt
            self.y += self.vx * math.sin(self.theta) * dt
        else:
            # Rotation and translation
            radius = self.vx / self.vtheta if abs(self.vtheta) > 0.001 else 0
            if abs(radius) > 0.001:
                self.x += radius * (math.sin(self.theta + self.vtheta * dt) - 
                                   math.sin(self.theta))
                self.y -= radius * (math.cos(self.theta + self.vtheta * dt) - 
                                   math.cos(self.theta))
            
        self.theta += self.vtheta * dt
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
        
        # Log motion
        if abs(self.vx) > 0.001 or abs(self.vtheta) > 0.001:
            self.get_logger().info(f'[ODOM] x={self.x:.2f}, y={self.y:.2f}, theta={self.theta:.2f}')
    
    def publish_odom_and_velocity(self):
        """Publish odometry and forward velocity commands to Gazebo"""
        current_time = self.get_clock().now()
        
        # Publish odometry
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'
        
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        
        q = euler_to_quaternion(0, 0, self.theta)
        odom.pose.pose.orientation.x = q[0]
        odom.pose.pose.orientation.y = q[1]
        odom.pose.pose.orientation.z = q[2]
        odom.pose.pose.orientation.w = q[3]
        
        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.linear.y = self.vy
        odom.twist.twist.linear.z = 0.0
        
        odom.twist.twist.angular.x = 0.0
        odom.twist.twist.angular.y = 0.0
        odom.twist.twist.angular.z = self.vtheta
        
        # Set covariance
        odom.pose.covariance[0] = 0.0001
        odom.pose.covariance[7] = 0.0001
        odom.pose.covariance[14] = 0.0001
        odom.pose.covariance[21] = 0.01
        odom.pose.covariance[28] = 0.01
        odom.pose.covariance[35] = 0.01
        
        self.odom_pub.publish(odom)
        
        # Forward commands to Gazebo
        try:
            # Send position directly to Gazebo
            pose = Pose()
            pose.position.x = self.x
            pose.position.y = self.y
            pose.position.z = 0.0
            
            q = euler_to_quaternion(0, 0, self.theta)
            pose.orientation.x = q[0]
            pose.orientation.y = q[1]
            pose.orientation.z = q[2]
            pose.orientation.w = q[3]
            
            self.gazebo_pose_pub.publish(pose)
            
            # Also send velocity for physics simulation
            vel_cmd = Twist()
            vel_cmd.linear.x = self.vx
            vel_cmd.linear.y = self.vy
            vel_cmd.linear.z = 0.0
            vel_cmd.angular.x = 0.0
            vel_cmd.angular.y = 0.0
            vel_cmd.angular.z = self.vtheta
            
            self.gazebo_vel_pub.publish(vel_cmd)
            # Publish to /cmd_vel for Gazebo's planar_move plugin
            self.cmd_vel_pub.publish(vel_cmd)
            
            # Debug logging
            self.counter += 1
            if self.counter % 20 == 0 and (abs(self.vx) > 0.001 or abs(self.vtheta) > 0.001):
                self.get_logger().info(f'[GAZEBO] Pose: ({self.x:.2f}, {self.y:.2f}), Vel: vx={self.vx:.2f}, vtheta={self.vtheta:.2f}')
        
        except Exception as e:
            self.get_logger().error(f'[ERROR] Failed to publish to Gazebo: {e}')



def main(args=None):
    rclpy.init(args=args)
    node = RobotMotionSim()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()




