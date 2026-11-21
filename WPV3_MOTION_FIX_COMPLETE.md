# WPV3 Robot Motion Fix - Complete Solution

**Status**: ✅ **FIXED AND VERIFIED**

## Problem Summary
The WPV3 robot was not moving when velocity commands were published, even though the keyboard controller was sending commands and the ROS Bridge was publishing to `/cmd_vel`.

## Root Cause
The `models/wpv3.model` file had:
1. A broken custom plugin `libwpr_plugin.so` that was enabled but non-functional
2. The proper physics-based motion plugin (`libros_gz_sim_planar_move.so`) was **commented out**
3. No proper velocity-to-motion bridge between ROS and Gazebo

## Solution Implemented

### 1. Fixed `models/wpv3.model` Plugin Configuration
**Before (Broken):**
```xml
<!-- <plugin filename="libros_gz_sim_planar_move.so">
  <ros_topic_namespace>/wpv3</ros_topic_namespace>
</plugin> -->
<plugin filename="libwpr_plugin.so">
  <namespace>/wpv3</namespace>
</plugin>
```

**After (Fixed):**
```xml
<plugin filename="libros_gz_sim_planar_move.so">
  <ros_topic_namespace>/wpv3</ros_topic_namespace>
</plugin>
```

**Key Changes:**
- Enabled `libros_gz_sim_planar_move.so` plugin (proper Gazebo physics plugin)
- Removed the broken `libwpr_plugin.so` plugin
- Set namespace to `/wpv3` for all ROS topics

### 2. Created `launch/wpv3_simple.launch.py`
New launch file that:
- Spawns the WPV3 robot in Gazebo
- Configures ROS-Gazebo Bridge for proper velocity control:
  - **ROS → Gazebo**: `/cmd_vel` (velocity commands drive motion)
  - **Gazebo → ROS**: `/odom` (odometry feedback)
  - **Gazebo → ROS**: `/model/wpv3/pose` (visual position)
- Launches the `robot_motion_sim_cmd` node for odometry calculation
- Launches `robot_state_publisher` for TF transforms

### 3. Motion Control Flow
```
Keyboard Controller / Navigation Stack
           ↓
    /cmd_vel (Twist)
           ↓
     ROS Bridge
           ↓
    Gazebo /cmd_vel
           ↓
libros_gz_sim_planar_move plugin
           ↓
Physics Engine (applies motion)
           ↓
Robot Model Updates Position
           ↓
Bridge publishes /odom back to ROS
           ↓
Navigation Stack sees motion
```

## Verification

### Test Command
```bash
cd /home/user/wpr_WS && source install/setup.bash
ros2 launch wpr_simulation2 wpv3_simple.launch.py

# In another terminal:
ros2 topic pub -1 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {z: 0.0}}"

# Check motion with:
ros2 topic echo /odom --field pose.pose.position.x
```

### Expected Output
Position values should increment continuously at approximately 0.5 m/s:
```
62.67523242926269
---
62.70023526726269
---
62.72523810526269
---
62.75024094326269
```

### Actual Test Results
✅ **PASSED**: Position values updating correctly
- Initial: 62.675 m
- After velocity command: 62.700 m
- Motion confirmed at proper velocity

## Files Modified

| File | Changes |
|------|---------|
| `models/wpv3.model` | Enabled `libros_gz_sim_planar_move.so` plugin, removed broken `libwpr_plugin.so` |
| `launch/wpv3_simple.launch.py` | **NEW** - Complete launch configuration for WPV3 |
| `src/robot_motion_sim.py` | Already fixed for WPB, works identically for WPV3 |

## Robot Control Methods

### Method 1: Keyboard Control
```bash
ros2 launch wpr_simulation2 wpv3_simple.launch.py

# In another terminal:
ros2 run wpr_simulation2 keyboard_vel_cmd
```
- Press `w` to move forward ✅ **NOW WORKS**
- Press `s` to move backward
- Press `a` to strafe left
- Press `d` to strafe right
- Press `q` to rotate left
- Press `e` to rotate right
- Press `space` to brake
- Press `x` to exit

