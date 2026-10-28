"""
Module Nhận diện Đối tượng Thời gian thực (Real-time Object Detector).
Sử dụng YOLOv8 (Nano) tối ưu hóa cho thiết bị di động / GPU CUDA.
Chuyên phát hiện người (person), đếm đối tượng và tính toán khoảng cách/tỷ lệ khung hình.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from .tracker import PersonTracker, TrackedPerson


@dataclass
class DetectionResult:
    """Cấu trúc dữ liệu chứa kết quả phát hiện trong 1 khung hình."""
    has_person: bool = False
    person_count: int = 0
    max_person_ratio: float = 0.0  # Tỷ lệ diện tích của người gần nhất so với toàn khung hình (0.0 - 1.0)
    tracked_persons: List[TrackedPerson] = field(default_factory=list)
    objects_detected: List[Dict[str, Any]] = field(default_factory=list)
    summary_text: str = ""
    inference_time_sec: float = 0.0
    annotated_frame: Optional[np.ndarray] = None


class ObjectDetector:
    """
    Bộ nhận diện đối tượng dựa trên YOLOv8 tích hợp bộ theo dõi định danh (PersonTracker).
    Tối ưu hóa chạy trên GPU CUDA với kích thước ảnh imgsz=320.
    """
    def __init__(
        self,
        model_path: str | Path,
        device: str = "0",
        imgsz: int = 320,
        conf_threshold: float = 0.50
    ):
        self.model_path = str(model_path)
        self.device = device
        self.imgsz = imgsz
        self.conf_threshold = conf_threshold
        self.model = None
        self.is_ready = False
        self.tracker = PersonTracker()
        
        self._initialize_model()

    def _initialize_model(self):
        """Khởi tạo mô hình YOLOv8."""
        if YOLO is None:
            print("[❌ YOLO ERROR] Thư viện ultralytics chưa được cài đặt!")
            return

        import torch
        # Tự động điều chỉnh thiết bị nếu GPU không sẵn sàng
        if self.device in ("0", "cuda"):
            if not (hasattr(torch, "cuda") and torch.cuda.is_available()):
                print(f"[ℹ️ YOLO DEVICE] PyTorch không có CUDA khả dụng. Tự động chuyển device='cpu'.")
                self.device = "cpu"

        model_file = Path(self.model_path)
        if not model_file.exists():
            print(f"[⚠️ YOLO WARNING] Tệp mô hình không tồn tại tại: {model_file}")
            return

        try:
            print(f"[👁️ YOLO] Đang nạp mô hình Object Detector từ '{model_file.name}' (Device={self.device})...")
            self.model = YOLO(str(model_file))
            self.is_ready = True
            print(f"[✅ YOLO READY] Mô hình YOLOv8 đã sẵn sàng nhận diện trên [{self.device.upper()}].")
        except Exception as e:
            print(f"[❌ YOLO ERROR] Không thể tải mô hình YOLOv8: {e}")
            if self.device != "cpu":
                print("[🔄 YOLO FALLBACK] Thử nạp lại mô hình trên CPU...")
                try:
                    self.device = "cpu"
                    self.model = YOLO(str(model_file))
                    self.is_ready = True
                    print("[✅ YOLO READY] Đã nạp thành công trên CPU.")
                except Exception as ex:
                    print(f"[❌ YOLO ERROR] Nạp trên CPU thất bại: {ex}")

    def detect(self, frame: np.ndarray, annotate: bool = False) -> DetectionResult:
        """
        Thực hiện nhận diện đối tượng trên một khung hình.
        - frame: Ảnh OpenCV (BGR numpy array)
        - annotate: Có vẽ bounding box và nhãn lên ảnh trả về hay không
        """
        if not self.is_ready or self.model is None or frame is None:
            return DetectionResult(summary_text="Module thị giác chưa sẵn sàng.")

        import time
        t_start = time.time()
        frame_h, frame_w = frame.shape[:2]
        frame_area = float(frame_h * frame_w)

        try:
            # Inference với imgsz=320, stream=False, verbose=False
            results = self.model(
                frame,
                imgsz=self.imgsz,
                verbose=False,
                device=self.device,
                conf=self.conf_threshold
            )
        except Exception as e:
            print(f"[⚠️ YOLO DETECT ERROR] Lỗi trong quá trình inference: {e}")
            return DetectionResult(summary_text="Lỗi nhận diện hình ảnh.")

        inference_time = round(time.time() - t_start, 4)
        
        person_count = 0
        max_person_ratio = 0.0
        detected_items = []
        counts_by_class: Dict[str, int] = {}

        for r in results:
            for box in r.boxes:
                b = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                conf = float(box.conf[0].cpu().item())
                cls_id = int(box.cls[0].item())
                label = self.model.names[cls_id]

                # Tính diện tích bounding box
                box_w = max(0.0, float(b[2] - b[0]))
                box_h = max(0.0, float(b[3] - b[1]))
                box_area = box_w * box_h
                area_ratio = box_area / frame_area if frame_area > 0 else 0.0

                detected_items.append({
                    "label": label,
                    "confidence": round(conf, 2),
                    "bbox": [round(coord, 1) for coord in b],
                    "area_ratio": round(area_ratio, 3)
                })

                counts_by_class[label] = counts_by_class.get(label, 0) + 1

        # Cập nhật bộ theo dõi định danh đa đối tượng (MOT Tracker) cho class 'person'
        person_detections = [item for item in detected_items if item["label"] == "person"]
        tracked_persons = self.tracker.update(person_detections, frame_area)
        
        person_count = len(tracked_persons)
        max_person_ratio = max([t.area_ratio for t in tracked_persons]) if tracked_persons else 0.0

        # Tổng hợp mô tả tóm tắt
        if detected_items:
            summary_parts = [f"{cnt} {cls}" for cls, cnt in counts_by_class.items()]
            summary_text = "Phát hiện: " + ", ".join(summary_parts)
            if tracked_persons:
                ids_str = ", ".join([f"ID#{t.track_id}" for t in tracked_persons])
                summary_text += f" (Đang theo dõi: {ids_str})"
        else:
            summary_text = "Không phát hiện đối tượng nào rõ ràng."

        annotated_img = None
        if annotate and len(results) > 0:
            annotated_img = results[0].plot()

        return DetectionResult(
            has_person=(person_count > 0),
            person_count=person_count,
            max_person_ratio=round(max_person_ratio, 3),
            tracked_persons=tracked_persons,
            objects_detected=detected_items,
            summary_text=summary_text,
            inference_time_sec=inference_time,
            annotated_frame=annotated_img
        )
