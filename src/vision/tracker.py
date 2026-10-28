"""
Bộ theo dõi Đa đối tượng thuần Python (Lightweight IoU + Centroid Person Tracker).
Không phụ thuộc vào các thư viện C++ ngoài (như lap hay scipy).
Chuyên trách:
  1. Gán Track ID ổn định cho từng người trong khung hình.
  2. Phân biệt người cũ và người mới đến thế chỗ.
  3. Theo dõi trạng thái đã chào (greeted) để chống chào lặp lại.
"""
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


def compute_iou(box1: List[float], box2: List[float]) -> float:
    """Tính Intersection over Union (IoU) giữa 2 bounding box [x1, y1, x2, y2]."""
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


@dataclass
class TrackedPerson:
    """Thông tin một người đang được theo dõi."""
    track_id: int
    bbox: List[float]               # [x1, y1, x2, y2]
    area_ratio: float               # Tỷ lệ diện tích so với khung hình
    confidence: float
    last_seen_time: float
    missing_frames: int = 0
    is_greeted: bool = False


class PersonTracker:
    """
    Bộ theo dõi vị trí người qua các khung hình liên tiếp.
    Duy trì ID duy nhất cho mỗi người và tự động dọn dẹp khi người rời đi.
    """
    def __init__(
        self,
        iou_threshold: float = 0.25,
        max_missing_frames: int = 30,  # ~1 - 1.5 giây vắng mặt thì coi như đã rời đi
        history_expiry_sec: float = 120.0  # Sau 2 phút mới tái sử dụng / quên ID cũ
    ):
        self.iou_threshold = iou_threshold
        self.max_missing_frames = max_missing_frames
        self.history_expiry_sec = history_expiry_sec
        
        self._next_id: int = 1
        self.active_tracks: Dict[int, TrackedPerson] = {}
        # Lưu lịch sử các ID đã chào: {track_id: last_seen_time}
        self.greeted_history: Dict[int, float] = {}

    def update(
        self,
        detected_persons: List[Dict[str, Any]],
        frame_area: float
    ) -> List[TrackedPerson]:
        """
        Cập nhật danh sách người được theo dõi từ kết quả detection của YOLO.
        detected_persons: Danh sách dict [{'bbox': [...], 'confidence': ..., 'area_ratio': ...}]
        """
        now = time.time()
        
        # Nếu không có người nào trong khung hình hiện tại
        if not detected_persons:
            for t in list(self.active_tracks.values()):
                t.missing_frames += 1
                if t.missing_frames > self.max_missing_frames:
                    # Người đã rời khỏi khung hình
                    del self.active_tracks[t.track_id]
            self._cleanup_history(now)
            return []

        # Ma trận IoU giữa các Track đang có và các BBox mới phát hiện
        active_ids = list(self.active_tracks.keys())
        matched_tracks = set()
        matched_detections = set()

        if active_ids:
            # Tìm cặp ghép đôi có IoU lớn nhất
            iou_matches = []
            for d_idx, det in enumerate(detected_persons):
                for t_id in active_ids:
                    iou = compute_iou(det["bbox"], self.active_tracks[t_id].bbox)
                    if iou >= self.iou_threshold:
                        iou_matches.append((iou, d_idx, t_id))

            # Sắp xếp IoU giảm dần (ưu tiên ghép cặp khớp nhất)
            iou_matches.sort(key=lambda x: x[0], reverse=True)

            for iou, d_idx, t_id in iou_matches:
                if d_idx in matched_detections or t_id in matched_tracks:
                    continue
                # Cập nhật thông tin cho Track đã có
                track = self.active_tracks[t_id]
                track.bbox = det["bbox"]
                track.area_ratio = det.get("area_ratio", 0.0)
                track.confidence = det.get("confidence", 0.0)
                track.last_seen_time = now
                track.missing_frames = 0
                
                # Cập nhật vào lịch sử greeted nếu đã từng chào
                if track.is_greeted:
                    self.greeted_history[t_id] = now

                matched_tracks.add(t_id)
                matched_detections.add(d_idx)

        # Xử lý các Track cũ không tìm thấy trong khung hình này
        for t_id, track in list(self.active_tracks.items()):
            if t_id not in matched_tracks:
                track.missing_frames += 1
                if track.missing_frames > self.max_missing_frames:
                    del self.active_tracks[t_id]

        # Khởi tạo Track mới cho các Detection chưa được ghép cặp
        for d_idx, det in enumerate(detected_persons):
            if d_idx not in matched_detections:
                new_id = self._next_id
                self._next_id += 1
                
                # Kiểm tra xem ID này trong quá khứ đã được chào chưa
                is_already_greeted = new_id in self.greeted_history
                
                new_track = TrackedPerson(
                    track_id=new_id,
                    bbox=det["bbox"],
                    area_ratio=det.get("area_ratio", 0.0),
                    confidence=det.get("confidence", 0.0),
                    last_seen_time=now,
                    missing_frames=0,
                    is_greeted=is_already_greeted
                )
                self.active_tracks[new_id] = new_track

        self._cleanup_history(now)
        return list(self.active_tracks.values())

    def mark_as_greeted(self, track_ids: List[int]):
        """Đánh dấu danh sách các track_id là đã được cất lời chào đón."""
        now = time.time()
        for t_id in track_ids:
            if t_id in self.active_tracks:
                self.active_tracks[t_id].is_greeted = True
            self.greeted_history[t_id] = now

    def _cleanup_history(self, now: float):
        """Dọn dẹp các ID cũ đã rời đi quá lâu khỏi bộ nhớ."""
        expired = [
            t_id for t_id, last_time in self.greeted_history.items()
            if (now - last_time) > self.history_expiry_sec
        ]
        for t_id in expired:
            del self.greeted_history[t_id]
