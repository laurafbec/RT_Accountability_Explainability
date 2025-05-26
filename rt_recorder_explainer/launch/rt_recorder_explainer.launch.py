import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    config = os.path.join(
        get_package_share_directory('rt_recorder_explainer'),
        'config',
        'bc_rates.yaml'
        )

    return LaunchDescription([
        Node(
            package='rt_recorder_explainer',
            executable='kafka_producer_node',
            output='screen',
            parameters = [config],
            arguments=['--ros-args', '--log-level', 'info']
        )
    ])