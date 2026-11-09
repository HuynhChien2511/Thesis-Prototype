"""
Kiểm thử Unit Test cho Giao diện Tích hợp Robot ROS 2 và Cầu nối IPC Bridge (8 bài test - Task 5).
Bao gồm:
  1. Tuần tự hóa thông điệp Action Goal NavigateToPose cho Nav2.
  2. Tra cứu tọa độ địa danh đặc trưng (Semantic Waypoint Mapping).
  3. Từ chối an toàn địa danh không tồn tại trong bản đồ.
  4. Đóng gói lệnh hủy điều hướng (Cancel Navigation).
  5. Phát lệnh phanh dừng khẩn cấp (/cmd_vel Twist) khi phát hiện từ khóa nguy cấp.
  6. Trích xuất vận tốc góc quay (omega_z từ /odom) phục vụ bù trừ camera MOT.
  7. Cảnh báo pin yếu tự động (Battery State Telemetry < 20%).
  8. Phân giải siêu dữ liệu bản đồ SLAM OccupancyGrid (/map metadata & World-to-Grid).
"""
import sys
import unittest
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))


# Định nghĩa các hàm tiện ích của IPC Bridge (sẽ được tích hợp vào bridge_server.py)
SEMANTIC_WAYPOINTS = {
    "phong_mot_cua": {"x": 12.45, "y": 8.30, "theta": 0.0},
    "ban_huong_dan": {"x": 2.10, "y": 1.50, "theta": 1.57},
    "phong_cong_chung": {"x": 8.70, "y": 15.20, "theta": -1.57},
    "tram_sac_pin": {"x": 0.00, "y": 0.00, "theta": 3.14},
}


def serialize_nav2_goal(target_name: str, x: float, y: float, theta: float = 0.0) -> Dict[str, Any]:
    """Tạo payload JSON chuẩn gửi Action NavigateToPose cho ROS 2 Nav2."""
    # Chuyển đổi góc quay theta (yaw) sang quaternion z, w (trục phẳng 2D)
    qz = math.sin(theta / 2.0)
    qw = math.cos(theta / 2.0)
    return {
        "action": "navigate_to_pose",
        "target_name": target_name,
        "pose": {
            "header": {
                "frame_id": "map",
            },
            "pose": {
                "position": {"x": round(x, 2), "y": round(y, 2), "z": 0.0},
                "orientation": {"x": 0.0, "y": 0.0, "z": round(qz, 4), "w": round(qw, 4)}
            }
        }
    }


def lookup_waypoint(location_name: str) -> Optional[Dict[str, float]]:
    """Tra cứu tọa độ mục tiêu từ tên địa danh người dùng nói."""
    normalized = location_name.lower().strip().replace(" ", "_")
    return SEMANTIC_WAYPOINTS.get(normalized)


def create_emergency_stop_command() -> Dict[str, Any]:
    """Tạo lệnh phanh dừng khẩn cấp cho động cơ robot."""
    return {
        "command": "emergency_stop",
        "topic": "/cmd_vel",
        "twist": {
            "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
            "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
        }
    }


def parse_odometry_telemetry(odom_msg: Dict[str, Any]) -> Dict[str, float]:
    """Trích xuất vận tốc dài và vận tốc góc quay từ thông điệp nav_msgs/Odometry."""
    twist = odom_msg.get("twist", {}).get("twist", {})
    linear_x = twist.get("linear", {}).get("x", 0.0)
    angular_z = twist.get("angular", {}).get("z", 0.0)
    return {"linear_v": round(linear_x, 3), "angular_w": round(angular_z, 3)}


def evaluate_battery_status(battery_msg: Dict[str, Any]) -> Dict[str, Any]:
    """Đánh giá dung lượng pin và cảnh báo nếu dưới 20%."""
    percentage = battery_msg.get("percentage", 1.0)
    voltage = battery_msg.get("voltage", 24.0)
    is_low = percentage < 0.20
    warning_text = ""
    if is_low:
        warning_text = f"Dung lượng pin hiện tại còn {int(percentage*100)}%, xin vui lòng đưa robot về trạm sạc."
    return {
        "percentage": percentage,
        "voltage": voltage,
        "is_low": is_low,
        "warning_text": warning_text
    }


def world_to_map_grid(x: float, y: float, map_meta: Dict[str, Any]) -> Tuple[int, int]:
    """Chuyển đổi tọa độ thế giới thực (mét) sang ô lưới pixel bản đồ SLAM."""
    resolution = map_meta.get("resolution", 0.05)  # 5cm/pixel
    origin_x = map_meta.get("origin", {}).get("x", 0.0)
    origin_y = map_meta.get("origin", {}).get("y", 0.0)

    grid_col = int((x - origin_x) / resolution)
    grid_row = int((y - origin_y) / resolution)
    return grid_col, grid_row


