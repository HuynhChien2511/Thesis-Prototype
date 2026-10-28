"""
Module Quản lý Ngữ cảnh Thị giác & Multimodal VQA (Visual Question Answering).
Kết nối luồng Camera và Bộ nhận diện YOLO với Não bộ LLM:
  1. Giám sát thời gian thực người đến gần để kích hoạt chào hỏi chủ động (Proactive Greeting).
  2. Phát hiện câu hỏi liên quan đến thị giác để chụp ảnh gửi vào Gemini 2.5 Flash.
"""
import io
import time
import base64
import threading
from typing import Optional, Callable, Dict, Any, List
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from .camera import VideoCaptureThread
from .detector import ObjectDetector, DetectionResult
from ..config import (
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    PROACTIVE_GREETING_ENABLED,
    PROACTIVE_GREETING_RATIO,
    PROACTIVE_COOLDOWN_SEC
)

# Từ khóa nhận biết người dùng đang đặt câu hỏi về thị giác / không gian trước mặt
VISUAL_QUERY_KEYWORDS = [
    "thấy gì", "trước mặt", "nhìn", "xem hộ", "xem giúp", "đây là gì",
    "giấy này", "tờ này", "cầm gì", "bao nhiêu người",
    "mấy người", "ai đây", "áo gì", "màu gì", "ở đâu trong phòng",
    "vật gì", "đang làm gì"
]


