# WPR Robot Simulation - Quick Start Guide

## 🚀 快速开始（5分钟）

### 步骤 1: 编译
```bash
cd /home/user/wpr_WS
colcon build --packages-select wpr_simulation2
source install/setup.bash
```

### 步骤 2: 启动模拟器
```bash
ros2 launch wpr_simulation2 wpb_simple.launch.py
```

**预期结果**：
- Gazebo 窗口打开
- 机器人显示为圆柱体（浮在空中，不沉地）
- 书架显示在位置 (3, 0)
- 控制台显示"Entity creation successful"两次

### 步骤 3: 新终端中控制机器人
```bash
source /home/user/wpr_WS/install/setup.bash
ros2 run wpr_simulation2 keyboard_vel_cmd
```

### 步骤 4: 按键盘控制
- 按 `w` → 机器人应该在 Gazebo 中向前移动
- 按 `a` / `d` → 机器人向左/右移动
- 按 `q` / `e` → 机器人向左/右旋转
- 按 `space` → 机器人停止
- 按 `x` → 退出控制程序

---

## ✅ 验证清单

运行以下命令验证每个功能：

```bash
# 1. 检查桥接是否运行
ros2 node list | grep bridge
# ✓ 应该看到: /ros_gz_bridge

# 2. 检查话题是否发布
ros2 topic list | grep -E "cmd_vel|odom|scan"
# ✓ 应该看到: /cmd_vel, /odom, /scan, /clock

# 3. 检查订阅者数量
ros2 topic info /cmd_vel
# ✓ Subscribers: 1

# 4. 实时测试（新终端）
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.5}}'
# ✓ 机器人应该在 Gazebo 中移动
```

---

## 🔧 故障排查

| 问题 | 解决方案 |
|------|--------|
| **机器人看不见** | 检查 Gazebo 窗口，或运行 `colcon build` 重新编译 |
| **机器人沉到地上** | 修复已应用，重新启动 |
| **键盘控制无效** | 确保终端窗口有焦点，再试一次 |
| **障碍物看不见** | 在 Gazebo 中查看 (3, 0) 位置，或检查生成日志 |
| **话题缺失** | 重新启动启动器：`ros2 launch wpr_simulation2 wpb_simple.launch.py` |

---

## 📊 已修复的问题

✅ **Robot not moving** - 添加了 ros_gz_bridge  
✅ **Robot sinking** - 禁用了基座重力  
✅ **Obstacle missing** - 修复了生成参数  

详细信息见 [ROBOT_CONTROL.md](ROBOT_CONTROL.md)
