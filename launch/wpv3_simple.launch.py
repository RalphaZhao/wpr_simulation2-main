#!/usr/bin/env python3
#
# Copyright 2023 6-robot.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    launch_file_dir = os.path.join(get_package_share_directory('wpr_simulation2'), 'launch')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    world = os.path.join(
        get_package_share_directory('wpr_simulation2'),
        'worlds',
        'wpb_simple.world'
    )

    gz_sim_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r "{world}"'}.items()
    )

    # Spawn wpv3 robot
    spawn_robot_cmd = Node(
            package='ros_gz_sim',
            namespace='',
            executable='create',
            name='spawn_wpv3',
            arguments=[
                '-file', os.path.join(get_package_share_directory('wpr_simulation2'), 'models', 'wpv3.model'),
                '-name', 'wpv3',
                '-x', '0.0',
                '-y', '0.0',
                '-z', '0.0',
            ],
            output='screen'
        )

    # Robot state publisher for wpv3
    robot_state_publisher_cmd = Node(
            package='robot_state_publisher',
            namespace='',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            arguments=['--ros-args', '-p', 'robot_description:=<robot name="wpv3"></robot>']
        )

    # Bridge to connect ROS topics with Gazebo
    ros_gz_bridge_cmd = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            output='screen',
            arguments=[
                # Clock messages - subscribe from Gazebo to sync time
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                # Velocity commands - subscribe from ROS, publish to Gazebo
                '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                # Robot pose - subscribe from Gazebo, publish to ROS for visualization
                '/model/wpv3/pose[gz.msgs.Pose>geometry_msgs/msg/Pose',
            ]
        )

    # Robot motion simulator - provides odometry from cmd_vel
    robot_motion_sim_cmd = Node(
            package='wpr_simulation2',
            executable='robot_motion_sim.py',
            name='robot_motion_sim',
            output='screen'
        )

    ld = LaunchDescription()

    # Add the commands to the launch description
    ld.add_action(gz_sim_cmd)
    ld.add_action(spawn_robot_cmd)
    ld.add_action(ros_gz_bridge_cmd)
    ld.add_action(robot_motion_sim_cmd)

    return ld
