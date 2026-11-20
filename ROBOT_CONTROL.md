# WPR Robot Simulation - Movement Control Guide

## 修复内容 ✅

已成功修复以下问题：

### 1️⃣ Robot not move（机器人不动）
**原因**: 缺少 `ros_gz_bridge` 节点连接 ROS 和 Gazebo

**修复**: 在 `launch/wpb_simple.launch.py` 中添加了 `parameter_bridge` 节点
```
ROS /cmd_vel ←→ Gazebo /cmd_vel
Gazebo /odom ←→ ROS /odom
Gazebo /clock ←→ ROS /clock
```

### 2️⃣ Robot sinking to ground（机器人沉到地上）
**原因**: `libros_gz_sim_planar_move` 插件使用直接位置控制，不适合重力模拟

**修复**: 在 `models/wpb_home_lidar.model` 中禁用基座链接的重力
```xml
<gazebo reference="base_link">
  <gravity>false</gravity>
</gazebo>
<gazebo reference="base_footprint">
  <gravity>false</gravity>
</gazebo>
```

### 3️⃣ Obstacle disappearing（障碍物消失）
**原因**: 对象生成路径格式错误，参数列表嵌套不当

**修复**: 在 `launch/wpb_simple.launch.py` 中修复了障碍物生成的参数格式和添加了 Z 坐标
```python
arguments=[
    '-file', os.path.join(..., 'bookshelft.model'),  # 路径不嵌套在列表中
    '-name', 'bookshelft_01',
    '-x', '3.0',
    '-y', '0.0',
    '-z', '0.3',  # 确保正确的高度
    '-Y', '3.1415926'
]
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

**预期输出（表示成功）**：
```
[create-3] [INFO] Entity creation successful.          # Robot
[create-4] [INFO] Entity creation successful.          # Bookshelf
[parameter_bridge-5] [INFO] Creating ROS->GZ Bridge: [/cmd_vel ...]
[parameter_bridge-5] [INFO] Creating GZ->ROS Bridge: [/odom ...]
[parameter_bridge-5] [INFO] Creating GZ->ROS Bridge: [/clock ...]
```

在 Gazebo 窗口中应该看到：
- ✅ 机器人圆柱体悬浮在空中（不沉到地上）
- ✅ 书架障碍物在位置 (3.0, 0.0, 0.3)
- ✅ 灰色地面

### 3️⃣ 控制机器人移动
**终端2** - 使用键盘控制：
```bash
source /home/user/wpr_WS/install/setup.bash
ros2 run wpr_simulation2 keyboard_vel_cmd
```

**键盘命令**：
```
w - 前进（加速）         s - 后退（加速）
a - 左移（加速）         d - 右移（加速）
q - 左转（加速）         e - 右转（加速）
space - 停止             x - 退出
```

现在机器人应该在 Gazebo 中平滑地移动！🤖

### 4️⃣ 验证和监控
**终端3** - 查看数据：
```bash
source /home/user/wpr_WS/install/setup.bash

# 查看活跃话题
ros2 topic list

# 实时查看速度命令
ros2 topic echo /cmd_vel

# 实时查看里程表（机器人位置和速度）
ros2 topic echo /odom

# 实时查看激光扫描
ros2 topic echo /scan
```

---

## 验证清单

| 检查项 | 命令 | 预期结果 |
|------|------|--------|
| **桥接状态** | `ros2 node list \| grep bridge` | `/ros_gz_bridge` |
| **话题连接** | `ros2 topic info /cmd_vel` | 有订阅者 (1 subscriber) |
| **里程表** | `ros2 topic echo /odom -n 1` | 显示位置和速度信息 |
| **实时测试** | `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.5}}'` | 机器人在 Gazebo 中移动 |

---

## 常见问题排查

### Q: 机器人仍然不动？
**A:** 检查以下几点：
1. ✓ 确保编译后运行 `source install/setup.bash`
2. ✓ 检查 Gazebo 窗口中是否加载了机器人（应该看到悬浮的圆柱体）
3. ✓ 检查终端日志中是否有错误信息
4. ✓ 确保 `ros_gz_bridge` 节点正在运行

### Q: 看不到机器人模型？
**A:** 机器人可能生成失败，检查日志：
```bash
# 查看完整输出
ros2 launch wpr_simulation2 wpb_simple.launch.py 2>&1 | grep -E "Entity|ERROR|ERROR"
```

### Q: 机器人还是沉到地上？
**A:** 确保修改已生效：
```bash
# 检查模型文件中是否有重力禁用配置
grep -A 2 "reference=\"base_link\"" models/wpb_home_lidar.model | grep gravity
```

### Q: 键盘控制没有响应？
**A:** 检查：
1. ✓ 话题是否发布：`ros2 topic echo /cmd_vel`
2. ✓ 是否有订阅者：`ros2 topic info /cmd_vel`
3. ✓ 尝试重启 `keyboard_vel_cmd` 节点

### Q: 障碍物看不见？
**A:** 检查生成日志：
```bash
# 在启动输出中查找
grep -i "bookshelft" /path/to/launch/output
# 应该显示 "Entity creation successful"
```

---

## 修改的文件

| 文件 | 修改内容 |
|------|--------|
| `launch/wpb_simple.launch.py` | 添加 ros_gz_bridge + 修复障碍物生成参数 |
| `models/wpb_home_lidar.model` | 禁用基座重力（防止沉地） |

---

## 技术细节

### libros_gz_sim_planar_move 插件
- **功能**: 直接控制平面运动（2D + 旋转）
- **特点**: 不受物理引擎影响，适合移动机器人
- **限制**: 需要禁用重力和碰撞物理

### ros_gz_bridge 话题映射
```
/topic_name@ROS_MsgType]GZ_MsgType     # ROS to Gazebo
/topic_name@ROS_MsgType[GZ_MsgType     # Gazebo to ROS (双向)
```

---

## 更多资源

- [ROS 2 Gazebo Bridge 文档](https://github.com/gazebosim/ros_gz)
- [ROS 2 话题通信](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html)
- 项目 README: [README.md](README.md)