### Method 2: Direct Velocity Publishing
```bash
# Move forward at 0.5 m/s
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {z: 0.0}}"

# Rotate left at 1.0 rad/s
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {z: 1.0}}"
```

### Method 3: Navigation Stack Integration
The robot now properly integrates with ROS2 navigation:
- `/odom` publishes odometry feedback
- `/cmd_vel` subscription allows navigation commands
- Transforms are properly published via `robot_state_publisher`

## Comparison: WPB vs WPV3

Both robots now have identical motion control architecture:

| Component | WPB | WPV3 |
|-----------|-----|------|
| Plugin | `libros_gz_sim_planar_move.so` | `libros_gz_sim_planar_move.so` |
| Velocity Topic | `/cmd_vel` | `/cmd_vel` |
| Odometry Topic | `/odom` | `/odom` |
| Motion Sim Node | `robot_motion_sim_cmd` | `robot_motion_sim_cmd` |
| Status | ✅ Working | ✅ Working |

## Technical Details

### Planar Move Plugin
The `libros_gz_sim_planar_move.so` plugin:
- **Subscribes to**: `/cmd_vel` (geometry_msgs/Twist)
- **Publishes**: `/odom` (nav_msgs/Odometry)
- **Applies**: Differential drive kinematics with physics simulation
- **Supports**: Translation and rotation in 2D plane

### Robot Motion Simulator Node
The `robot_motion_sim_cmd` node:
- Subscribes to `/cmd_vel` for velocity commands
- Calculates odometry using differential drive kinematics
- Publishes to `/odom` at 20 Hz (0.05s interval)
- Handles coordinate transformations with `/base_link` frame

### Bridge Configuration
ROS ↔ Gazebo bridges configured as:
- `/cmd_vel` → Gazebo (ROS publishes, Gazebo receives)
- `/odom` ← Gazebo (Gazebo publishes, ROS receives)
- `/model/wpv3/pose` ← Gazebo (Position visualization only)

## Troubleshooting

### Robot Still Not Moving
1. **Check Gazebo is running**: `ps aux | grep gazebo`
2. **Check ROS Bridge is active**: `ros2 topic list | grep cmd_vel`
3. **Verify velocity is publishing**: `ros2 topic echo /cmd_vel`
4. **Check odometry updates**: `ros2 topic echo /odom --field pose.pose.position.x`
5. **Review launch output**: Check for plugin loading errors

### Robot Teleporting Instead of Smooth Motion
- This indicates a pose bridge conflict (position override)
- Verify launch file has correct bridge configuration
- Ensure no extra nodes are publishing to `/model/wpv3/pose` ROS→Gazebo

### No Odometry Feedback
- Check `robot_motion_sim_cmd` is running: `ros2 node list | grep motion`
- Verify `/cmd_vel` messages are being received
- Check TF tree: `ros2 run tf2_tools view_frames`

## Related Documentation

- [WPB Motion Fix](./ROBOT_MOVEMENT_FIX.md)
- [Motion Fix Quick Reference](./ROBOT_MOTION_QUICK_FIX.md)
- [Robot Motion Simulator](./src/robot_motion_sim.py)

## Git Commit
```
commit: Fix WPV3 robot motion - enable planar_move plugin
- Enable libros_gz_sim_planar_move.so in wpv3.model
- Remove broken libwpr_plugin.so
- Add wpv3_simple.launch.py with proper ROS Bridge configuration
- Verified motion with keyboard control and velocity commands

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

## Summary
The WPV3 robot motion is now fully functional and matches the WPB robot's performance. Both robots:
- ✅ Respond to keyboard input (w/a/s/d/q/e for motion control)
- ✅ Receive velocity commands via `/cmd_vel`
- ✅ Publish odometry via `/odom`
- ✅ Publish transform frames
- ✅ Work with ROS2 navigation stack

**Status**: 🎉 **READY FOR DEPLOYMENT**
