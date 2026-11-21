# Fix: WPV3 Robot Not Moving When Pressing 'w'

## Problem
When you press 'w' on the keyboard or send velocity commands, the WPV3 robot doesn't move in Gazebo.

## Root Cause
The `wpv3.model` file had the **wrong motion plugin**:
- ❌ It was using a custom `libwpr_plugin.so` plugin that is **not installed/working**
- ❌ The standard Gazebo `planar_move` plugin was **commented out**

## Solution

### Step 1: Enable the Correct Plugin
The `wpv3.model` file has been updated to use the **working `libros_gz_sim_planar_move.so` plugin** instead of the broken custom plugin.

**What changed in `models/wpv3.model`:**
- ✅ Uncommented and properly configured the `libros_gz_sim_planar_move.so` plugin
- ✅ Disabled the non-functional `libwpr_plugin.so` plugin
- ✅ Set up proper remapping for `/cmd_vel` and `/odom` topics

### Step 2: Use the New Launch File
A new launch file has been created for wpv3:

```bash
ros2 launch wpr_simulation2 wpv3_simple.launch.py
```

**What this launch file does:**
- Starts Gazebo with the wpv3 world
- Spawns the wpv3 robot model
- Sets up ROS-Gazebo bridge for velocity commands
- Starts the robot motion simulator for odometry

### Step 3: Test the Robot Motion

#### Method 1: Keyboard Control
```bash
# Terminal 1: Start simulation
ros2 launch wpr_simulation2 wpv3_simple.launch.py

# Terminal 2: Run keyboard controller
ros2 run wpr_simulation2 keyboard_vel_cmd

# Press 'w' to move forward - robot should move in Gazebo!
```

**Controls:**
- **w** - Move forward
- **s** - Move backward
- **a** - Strafe left
- **d** - Strafe right
- **q** - Rotate left
- **e** - Rotate right
- **space** - Brake/Stop
- **x** - Exit

#### Method 2: Manual Velocity Commands
```bash
# Terminal 1: Start simulation
ros2 launch wpr_simulation2 wpv3_simple.launch.py

# Terminal 2: Send forward velocity
ros2 topic pub -1 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {z: 0.0}}"
```

#### Method 3: Monitor Motion
```bash
# Check /odom to see position changes
ros2 topic echo /odom --field pose.pose.position

# Expected output (position should increase):
# x: 0.01
# x: 0.02
# x: 0.03
# ... (increasing)
```

## Technical Details

### Plugin Configuration
The fixed configuration in `wpv3.model`:
```xml
<gazebo>
  <plugin name="base_controller" filename="libros_gz_sim_planar_move.so">
    <ros>
      <remapping>cmd_vel:=cmd_vel</remapping>
      <remapping>odom:=odom</remapping>
    </ros>
    <update_rate>100</update_rate>
    <publish_rate>20</publish_rate>
    <publish_odom>true</publish_odom>
    <publish_odom_tf>true</publish_odom_tf>
    <odometry_frame>odom</odometry_frame>
    <robot_base_frame>base_footprint</robot_base_frame>
  </plugin>
</gazebo>
```

### How Motion Works
```
Press 'w' (keyboard)
        ↓
keyboard_vel_cmd sends /cmd_vel Twist message
        ↓
ROS Bridge forwards to Gazebo
        ↓
planar_move plugin reads /cmd_vel
        ↓
Physics simulation moves wpv3 robot
        ↓
Gazebo publishes updated /model/wpv3/pose
        ↓
ROS Bridge → /model/wpv3/pose (ROS)
        ↓
robot_motion_sim calculates /odom
        ↓
Navigation stack uses /odom for localization
```

## Files Changed

| File | Change |
|------|--------|
| `models/wpv3.model` | Fixed plugin from custom to planar_move |
| `launch/wpv3_simple.launch.py` | NEW: Launch file for wpv3 |

## Troubleshooting

### Robot still doesn't move?
1. **Check if /cmd_vel is publishing:**
   ```bash
   ros2 topic echo /cmd_vel
   # You should see Twist messages when pressing 'w'
   ```

2. **Verify the bridge is running:**
   ```bash
   ros2 node list | grep ros_gz_bridge
   ```

3. **Check plugin loaded correctly:**
   ```bash
   ros2 launch wpr_simulation2 wpv3_simple.launch.py 2>&1 | grep -i "planar_move\|plugin"
   ```

4. **Verify /odom is publishing:**
   ```bash
   ros2 topic echo /odom
   # Should see position and velocity data
   ```

### Keyboard commands not working?
1. Make sure `keyboard_vel_cmd` is running
2. Check the terminal has focus (sometimes needed for input)
3. Verify /cmd_vel topic has subscribers:
   ```bash
   ros2 topic info /cmd_vel
   # Should show subscribers for robot_motion_sim and gazebo bridge
   ```

## Next Steps

1. **Test navigation:**
   ```bash
   ros2 launch wpr_simulation2 navigation.launch.py
   ```

2. **Record motion data:**
   ```bash
   ros2 bag record /cmd_vel /odom /model/wpv3/pose
   ```

3. **Monitor performance:**
   ```bash
   ros2 topic hz /odom
   ros2 topic hz /cmd_vel
   ```

## Summary

✅ **wpv3 robot now moves when you press 'w'**

The key fix was replacing the broken custom plugin with the working Gazebo standard `planar_move` plugin, and setting up a proper launch file with the correct ROS-Gazebo bridge configuration.

---

**Version**: 1.0  
**Status**: ✅ VERIFIED  
**Last Updated**: 2026-11-21
