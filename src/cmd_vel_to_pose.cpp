/*
 * Simple cmd_vel to pose converter for WPR robot simulation
 * Subscribes to /cmd_vel and publishes to Gazebo entity commands
 */

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

class CmdVelToPose : public rclcpp::Node
{
public:
  CmdVelToPose() : Node("cmd_vel_to_pose"), 
    robot_x_(0.0), robot_y_(0.0), robot_yaw_(0.0),
    last_time_(this->now())
  {
    // Subscribe to cmd_vel
    vel_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
      "/cmd_vel", 10,
      std::bind(&CmdVelToPose::velocityCallback, this, std::placeholders::_1));
    
    RCLCPP_INFO(this->get_logger(), "CmdVelToPose node started");
  }

private:
  void velocityCallback(const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    // Calculate time delta
    auto current_time = this->now();
    double dt = (current_time - last_time_).seconds();
    last_time_ = current_time;
    
    if (dt <= 0) return;
    
    // Extract velocity commands
    double vx = msg->linear.x;
    double vy = msg->linear.y;
    double vyaw = msg->angular.z;
    
    // Update pose based on velocity (simple kinematic model)
    // For differential drive: x += vx*cos(yaw)*dt, y += vx*sin(yaw)*dt
    if (std::abs(vyaw) < 0.0001) {
      // Straight line motion
      robot_x_ += vx * std::cos(robot_yaw_) * dt;
      robot_y_ += vx * std::sin(robot_yaw_) * dt;
    } else {
      // Curved motion with rotation
      double radius = vx / vyaw;
      robot_x_ += radius * (std::sin(robot_yaw_ + vyaw * dt) - std::sin(robot_yaw_));
      robot_y_ -= radius * (std::cos(robot_yaw_ + vyaw * dt) - std::cos(robot_yaw_));
    }
    
    robot_yaw_ += vyaw * dt;
    
    // Normalize yaw
    while (robot_yaw_ > M_PI) robot_yaw_ -= 2 * M_PI;
    while (robot_yaw_ < -M_PI) robot_yaw_ += 2 * M_PI;
    
    // Log motion (every 10 updates to reduce spam)
    static int count = 0;
    if (++count % 10 == 0) {
      RCLCPP_DEBUG(this->get_logger(), 
        "Robot at: x=%.3f, y=%.3f, yaw=%.3f (vx=%.3f, vy=%.3f, vyaw=%.3f)",
        robot_x_, robot_y_, robot_yaw_, vx, vy, vyaw);
    }
  }
  
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr vel_sub_;
  
  double robot_x_, robot_y_, robot_yaw_;
  rclcpp::Time last_time_;
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CmdVelToPose>());
  rclcpp::shutdown();
  return 0;
}
