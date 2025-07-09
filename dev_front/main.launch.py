import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():
    # 工作目录
    work_dir = os.path.expanduser("~/dev_ws_A/src")

    # 1. hobot_audio 节点
    hobot_audio_node = ExecuteProcess(
        cmd=[
            '/bin/bash', '-c',
            f'''
            cd {work_dir} && \
            source /opt/tros/humble/setup.bash && \
            cp -r /opt/tros/$TROS_DISTRO/lib/hobot_audio/config/ . && \
            export GLOG_minloglevel=3 && \
            ros2 launch hobot_audio hobot_audio.launch.py
            '''
        ],
        cwd=work_dir,
        output='screen'
    )

    # 2. originbot_base 和 3. audio_control 节点
    audio_control_node = ExecuteProcess(
        cmd=[
            '/bin/bash', '-c',
            f'''
            cd {work_dir} && \
            source /opt/tros/humble/setup.bash && \
            ros2 launch originbot_base robot.launch.py & \
            colcon build --packages-select audio_control --symlink-install && \
            source install/setup.bash && \
            export GLOG_minloglevel=3 && \
            ros2 launch audio_control audio_control.launch.py
            '''
        ],
        cwd=work_dir,
        output='screen'
    )

   

    # 5. 人体跟踪 body_tracking_without_gesture 节点
    body_tracking_node = ExecuteProcess(
        cmd=[
            '/bin/bash', '-c',
            '''
            cd /userdata/dev_ws && \
            source install/setup.bash && \
            ros2 launch body_tracking body_tracking_without_gesture.launch.py
            '''
        ],
        cwd='/userdata/dev_ws',
        output='screen'
    )

    # 6. 摔倒检测 hobot_falldown_detection 节点
    falldown_detection_node = ExecuteProcess(
        cmd=[
            '/bin/bash', '-c',
            '''
            cd /opt/tros/humble/share/hobot_falldown_detection/launch && \
            source /opt/tros/humble/setup.bash && \
            ros2 launch hobot_falldown_detection hobot_falldown_detection.launch.py
            '''
        ],
        cwd='/opt/tros/humble/share/hobot_falldown_detection/launch',
        output='screen'
    )

    # 7. voice_command_node 节点
    voice_command_node = ExecuteProcess(
        cmd=[
            '/bin/bash', '-c',
            '''
            cd ~/dev_ws_A && \
            source install/setup.bash && \
            ros2 run voice_control voice_command_node
            '''
        ],
        cwd=os.path.expanduser("~/dev_ws_A"),
        output='screen'
    )  
    return LaunchDescription([
        hobot_audio_node,
        audio_control_node,
        body_tracking_node,
        falldown_detection_node,
        voice_command_node
    ])
