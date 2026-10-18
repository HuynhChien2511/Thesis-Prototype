"""
Module Speech-to-Text (STT) nhận diện giọng nói tiếng Việt bằng Faster-Whisper (Sprint 2 - Đôi tai).
Chạy tăng tốc trên GPU NVIDIA (CUDA) với cơ chế tự động Fallback sang CPU nếu cần.
"""
import sys
import time
from pathlib import Path
from typing import Union, Dict, Any

# Thêm thư mục prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

import os
import site

# Tự động nạp các thư viện NVIDIA CUDA DLL trên Windows nếu có
for sp in site.getsitepackages():
    nvidia_dir = Path(sp) / "nvidia"
    if nvidia_dir.exists():
        for bin_dir in nvidia_dir.glob("*/bin"):
            if bin_dir.is_dir():
                try:
                    os.add_dll_directory(str(bin_dir))
                    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
                except Exception:
                    pass

import numpy as np
from faster_whisper import WhisperModel

from src.config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    AUDIO_SAMPLE_RATE
)

# Đảm bảo UTF-8 console trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


class SpeechToText:
    def __init__(
        self,
        model_name: str = WHISPER_MODEL,
        device: str = WHISPER_DEVICE,
        compute_type: str = WHISPER_COMPUTE_TYPE
    ):
        """Khởi tạo mô hình Faster-Whisper."""
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model = self._load_model()

    def _load_model(self) -> WhisperModel:
        """Tải mô hình Faster-Whisper với cơ chế Fallback an toàn."""
        print(f"[*] Đang nạp mô hình Whisper '{self.model_name}' trên thiết bị '{self.device}' ({self.compute_type})...")
        try:
            model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            print(f"[SUCCESS] Đã nạp thành công mô hình Whisper trên GPU {self.device.upper()}.")
            return model
        except Exception as e:
            print(f"[!] Không thể khởi chạy trên {self.device}: {e}")
            print("[*] Đang tự động chuyển sang chế độ CPU (compute_type='int8')...")
            self.device = "cpu"
            self.compute_type = "int8"
            model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8"
            )
            print("[SUCCESS] Đã nạp thành công mô hình Whisper trên CPU.")
            return model

    def transcribe(self, audio_input: Union[str, Path, np.ndarray]) -> Dict[str, Any]:
        """
        Nhận diện giọng nói từ file âm thanh hoặc mảng numpy (16kHz float32):
        - language='vi' (cố định tiếng Việt)
        - task='transcribe'
        - beam_size=5
        """
        start_time = time.time()
        
        # Tính độ dài âm thanh nếu đầu vào là numpy array
        duration_sec = 0.0
        if isinstance(audio_input, np.ndarray):
            duration_sec = round(len(audio_input) / AUDIO_SAMPLE_RATE, 2)
            if len(audio_input) == 0:
                return {
                    "text": "",
                    "language": "vi",
                    "probability": 0.0,
                    "latency_sec": 0.0,
                    "duration_sec": 0.0
                }

        # Gợi ý ngữ cảnh chuyên ngành hành chính công để Whisper nhận diện chuẩn xác thuật ngữ
        admin_prompt = "Hệ thống trợ lý dịch vụ hành chính công: căn cước, căn cước công dân, CCCD, tạm trú, thường trú, kết hôn, khai sinh, VNeID, UBND."

        # Gọi Faster-Whisper giải mã âm thanh
        segments, info = self.model.transcribe(
            audio_input,
            language="vi",
            task="transcribe",
            initial_prompt=admin_prompt,
            beam_size=5,
            vad_filter=True, # Lọc bỏ khoảng lặng nhưng giữ đệm an toàn không cắt nuốt từ
            vad_parameters=dict(
                min_silence_duration_ms=800,
                speech_pad_ms=400
            )
        )

        # Ghép các phân đoạn text
        text_segments = [seg.text.strip() for seg in segments]
        full_text = " ".join(text_segments).strip()

        # Chuẩn hóa viết hoa chữ cái đầu và xóa dấu chấm thừa ở cuối
        if full_text:
            full_text = full_text[0].upper() + full_text[1:]
            # Xóa các ký tự lặp rác do khoảng lặng nếu có
            if full_text.endswith("..."):
                full_text = full_text[:-3].strip()

        latency_sec = round(time.time() - start_time, 2)
        if duration_sec == 0.0 and hasattr(info, "duration") and info.duration:
            duration_sec = round(info.duration, 2)

        return {
            "text": full_text,
            "language": info.language,
            "probability": round(info.language_probability, 2),
            "latency_sec": latency_sec,
            "duration_sec": duration_sec
        }


if __name__ == "__main__":
    stt = SpeechToText()
    print("[+] Khởi tạo STT thành công. Sẵn sàng nhận diện giọng nói.")
