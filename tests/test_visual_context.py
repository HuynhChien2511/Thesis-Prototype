"""
Kiểm thử Unit Test cho Module Quản lý Ngữ cảnh Thị giác (VisionContextManager & Multimodal VQA).
Được tích hợp vào unittest framework để tự động phát hiện và chạy qua 'unittest discover'.

Bao gồm các nhóm kiểm thử:
  1. Nhận diện truy vấn thị giác (is_visual_query) cho các câu hỏi quan sát không gian.
  2. Bỏ qua truy vấn phi thị giác (Pure Text/Administrative queries).
  3. Quản lý trạng thái chào hỏi chủ động (Proactive Greeting pause/resume).
  4. Cập nhật và truy xuất trạng thái tri giác (Perception State & Thread Safety).
  5. Xử lý an toàn khi Camera không có tín hiệu khung hình (Frame Capture Fallback).
  6. Tích hợp Multimodal Gemini Vision với dữ liệu hình ảnh giả lập (Mocked VQA).
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Thêm prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

# Đảm bảo UTF-8 console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from src.vision.visual_context import VisionContextManager, VISUAL_QUERY_KEYWORDS
from src.vision.detector import DetectionResult
from src.vision.tracker import TrackedPerson


class TestVisionContextManager(unittest.TestCase):
    """Bộ kiểm thử đơn vị cho Module Ngữ cảnh Thị giác & Multimodal VQA."""

    def setUp(self):
        self.mock_camera = MagicMock()
        self.mock_detector = MagicMock()
        self.vcm = VisionContextManager(
            camera=self.mock_camera,
            detector=self.mock_detector
        )

    def test_1_is_visual_query_positive(self):
        """Kiểm tra nhận diện chính xác các câu hỏi yêu cầu Robot quan sát hình ảnh trước mặt."""
        positive_queries = [
            "Nhìn xem trước mặt tôi có giấy tờ gì?",
            "Nhìn giúp tôi xem đây là giấy gì?",
            "Trước mặt có mấy người đang đứng?",
            "Tôi đang cầm vật gì trên tay?",
            "Xem hộ tôi tờ giấy này ghi thông tin gì?",
            "Người đang đứng đối diện mặc áo gì?",
            "Thấy gì trước camera không?",
            "Bao nhiêu người đang xếp hàng?"
        ]
        for query in positive_queries:
            is_vis = self.vcm.is_visual_query(query)
            self.assertTrue(
                is_vis,
                f"Câu hỏi thị giác '{query}' phải được nhận diện is_visual_query=True"
            )

    def test_2_is_visual_query_negative(self):
        """Kiểm tra câu hỏi thuần văn bản hành chính không bị nhận nhầm thành thị giác."""
        negative_queries = [
            "Thủ tục làm thẻ căn cước cần những giấy tờ gì?",
            "Lệ phí đăng ký kết hôn tại xã là bao nhiêu tiền?",
            "Thời tiết tại Đà Nẵng hôm nay có mưa không?",
            "Đăng ký thường trú ở đâu?",
            "Xin chào em robot",
            "Cảm ơn em nhiều nhé",
            "",
            "12345"
        ]
        for query in negative_queries:
            is_vis = self.vcm.is_visual_query(query)
            self.assertFalse(
                is_vis,
                f"Câu hỏi '{query}' KHÔNG được nhận là thị giác (phải là False)"
            )

    def test_3_proactive_greeting_pause_and_resume(self):
        """Kiểm tra cơ chế tạm dừng và phục hồi lời chào chủ động khi vào phiên đàm thoại."""
        self.assertFalse(self.vcm.greeting_paused)
        self.assertEqual(self.vcm.consecutive_ungreeted_frames, 0)

        # Giả lập đang trong phiên nói chuyện -> Tạm dừng chào
        self.vcm.consecutive_ungreeted_frames = 5
        self.vcm.pause_greeting()
        self.assertTrue(self.vcm.greeting_paused)

        # Trở về màn hình chờ -> Phục hồi chào
        self.vcm.resume_greeting()
        self.assertFalse(self.vcm.greeting_paused)
        self.assertEqual(self.vcm.consecutive_ungreeted_frames, 0)

    def test_4_perception_state_update(self):
        """Kiểm tra cập nhật và truy xuất kết quả nhận diện đa luồng (Perception State)."""
        import time
        tracked_p = TrackedPerson(
            track_id=10,
            bbox=[100, 100, 300, 400],
            confidence=0.92,
            area_ratio=0.35,
            last_seen_time=time.time(),
            is_greeted=False
        )
        fake_result = DetectionResult(
            has_person=True,
            person_count=1,
            max_person_ratio=0.35,
            tracked_persons=[tracked_p],
            summary_text="1 người (gần)"
        )

        with self.vcm._lock:
            self.vcm.latest_result = fake_result

        current = self.vcm.get_current_perception()
        self.assertTrue(current.has_person)
        self.assertEqual(current.person_count, 1)
        self.assertEqual(current.max_person_ratio, 0.35)
        self.assertEqual(len(current.tracked_persons), 1)
        self.assertEqual(current.tracked_persons[0].track_id, 10)

    def test_5_multimodal_vision_fallback_when_no_frame(self):
        """Kiểm tra xử lý nhẹ nhàng khi không chụp được khung hình từ Camera."""
        self.mock_camera.get_frame.return_value = None

        res = self.vcm.ask_multimodal_vision("Trước mặt có gì?")
        self.assertFalse(res["success"])
        self.assertIn("không ghi nhận được hình ảnh", res["answer"])
        self.assertEqual(res["latency_sec"], 0.0)

    def test_6_multimodal_vision_with_mocked_gemini(self):
        """Kiểm tra luồng gửi câu hỏi và ảnh JPEG tới mô hình Gemini Vision."""
        fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # Header JPEG giả lập
        
        mock_response = MagicMock()
        mock_response.text = "Trước mặt bạn là một người đang cầm tờ giấy hẹn làm Căn cước công dân."

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        self.vcm._genai_client = mock_client

        res = self.vcm.ask_multimodal_vision(
            question="Nhìn xem tờ giấy này là gì?",
            jpeg_bytes=fake_jpeg
        )
        self.assertTrue(res["success"])
        self.assertIn("Căn cước công dân", res["answer"])
        self.assertGreater(res["latency_sec"], 0.0)
        mock_client.models.generate_content.assert_called_once()


if __name__ == "__main__":
    unittest.main()
