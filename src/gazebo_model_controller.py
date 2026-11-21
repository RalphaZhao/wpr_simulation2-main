#!/usr/bin/env python3
"""
Gazebo Model Controller - Updates Gazebo model pose based on ROS topics
This node subscribes to /model/<model_name>/pose and uses Gazebo services to update the actual model position
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose
import subprocess
import math

class GazeboModelController(Node):
    def __init__(self):
        super().__init__('gazebo_model_controller')
        
        self.model_name = 'wpb_home'
        self.last_pose = None
        
        # Subscribe to the pose topic
        self.pose_sub = self.create_subscription(
            Pose, f'/model/{self.model_name}/pose', self.pose_callback, 10)
        
        self.counter = 0
        
        self.get_logger().info(f'Gazebo Model Controller started for model: {self.model_name}')
        self.get_logger().info(f'Subscribing to: /model/{self.model_name}/pose')
        self.get_logger().info('Using gz service to update model position in Gazebo')
    
    def pose_callback(self, msg):
        """Receive pose and update Gazebo model"""
        self.counter += 1
        
        # Only update periodically to reduce overhead
        if self.counter % 2 == 0:  # Update every 2nd message
            try:
                x = msg.position.x
                y = msg.position.y
                z = msg.position.z
                
                # Quaternion to RPY
                qx = msg.orientation.x
                qy = msg.orientation.y
                qz = msg.orientation.z
                qw = msg.orientation.w
                
                # Convert quaternion to yaw (since we only care about rotation around z)
                yaw = math.atan2(2.0*(qw*qz + qx*qy), 1.0 - 2.0*(qy*qy + qz*qz))
                
                # Use gz service to update model pose
                # Format: gz service /world/<world_name>/set_pose [args]
                # Try to get world name first
                try:
                    result = subprocess.run(
                        ['gz', 'world', 'list'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if result.returncode == 0 and result.stdout:
                        world_name = result.stdout.strip().split('\n')[0]
                    else:
                        world_name = 'default'
                except:
                    world_name = 'default'
                
                # Call gz service to set model pose
                # This is the proper way to update model position in Gazebo Sim
                cmd = [
                    'gz', 'service',
                    '-s', '/world/' + world_name + '/set_pose',
                    '--req', 
                    f'name: "{self.model_name}", pose: {{position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{x: 0, y: 0, z: {math.sin(yaw/2)}, w: {math.cos(yaw/2)}}}}}'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                
                if self.counter % 20 == 0:
                    self.get_logger().info(f'Updated {self.model_name} pose to ({x:.2f}, {y:.2f}, yaw={yaw:.2f})')
                
            except subprocess.TimeoutExpired:
                # Timeout - Gazebo service might not be ready
                pass
            except Exception as e:
                if self.counter % 100 == 0:
                    self.get_logger().warn(f'Error updating model: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = GazeboModelController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
