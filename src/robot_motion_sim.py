#!/usr/bin/env python3
"""
Robot motion simulator - converts cmd_vel to Gazebo twist updates
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math
from gz.transport13 import Node as GazeboNode
from gz.msgs10.pose_pb2 import Pose as GazeboPose
from gz.msgs10.boolean_pb2 import Boolean

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

        # Gazebo Transport 节点，用于调用世界服务修改模型位姿。
        self.gz_node = GazeboNode()
        # Gazebo Harmonic 中设置指定模型世界位姿的服务地址。
        self.gz_set_pose = '/world/default/set_pose'
        
        # Timer for publishing odometry
        self.timer = self.create_timer(0.05, self.publish_odom_and_velocity)  # 20Hz
        
        self.counter = 0
        
        self.get_logger().info('Robot motion simulator started')
        self.get_logger().info('  - Subscribing to: /cmd_vel')
        self.get_logger().info('  - Publishing to: /odom')
        self.get_logger().info('  - Moving Gazebo model: wpv3')
    
    def cmd_vel_callback(self, msg):
        """Handle velocity commands from keyboard or other source"""
        self.vx = msg.linear.x
        self.vy = msg.linear.y
        self.vtheta = msg.angular.z

        # Initialize on first callback
        if self.last_update is None:
            self.get_logger().info(f'[CMD] First cmd_vel: vx={self.vx:.2f}, vtheta={self.vtheta:.2f}')
            self.last_update = self.get_clock().now()
    
    def publish_odom_and_velocity(self):
        """Publish odometry and forward velocity commands to Gazebo"""
        current_time = self.get_clock().now()

        if self.last_update is not None:
            dt = (current_time - self.last_update).nanoseconds / 1e9
            if 0 < dt <= 0.2:
                if abs(self.vtheta) < 0.001:
                    self.x += self.vx * math.cos(self.theta) * dt
                    self.y += self.vx * math.sin(self.theta) * dt
                else:
                    radius = self.vx / self.vtheta
                    self.x += radius * (
                        math.sin(self.theta + self.vtheta * dt) -
                        math.sin(self.theta)
                    )
                    self.y -= radius * (
                        math.cos(self.theta + self.vtheta * dt) -
                        math.cos(self.theta)
                    )
                    self.theta += self.vtheta * dt
                    self.theta = math.atan2(
                        math.sin(self.theta),
                        math.cos(self.theta)
                    )
        self.last_update = current_time
        
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
            q = euler_to_quaternion(0, 0, self.theta)
            # GazeboPose 对应 gz.msgs.Pose，用于描述模型的新世界位姿。
            pose = GazeboPose()
            pose.name = 'wpv3'
            pose.position.x = self.x
            pose.position.y = self.y
            pose.position.z = 0.20
            pose.orientation.x = q[0]
            pose.orientation.y = q[1]
            pose.orientation.z = q[2]
            pose.orientation.w = q[3]
            self.gz_node.request(
                self.gz_set_pose, #'/world/default/set_pose'
                pose,
                GazeboPose,  # 请求消息类型：Gazebo 位姿。
                Boolean,     # 响应消息类型：操作成功或失败。
                100          # 服务等待超时，单位为毫秒。
            )
            
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




