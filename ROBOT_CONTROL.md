# WPR Robot Simulation - Movement Control Guide

## 修复内容 ✅

已成功修复 **Robot not move** 问题，通过添加 `ros_gz_bridge` 建立 ROS 和 Gazebo 之间的通信桥接。

### 问题原因
- 机器人模型内部有 Gazebo 插件 (`libros_gz_sim_planar_move.so`) 订阅 `/cmd_vel` 话题
- 但缺少 `ros_gz_bridge` 节点来桥接 ROS Twist 消息和 Gazebo Twist 消息

### 修复方案
在 `launch/wpb_simple.launch.py` 中添加了 `ros_gz_bridge` 节点，实现以下映射：

```
ROS /cmd_vel (geometry_msgs/Twist) ←→ Gazebo /cmd_vel (gz.msgs.Twist)
Gazebo /odom (gz.msgs.Odometry) ←→ ROS /odom (nav_msgs/Odometry)
Gazebo /clock (gz.msgs.Clock) ←→ ROS /clock (rosgraph_msgs/Clock)
```

---

## 使用方法

### 1️⃣ 编译项目
```bash
cd /home/user/wpr_WS
colcon build --packages-select wpr_simulation2
source install/setup.bash
```

### 2️⃣ 启动模拟器
**终端1** - 启动 Gazebo 和机器人：
```bash
source /home/user/wpr_WS/install/setup.bash
ros2 launch wpr_simulation2 wpb_simple.launch.py
```

输出应该包含：
```
[parameter_bridge-5] [INFO] Creating ROS->GZ Bridge: [/cmd_vel ...]
[parameter_bridge-5] [INFO] Creating GZ->ROS Bridge: [/odom ...]
[parameter_bridge-5] [INFO] Creating GZ->ROS Bridge: [/clock ...]
```

### 3️⃣ 控制机器人移动
**终端2** - 使用键盘控制：
```bash
source /home/user/wpr_WS/install/setup.bash
ros2 run wpr_simulation2 keyboard_vel_cmd
```

**键盘命令：**
- `w` - 前进（加速）
- `s` - 后退（加速）
- `a` - 左移（加速）
- `d` - 右移（加速）
- `q` - 左转（加速）
- `e` - 右转（加速）
- `space` - 停止
- `x` - 退出

### 4️⃣ 验证运动
**终端3** - 查看话题和里程表数据：
```bash
source /home/user/wpr_WS/install/setup.bash

# 查看活跃话题
ros2 topic list

# 实时查看速度命令
ros2 topic echo /cmd_vel

# 实时查看里程表（机器人位置）
ros2 topic echo /odom

# 实时查看激光扫描
ros2 topic echo /scan
```

---

## 验证清单

✅ **桥接状态** - 检查 ros_gz_bridge 是否运行：
```bash
ros2 node list | grep bridge
# 输出: /ros_gz_bridge
```

✅ **话题连接** - 检查 `/cmd_vel` 是否有订阅者：
```bash
ros2 topic info /cmd_vel
# 输出应该显示有订阅者
```

✅ **里程表输出** - 检查 `/odom` 是否发布数据：
```bash
ros2 topic echo /odom -n 1
# 应该显示位置和速度信息
```

✅ **实时测试** - 直接发送速度命令：
```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.5}, angular: {z: 0.0}}'
# 机器人应该在 Gazebo 中移动
```

---

## 常见问题排查

### Q: 机器人仍然不动？
**A:** 检查以下几点：
1. 确保编译后运行 `source install/setup.bash`
2. 检查 Gazebo 窗口中是否加载了机器人（应该看到圆柱体机器人）
3. 检查终端日志中是否有错误信息
4. 确保 `ros_gz_bridge` 节点正在运行

### Q: 看不到机器人模型？
**A:** 机器人可能生成失败，检查：
```bash
# 查看生成日志
ros2 service call /spawn_entity ros_gz_sim/srv/CreateEntity '...'
```

### Q: 键盘控制没有响应？
**A:** 检查：
1. 话题是否发布：`ros2 topic echo /cmd_vel`
2. 是否有订阅者：`ros2 topic info /cmd_vel`
3. 尝试重启 `keyboard_vel_cmd` 节点

---

## 修改的文件

📝 **launch/wpb_simple.launch.py**
- 添加了 `ros_gz_bridge` 参数桥接节点
- 配置了 `/cmd_vel`, `/odom`, `/clock` 话题的双向桥接

## 技术细节

### ros_gz_bridge 话题映射格式
```
/topic_name@ROS_MsgType]GZ_MsgType     # ROS to Gazebo
/topic_name@ROS_MsgType[GZ_MsgType     # Gazebo to ROS (双向)
```

### 机器人插件
- **base_controller** (`libros_gz_sim_planar_move.so`) - 处理平面运动
- **laser_link** (`libros_gz_sim_ray_sensor.so`) - LIDAR 传感器
- **kinect2** (`libros_gz_sim_camera.so`) - 深度摄像头
- **imu_sensor** (`libros_gz_sim_imu_sensor.so`) - IMU 传感器

---

## 更多资源

- [ROS 2 Gazebo Bridge 文档](https://github.com/gazebosim/ros_gz)
- [ROS 2 话题通信](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html)
- 项目 README: [README.md](README.md)
