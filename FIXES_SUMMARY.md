# 修复总结 - WPR Robot Simulation

## 问题描述

用户在运行 `ros2 launch wpr_simulation2 wpb_simple.launch.py` 后遇到三个问题：

1. **Robot not move**: `ros2 run wpr_simulation2 keyboard_vel_cmd` 无法控制机器人移动
2. **Robot sinking**: 机器人沉到地面
3. **Obstacle missing**: 书架障碍物消失不见

---

## 根本原因分析

### 问题 1: Robot not move

**根本原因**：缺少 ROS ↔ Gazebo 通信桥接

- 机器人模型内部的 Gazebo 插件 (`libros_gz_sim_planar_move.so`) 订阅 `/cmd_vel` 话题
- 但这是 Gazebo 内部的话题，不连接到 ROS
- ROS 中的 `keyboard_vel_cmd` 发布消息到 ROS `/cmd_vel`，但无法到达 Gazebo

**解决方案**：添加 `ros_gz_bridge` 节点

```python
# launch/wpb_simple.launch.py
ros_gz_bridge_cmd = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=[
        '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
        '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
    ]
)
```

---

### 问题 2: Robot sinking

**根本原因**：`libros_gz_sim_planar_move` 插件使用直接位置控制（Kinematic mode）

- 该插件不受物理引擎影响，直接设置机器人的位置
- 但机器人的 `body_link` 仍然受重力影响
- 结果：机器人往下沉直到与地面碰撞

**解决方案**：禁用基座链接的重力

```xml
<!-- models/wpb_home_lidar.model -->
<gazebo reference="base_link">
  <gravity>false</gravity>
</gazebo>
<gazebo reference="base_footprint">
  <gravity>false</gravity>
</gazebo>
```

**原理**：
- `base_link` 和 `base_footprint` 是机器人的根链接（由 planar_move 插件控制）
- 禁用它们的重力，但保持其他链接（body, sensors）的重力
- 这样机器人可以正常移动而不会沉地

---

### 问题 3: Obstacle missing

**根本原因**：Gazebo 生成服务参数格式错误

原始代码：
```python
arguments=['-file', [os.path.join(...)] , '-name', 'bookshelft_01', ...]
                     ↑
              参数被嵌套在列表中，导致路径解析错误
```

**解决方案**：修复参数格式并添加 Z 坐标

```python
arguments=[
    '-file', os.path.join(get_package_share_directory('wpr_simulation2'), 'models', 'bookshelft.model'),
    '-name', 'bookshelft_01',
    '-x', '3.0',
    '-y', '0.0',
    '-z', '0.3',  # 确保正确的高度
    '-Y', '3.1415926'
]
```

**验证**：启动时日志应显示
```
[create-4] [INFO] Entity creation successful.    # 书架生成成功
```

---

## 修改的文件

### 1. `launch/wpb_simple.launch.py`

**变更**：
- 添加 `ros_gz_bridge` 节点用于 ROS ↔ Gazebo 通信
- 修复 `spawn_bookshelft` 的参数格式
- 添加 `-z 0.3` 参数确保书架正确高度
- 添加 `output='screen'` 便于调试

**代码片段**：
```python
# 添加了这个
ros_gz_bridge_cmd = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    output='screen',
    arguments=[
        '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
        '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
    ]
)

# 修改了这个
spawn_bookshelft = Node(
    package='ros_gz_sim',
    executable='create',
    arguments=[
        '-file', os.path.join(..., 'bookshelft.model'),  # 不再嵌套
        '-z', '0.3',  # 添加了这个
    ]
)

# 在 ld 中添加
ld.add_action(ros_gz_bridge_cmd)
```

### 2. `models/wpb_home_lidar.model`

**变更**：在 Gazebo 插件部分后添加重力禁用配置

**代码片段**：
```xml
<!-- 现有的插件配置... -->
</gazebo>

<!-- 添加了这个 -->
<gazebo reference="base_link">
  <gravity>false</gravity>
</gazebo>

<gazebo reference="base_footprint">
  <gravity>false</gravity>
</gazebo>
```

---

## 验证步骤

### 编译
```bash
cd /home/user/wpr_WS
colcon build --packages-select wpr_simulation2
source install/setup.bash
```

### 启动
```bash
ros2 launch wpr_simulation2 wpb_simple.launch.py
```

**检查点**：
1. ✅ 两个"Entity creation successful"消息
2. ✅ 三个"Creating ROS->GZ Bridge"消息
3. ✅ Gazebo 窗口中看到浮起的机器人和书架

### 控制
```bash
# 新终端
source /home/user/wpr_WS/install/setup.bash
ros2 run wpr_simulation2 keyboard_vel_cmd
```

**按键测试**：
- `w` - 机器人前进 ✅
- `a/d` - 机器人平移 ✅
- `q/e` - 机器人旋转 ✅
- `space` - 停止 ✅

---

## 技术背景

### ros_gz_bridge 的工作原理

ROS 和 Gazebo 使用不同的中间件通信：
- **ROS 2**: DDS (Data Distribution Service) / FastRTPS
- **Gazebo**: Gazebo Transport

`ros_gz_bridge` 的作用：
```
ROS 话题 ←→ ros_gz_bridge ←→ Gazebo 话题
```

参数格式：
- `/topic@ROS_Type]GZ_Type` - ROS to Gazebo (单向)
- `/topic@ROS_Type[GZ_Type` - Gazebo to ROS (单向)
- `/topic@ROS_Type=GZ_Type` - 双向（ROS 2 Humble+）

### libros_gz_sim_planar_move 插件

这是一个特殊的 Gazebo 插件，用于移动机器人模拟：

**特点**：
- ✅ 直接控制平面运动（x, y, θ）
- ✅ 不受物理约束影响
- ✅ 适合差分驱动轮式机器人
- ❌ 不能模拟轮子接触动力学
- ❌ 需要禁用链接重力

**工作流**：
1. 接收 `cmd_vel` 中的速度命令
2. 计算新位置（基于速度和时间步长）
3. 直接在 Gazebo 中设置机器人位置和方向
4. 发布里程计 `/odom` 话题

---

## 相关文件版本

编译后的结构：
```
/home/user/wpr_WS/
├── install/
│   └── wpr_simulation2/           # 已安装的包
├── build/
│   └── wpr_simulation2/           # 构建输出
├── src/
│   └── wpr_simulation2-main/      # 源代码
│       ├── launch/
│       │   └── wpb_simple.launch.py      # ✏️ 已修改
│       ├── models/
│       │   └── wpb_home_lidar.model      # ✏️ 已修改
│       ├── ROBOT_CONTROL.md              # ✨ 新增
│       └── QUICK_START.md                # ✨ 新增
```

---

## 后续改进建议

1. **添加 nav2 集成** - 实现自主导航
2. **添加 SLAM** - 实现地图构建和定位
3. **改进物理模型** - 使用实际的轮子受力而不是直接位置控制
4. **多机器人支持** - 同时模拟多个机器人
5. **传感器模拟** - 改进摄像头和激光的逼真度

---

## 参考资源

- [ROS 2 Gazebo Bridge](https://github.com/gazebosim/ros_gz)
- [ROS 2 Humble 文档](https://docs.ros.org/en/humble/)
- [Gazebo SDF 格式](https://gazebosim.org/docs/garden/sdf_worlds/)

