"""
Bộ kiểm thử Tự động cho Module Theo dõi Thị giác Đa đối tượng (PersonTracker & MOT).
Kiểm tra:
  1. Độ chính xác của thuật toán tính toán IoU (Intersection over Union).
  2. Khởi tạo định danh duy nhất (Track ID) cho người mới xuất hiện.
  3. Duy trì Track ID nhất quán giữa các khung hình liên tiếp.
  4. Cơ chế loại bỏ người thất lạc (Missing Frames Eviction) khi rời khung hình.
  5. Theo dõi độc lập nhiều người đồng thời trong cùng khung hình.
  6. Cơ chế đánh dấu đã chào hỏi (mark_as_greeted) và lưu lịch sử chống spam.
  7. Xử lý an toàn khi khung hình rỗng (không phát hiện người).
"""
import sys
import unittest
from pathlib import Path

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.vision.tracker import PersonTracker, compute_iou, TrackedPerson


class TestPersonTrackerMOT(unittest.TestCase):

    def setUp(self):
        self.tracker = PersonTracker(iou_threshold=0.3, max_missing_frames=5)
        self.frame_area = 640.0 * 480.0

    def test_1_compute_iou_accuracy(self):
        """Kiểm tra độ chính xác của hàm tính IoU giữa 2 bounding box."""
        # 1. Trùng khớp hoàn toàn -> IoU = 1.0
        box_a = [10.0, 10.0, 100.0, 100.0]
        box_b = [10.0, 10.0, 100.0, 100.0]
        self.assertAlmostEqual(compute_iou(box_a, box_b), 1.0, places=3)

        # 2. Không giao nhau -> IoU = 0.0
        box_c = [200.0, 200.0, 300.0, 300.0]
        self.assertEqual(compute_iou(box_a, box_c), 0.0)

        # 3. Giao nhau một phần
        box_d = [55.0, 10.0, 145.0, 100.0]  # Dịch chuyển 50% theo chiều ngang
        iou_val = compute_iou(box_a, box_d)
        self.assertGreater(iou_val, 0.2)
        self.assertLess(iou_val, 0.6)

    def test_2_new_track_creation(self):
        """Kiểm tra người mới xuất hiện được cấp Track ID mới với các chỉ số chuẩn xác."""
        detections = [{
            "bbox": [50.0, 50.0, 200.0, 350.0],
            "confidence": 0.92,
            "area_ratio": 0.15
        }]
        tracks = self.tracker.update(detections, self.frame_area)
        
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].track_id, 1)
        self.assertFalse(tracks[0].is_greeted)
        self.assertEqual(tracks[0].missing_frames, 0)
        self.assertAlmostEqual(tracks[0].area_ratio, 0.15)

    def test_3_track_continuation(self):
        """Kiểm tra người di chuyển nhẹ ở frame kế tiếp vẫn giữ nguyên Track ID."""
        # Frame 1
        det_1 = [{"bbox": [100.0, 100.0, 200.0, 300.0], "confidence": 0.9, "area_ratio": 0.1}]
        tracks_1 = self.tracker.update(det_1, self.frame_area)
        t_id = tracks_1[0].track_id

        # Frame 2: Người dịch chuyển nhẹ sang phải (vẫn có IoU cao)
        det_2 = [{"bbox": [105.0, 100.0, 205.0, 300.0], "confidence": 0.91, "area_ratio": 0.1}]
        tracks_2 = self.tracker.update(det_2, self.frame_area)
        
        self.assertEqual(len(tracks_2), 1)
        self.assertEqual(tracks_2[0].track_id, t_id, "Track ID phải được duy trì liên tục giữa các frame!")

    def test_4_missing_frames_eviction(self):
        """Kiểm tra sau khi người rời đi quá max_missing_frames, track bị xóa khỏi RAM."""
        det = [{"bbox": [100.0, 100.0, 200.0, 300.0], "confidence": 0.9, "area_ratio": 0.1}]
        self.tracker.update(det, self.frame_area)
        self.assertIn(1, self.tracker.active_tracks)

        # Giả lập 6 frames liên tiếp không phát hiện thấy người
        for _ in range(6):
            self.tracker.update([], self.frame_area)

        # Track 1 phải bị xóa do vượt quá max_missing_frames (5 frames)
        self.assertNotIn(1, self.tracker.active_tracks)

    def test_5_multiple_persons_tracking(self):
        """Kiểm tra theo dõi đồng thời 2 người khác nhau trong cùng một khung hình."""
        det_group = [
            {"bbox": [20.0, 50.0, 150.0, 300.0], "confidence": 0.88, "area_ratio": 0.1},
            {"bbox": [350.0, 50.0, 500.0, 300.0], "confidence": 0.92, "area_ratio": 0.12}
        ]
        tracks = self.tracker.update(det_group, self.frame_area)
        
        self.assertEqual(len(tracks), 2)
        track_ids = {t.track_id for t in tracks}
        self.assertEqual(len(track_ids), 2, "2 người phải có 2 Track ID hoàn toàn khác nhau!")

    def test_6_mark_as_greeted(self):
        """Kiểm tra đánh dấu đã chào hỏi và lưu vào bộ nhớ greeted_history."""
        det = [{"bbox": [100.0, 100.0, 200.0, 300.0], "confidence": 0.9, "area_ratio": 0.1}]
        tracks = self.tracker.update(det, self.frame_area)
        self.assertFalse(tracks[0].is_greeted)

        # Gọi hàm đánh dấu đã chào
        self.tracker.mark_as_greeted([tracks[0].track_id])
        self.assertTrue(self.tracker.active_tracks[tracks[0].track_id].is_greeted)
        self.assertIn(tracks[0].track_id, self.tracker.greeted_history)

    def test_7_empty_detection_safety(self):
        """Kiểm tra gọi update khi không có người không gây ra Exception."""
        tracks = self.tracker.update([], self.frame_area)
        self.assertEqual(len(tracks), 0)


if __name__ == "__main__":
    unittest.main()