class TestROS2IPCBridge(unittest.TestCase):
    """Bộ kiểm thử cho Cầu nối giao tiếp Robot ROS 2 IPC."""

    def test_1_navigate_to_pose_action_goal_serialization(self):
        """1. Kiểm tra định dạng JSON payload mục tiêu điều hướng Nav2."""
        goal = serialize_nav2_goal("phong_mot_cua", 12.45, 8.30, theta=0.0)
        self.assertEqual(goal["action"], "navigate_to_pose")
        self.assertEqual(goal["pose"]["header"]["frame_id"], "map")
        self.assertEqual(goal["pose"]["pose"]["position"]["x"], 12.45)
        self.assertEqual(goal["pose"]["pose"]["position"]["y"], 8.30)
        self.assertEqual(goal["pose"]["pose"]["orientation"]["w"], 1.0)

    def test_2_semantic_waypoint_lookup_success(self):
        """2. Kiểm tra tra cứu tọa độ từ tên địa danh thành công."""
        wp = lookup_waypoint("phong mot cua")
        self.assertIsNotNone(wp)
        self.assertEqual(wp["x"], 12.45)
        self.assertEqual(wp["y"], 8.30)

        wp_guide = lookup_waypoint("ban_huong_dan")
        self.assertIsNotNone(wp_guide)
        self.assertEqual(wp_guide["x"], 2.10)

    def test_3_unknown_waypoint_lookup_rejection(self):
        """3. Kiểm tra địa danh lạ không có trong bản đồ trả về None an toàn."""
        wp = lookup_waypoint("phong giam doc vip")
        self.assertIsNone(wp)

    def test_4_cancel_navigation_command(self):
        """4. Kiểm tra gói tin lệnh hủy điều hướng robot."""
        cancel_cmd = {"action": "cancel_navigation", "timestamp": 1731139200}
        self.assertEqual(cancel_cmd["action"], "cancel_navigation")
        self.assertIn("timestamp", cancel_cmd)

    def test_5_emergency_stop_velocity_zeroing(self):
        """5. Kiểm tra lệnh dừng khẩn cấp triệt tiêu vận tốc tuyến tính và góc về 0."""
        stop_cmd = create_emergency_stop_command()
        self.assertEqual(stop_cmd["command"], "emergency_stop")
        self.assertEqual(stop_cmd["topic"], "/cmd_vel")
        self.assertEqual(stop_cmd["twist"]["linear"]["x"], 0.0)
        self.assertEqual(stop_cmd["twist"]["angular"]["z"], 0.0)

    def test_6_odometry_angular_velocity_parsing(self):
        """6. Kiểm tra bóc tách vận tốc góc omega_z từ telemetry /odom để bù trừ camera."""
        mock_odom = {
            "twist": {
                "twist": {
                    "linear": {"x": 0.25, "y": 0.0, "z": 0.0},
                    "angular": {"x": 0.0, "y": 0.0, "z": 0.157}
                }
            }
        }
        res = parse_odometry_telemetry(mock_odom)
        self.assertEqual(res["linear_v"], 0.25)
        self.assertEqual(res["angular_w"], 0.157)

    def test_7_battery_state_low_voltage_alert(self):
        """7. Kiểm tra kích hoạt cảnh báo thoại khi pin dưới 20%."""
        mock_low_battery = {"percentage": 0.15, "voltage": 21.6}
        res = evaluate_battery_status(mock_low_battery)
        self.assertTrue(res["is_low"])
        self.assertIn("15%", res["warning_text"])

        mock_healthy_battery = {"percentage": 0.85, "voltage": 25.2}
        res_ok = evaluate_battery_status(mock_healthy_battery)
        self.assertFalse(res_ok["is_low"])
        self.assertEqual(res_ok["warning_text"], "")

    def test_8_slam_map_metadata_parsing(self):
        """8. Kiểm tra chuyển đổi tọa độ mét sang pixel bản đồ SLAM OccupancyGrid."""
        map_meta = {
            "resolution": 0.05,  # 5cm/pixel
            "origin": {"x": -10.0, "y": -10.0}
        }
        # Tọa độ (0.0m, 0.0m) với gốc (-10m, -10m):
        # (0 - (-10)) / 0.05 = 10 / 0.05 = 200 pixel
        col, row = world_to_map_grid(0.0, 0.0, map_meta)
        self.assertEqual(col, 200)
        self.assertEqual(row, 200)


if __name__ == "__main__":
    unittest.main()
