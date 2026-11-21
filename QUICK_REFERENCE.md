# 🚀 Quick Reference - Robot Motion Control

## ✅ Status: FULLY WORKING

---

## Get Started (30 seconds)

### Terminal 1: Launch Simulation
```bash
cd ~/wpr_WS && source install/setup.bash
ros2 launch wpr_simulation2 wpb_simple.launch.py
# OR for WPV3:
# ros2 launch wpr_simulation2 wpv3_simple.launch.py
```

### Terminal 2: Keyboard Control
```bash
cd ~/wpr_WS && source install/setup.bash
ros2 run wpr_simulation2 keyboard_vel_cmd
```

Then press **`w`** to move robot forward! ✨

---

## Keyboard Controls

| Key | Action | Current Status |
|-----|--------|-----------------|
| `w` | Forward | ✅ WORKING |
| `s` | Backward | ✅ WORKING |
| `a` | Left strafe | ✅ WORKING |
| `d` | Right strafe | ✅ WORKING |
| `q` | Rotate left | ✅ WORKING |
| `e` | Rotate right | ✅ WORKING |
| `space` | Brake/Stop | ✅ WORKING |
| `x` | Exit | ✅ WORKING |

---

## Programmatic Control

### Single Velocity Command
```bash
ros2 topic pub -1 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {z: 0.0}}"
```

### Forward at different speeds
```bash
# Slow (0.2 m/s)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}"

# Normal (0.5 m/s)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}"

# Fast (1.0 m/s)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}}"
```

### Rotation only
```bash
# Rotate left at 1.0 rad/s
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{angular: {z: 1.0}}"

# Rotate right at 1.0 rad/s
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{angular: {z: -1.0}}"
```

### Combined motion
```bash
# Forward + rotate (arc motion)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.5}}"
```

---

## Verify Everything is Working

### Check Robot Moving
```bash
# Terminal 1
ros2 launch wpr_simulation2 wpb_simple.launch.py

# Terminal 2
ros2 topic pub -1 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {z: 0.0}}"

# Terminal 3 - Watch position increment
ros2 topic echo /odom --field pose.pose.position.x
```

Expected output (position should increment):
```
62.675
---
62.700
---
62.725
---
62.750
---
```

### Check Odometry Publishing
```bash
ros2 topic echo /odom -n 1
```

Should show velocity and position data.

### Check TF Transforms
```bash
ros2 topic echo /tf
# Should show transformations between odom → base_link
```

---

## Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| Robot not moving | Is `/cmd_vel` being published? | `ros2 topic echo /cmd_vel` |
| No velocity response | Is Gazebo running? | Check launch output |
| Odometry not updating | Is robot_motion_sim running? | `ros2 node list \| grep motion` |
| Velocity too fast/slow | Adjust velocity values | Use values 0.1 to 1.0 m/s |

---

## Available Robots

| Robot | Launch Command | Status |
|-------|-----------------|--------|
| WPB (default) | `ros2 launch wpr_simulation2 wpb_simple.launch.py` | ✅ |
| WPV3 | `ros2 launch wpr_simulation2 wpv3_simple.launch.py` | ✅ |
| WPB with LIDAR | `ros2 launch wpr_simulation2 spawn_wpb_lidar.launch.py` | ✅ |
| WPB with Manipulator | `ros2 launch wpr_simulation2 wpb_mani.launch.py` | ✅ |

---

## ROS Topics

| Topic | Type | Direction | Purpose |
|-------|------|-----------|---------|
| `/cmd_vel` | Twist | ROS → Gazebo | Send motion commands |
| `/odom` | Odometry | Gazebo → ROS | Robot position/velocity feedback |
| `/tf` | Transforms | Gazebo → ROS | Robot frame transformations |
| `/clock` | Clock | Gazebo → ROS | Simulation time sync |

---

## Verify Installation

```bash
# Check ROS is installed
ros2 --version

# Check simulation package
ros2 pkg list | grep wpr_simulation2

# Check executable
ros2 run wpr_simulation2 keyboard_vel_cmd --help

# Build if needed
cd ~/wpr_WS && colcon build
```

---

## Save This for Later

**Documentation files:**
- `ROBOT_MOTION_COMPLETE_GUIDE.md` - Full architecture & detailed guide
- `WPV3_MOTION_FIX_COMPLETE.md` - WPV3-specific documentation
- `ROBOT_MOVEMENT_FIX.md` - WPB motion fix details

**Key source files:**
- `launch/wpb_simple.launch.py` - WPB launch configuration
- `launch/wpv3_simple.launch.py` - WPV3 launch configuration
- `src/robot_motion_sim.py` - Odometry calculation
- `models/wpb_home.model` - WPB robot definition
- `models/wpv3.model` - WPV3 robot definition

---

## Need Help?

```bash
# View all ROS nodes
ros2 node list

# View all topics
ros2 topic list

# Monitor specific topic
ros2 topic echo /cmd_vel

# Check node details
ros2 node info /gazebo

# View launch files
ls ~/wpr_WS/src/wpr_simulation2-main/launch/

# Check git history
cd ~/wpr_WS/src/wpr_simulation2-main
git log --oneline | head -10
```

---

## ✨ You're All Set!

The robots are ready to move. Start with the **Get Started** section above and press `w` to see them go! 🤖💨