class VisionContextManager:
    """
    Quản lý ngữ cảnh thị giác đa phương thức của Robot:
    - Chạy luồng quét nền (Background Vision Loop) kết hợp bộ theo dõi MOT.
    - Quản lý trạng thái chào hỏi theo từng người (Track ID) chống spam lặp lại.
    - Hỗ trợ chụp Frame gửi kèm Prompt cho mô hình Gemini Vision.
    """
    def __init__(
        self,
        camera: VideoCaptureThread,
        detector: ObjectDetector,
        on_person_detected: Optional[Callable[[DetectionResult, bool], None]] = None
    ):
        self.camera = camera
        self.detector = detector
        self.on_person_detected = on_person_detected
        
        self.latest_result: DetectionResult = DetectionResult()
        self._lock = threading.Lock()
        
        self._is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        self.greeting_paused = False  # Tạm dừng chào khi đang trong phiên hỏi đáp
        self.consecutive_ungreeted_frames: int = 0
        
        # Client Gemini Vision
        self._genai_client = None

    def pause_greeting(self):
        """Tạm dừng kích hoạt chào hỏi (dùng khi người dùng đang đàm thoại)."""
        self.greeting_paused = True

    def resume_greeting(self):
        """Bật lại cơ chế chào hỏi chủ động khi trở về màn hình chờ."""
        self.greeting_paused = False
        self.consecutive_ungreeted_frames = 0

    def start_monitoring(self):
        """Bắt đầu luồng giám sát thị giác chạy nền."""
        if self._is_monitoring:
            return

        if not self.camera.is_connected:
            started = self.camera.start()
            if not started:
                print("[⚠️ VISION] Không thể khởi động Camera để giám sát.")
                return

        self._is_monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        print("[👁️ VISION MONITOR] Đã kích hoạt luồng giám sát thị giác & MOT Tracker thời gian thực.")

    def _monitoring_loop(self):
        """Vòng lặp chạy nền nhận diện & theo dõi định danh người."""
        while self._is_monitoring:
            frame = self.camera.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            # Nhận diện & theo dõi đối tượng (YOLOv8n + IoU Tracker ~15-20ms)
            result = self.detector.detect(frame, annotate=False)
            
            with self._lock:
                self.latest_result = result

            # Kiểm tra điều kiện kích hoạt Lời chào chủ động (Proactive Greeting)
            # Chỉ chào khi: 
            # 1. Không bị pause (không trong phiên hỏi đáp)
            # 2. Cờ PROACTIVE_GREETING_ENABLED bật
            # 3. Có người chưa từng được chào (ungreeted person) và đứng đủ gần (ratio >= threshold)
            if PROACTIVE_GREETING_ENABLED and not self.greeting_paused and result.has_person:
                ungreeted_close_persons = [
                    t for t in result.tracked_persons
                    if (not t.is_greeted) and (t.area_ratio >= PROACTIVE_GREETING_RATIO)
                ]

                if ungreeted_close_persons:
                    self.consecutive_ungreeted_frames += 1
                else:
                    self.consecutive_ungreeted_frames = max(0, self.consecutive_ungreeted_frames - 1)

                # Yêu cầu xuất hiện ổn định ít nhất 3 frames liên tiếp (~0.25s) để chống nhiễu
                if self.consecutive_ungreeted_frames >= 3:
                    self.consecutive_ungreeted_frames = 0
                    
                    # Xác định nhóm đông hay người đơn lẻ
                    total_people = result.person_count
                    is_group = (total_people > 1)
                    
                    # Đánh dấu TẤT CẢ các ID người đang có mặt là ĐÃ CHÀO (chống chào lại cùng người này)
                    current_track_ids = [t.track_id for t in result.tracked_persons]
                    self.detector.tracker.mark_as_greeted(current_track_ids)
                    for t in result.tracked_persons:
                        t.is_greeted = True

                    ids_str = ", ".join([f"ID#{tid}" for tid in current_track_ids])
                    if is_group:
                        print(f"\n[🔔 PROACTIVE TRIGGER] Phát hiện nhóm {total_people} người mới đến ({ids_str})! Kích hoạt chào nhóm.")
                    else:
                        print(f"\n[🔔 PROACTIVE TRIGGER] Phát hiện người mới đến ({ids_str}, Tỷ lệ: {result.max_person_ratio*100:.1f}%)! Kích hoạt chào đón.")

                    if self.on_person_detected:
                        try:
                            self.on_person_detected(result, is_group)
                        except Exception as ex:
                            print(f"[⚠️ ERROR] Lỗi khi thực thi callback chào hỏi: {ex}")
            else:
                self.consecutive_ungreeted_frames = 0

            # Nghỉ ngắn giữa các chu kỳ quét để tiết kiệm CPU
            time.sleep(0.08)

    def get_current_perception(self) -> DetectionResult:
        """Lấy kết quả nhận diện mới nhất."""
        with self._lock:
            return self.latest_result

    def is_visual_query(self, query: str) -> bool:
        """Xác định câu hỏi của người dùng có cần quan sát hình ảnh hay không."""
        if not query:
            return False
        clean_q = query.lower()
        for kw in VISUAL_QUERY_KEYWORDS:
            if kw in clean_q:
                return True
        return False

    def capture_frame_jpeg(self) -> Optional[bytes]:
        """Chụp 1 khung hình hiện tại từ Camera và nén thành byte JPEG."""
        frame = self.camera.get_frame()
        if frame is None or cv2 is None:
            return None
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if success:
            return buffer.tobytes()
        return None

    def ask_multimodal_vision(self, question: str, jpeg_bytes: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Gửi câu hỏi và hình ảnh camera trực tiếp tới mô hình Gemini 2.5 Flash để thị giác giải đáp.
        """
        import time
        t_start = time.time()
        
        if jpeg_bytes is None:
            jpeg_bytes = self.capture_frame_jpeg()

        if jpeg_bytes is None:
            return {
                "answer": "Rất tiếc, hiện tại camera của tôi đang bận hoặc không ghi nhận được hình ảnh.",
                "latency_sec": 0.0,
                "success": False
            }

        try:
            from google import genai
            from google.genai import types

            if self._genai_client is None:
                self._genai_client = genai.Client(api_key=GOOGLE_API_KEY)

            system_instruction = (
                "Bạn là Robot Trợ lý Hành chính công thông minh có gắn Camera trước ngực. "
                "Hãy quan sát hình ảnh được chụp trực tiếp từ camera của bạn và trả lời câu hỏi "
                "của công dân một cách lịch sự, chính xác, ngắn gọn bằng tiếng Việt. "
                "Nếu là giấy tờ tùy thân, hãy đọc và giải thích loại giấy tờ hoặc thủ tục liên quan."
            )

            response = self._genai_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                    question
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2
                )
            )

            latency = round(time.time() - t_start, 2)
            answer_text = response.text.strip() if response.text else "Không nhận được phản hồi từ mô hình thị giác."

            return {
                "answer": answer_text,
                "latency_sec": latency,
                "success": True
            }
        except Exception as e:
            print(f"[❌ MULTIMODAL ERROR] Lỗi khi gọi Gemini Vision API: {e}")
            return {
                "answer": f"Có lỗi khi xử lý hình ảnh từ camera: {str(e)}",
                "latency_sec": round(time.time() - t_start, 2),
                "success": False
            }

    def stop_monitoring(self):
        """Dừng luồng giám sát thị giác."""
        self._is_monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        print("[👁️ VISION MONITOR] Đã dừng luồng giám sát thị giác.")
