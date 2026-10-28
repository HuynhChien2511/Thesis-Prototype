"""
Module quản lý luồng hình ảnh Camera thời gian thực (Zero-lag Threaded Camera).
Sử dụng OpenCV với luồng nền (Daemon Thread) chuyên đọc frame mới nhất,
loại bỏ hoàn toàn tình trạng trễ bộ đệm (frame buffer lag).
"""
import time
import threading
from typing import Optional, Tuple
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


class VideoCaptureThread:
    """
    Luồng thu nhận khung hình Camera thời gian thực.
    Đảm bảo get_frame() luôn trả về khung hình mới nhất tại thời điểm gọi.
    """
    def __init__(
        self,
        source: int | str = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30
    ):
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        
        self.cap: Optional[object] = None
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self.current_frame: Optional[np.ndarray] = None
        self.last_update_time: float = 0.0
        self.is_connected = False

    def start(self) -> bool:
        """Khởi động camera và bắt đầu luồng đọc frame nền."""
        if cv2 is None:
            print("[❌ CAMERA ERROR] Thư viện opencv-python chưa được cài đặt!")
            return False

        if self._is_running:
            return True

        print(f"[📷 CAMERA] Đang mở nguồn thiết bị Camera (source={self.source})...")
        try:
            self.cap = cv2.VideoCapture(self.source)
        except Exception as e:
            print(f"[❌ CAMERA ERROR] Không thể mở camera {self.source}: {e}")
            return False

        if not self.cap or not self.cap.isOpened():
            print(f"[⚠️ CAMERA WARNING] Không thể kết nối tới Camera index {self.source}.")
            self.is_connected = False
            return False

        # Tối ưu hóa phần cứng: độ phân giải và bộ đệm
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Đọc thử 1 frame đầu tiên
        ret, frame = self.cap.read()
        if not ret or frame is None:
            print(f"[⚠️ CAMERA WARNING] Camera mở thành công nhưng không đọc được tín hiệu hình ảnh.")
            self.is_connected = False
            return False

        with self._lock:
            self.current_frame = frame.copy()
            self.last_update_time = time.time()
            self.is_connected = True

        self._is_running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        print(f"[✅ CAMERA READY] Camera đã sẵn sàng (Độ phân giải: {self.width}x{self.height}).")
        return True

    def _capture_loop(self):
        """Vòng lặp đọc frame liên tục chạy trên luồng nền."""
        while self._is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            with self._lock:
                self.current_frame = frame
                self.last_update_time = time.time()

            # Giới hạn tốc độ đọc theo fps mong muốn để tiết kiệm CPU
            time.sleep(1.0 / (self.fps * 1.5))

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Lấy khung hình mới nhất (Thread-safe).
        Trả về bản sao numpy array (BGR) hoặc None nếu camera chưa sẵn sàng.
        """
        with self._lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def stop(self):
        """Dừng luồng camera và giải phóng tài nguyên phần cứng."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.is_connected = False
        print("[📷 CAMERA] Đã đóng camera và giải phóng tài nguyên phần cứng.")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
