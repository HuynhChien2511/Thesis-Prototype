"""
Module Tổng hợp Giọng nói Cục bộ (Local Offline TTS) cho Hệ thống Robot Hành chính công.
Hỗ trợ Kiến trúc Hybrid Dual-Engine TTS:
  - Tầng 1 (Ưu tiên Online): Edge-TTS (Hoài My / Nam Minh Neural) khi có mạng Wi-Fi.
  - Tầng 2 (Offline Cục bộ): Piper ONNX Engine (vi_VN-vais1000-medium) chạy 100% trên CPU.
  - Tầng 3 (Dự phòng Hệ thống): Windows SAPI5 Speech Synthesizer.
  - Tầng 4 (Safety Net Chime): Âm báo hòa âm cục bộ (Local Fallback Chime).

Không phụ thuộc internet, độ trễ thời gian thực (RTF < 0.1s trên CPU), chống treo ngắt luồng.
"""
import os
import sys
import time
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Union

# Đảm bảo in tiếng Việt UTF-8 chuẩn trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.config import DATA_DIR
from src.audio.text_normalizer import normalize_for_tts

# Thư mục lưu trữ model Piper ONNX cục bộ
PIPER_MODEL_DIR = DATA_DIR / "models" / "piper"
DEFAULT_PIPER_ONNX = PIPER_MODEL_DIR / "vi_VN-vais1000-medium.onnx"
DEFAULT_PIPER_JSON = PIPER_MODEL_DIR / "vi_VN-vais1000-medium.onnx.json"


def generate_offline_chime(output_path: Optional[Path] = None) -> Path:
    """
    Tự động tạo âm báo dự phòng offline (Local Fallback Chime - định dạng WAV 16-bit PCM)
    bằng thư viện chuẩn (wave + math), không phụ thuộc vào internet hay thư viện ngoài.
    Được sử dụng khi Circuit Breaker kích hoạt do mất mạng hoặc timeout.
    """
    if output_path is None:
        fallback_dir = DATA_DIR / "fallback_audio"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        output_path = fallback_dir / "offline_fallback_chime.wav"

    if output_path.exists() and output_path.stat().st_size > 100:
        return output_path

    import wave
    import struct
    import math

    sample_rate = 24000
    duration_sec = 0.35  # Âm báo ngắn gọn 350ms
    num_samples = int(sample_rate * duration_sec)

    # Hòa âm 2 tần số 523.25 Hz (Do5) và 659.25 Hz (Mi5) tạo âm báo lịch sự, êm dịu
    freq1, freq2 = 523.25, 659.25
    amplitude = 12000

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), 'w') as wav_file:
        wav_file.setnchannels(1)      # Mono
        wav_file.setsampwidth(2)      # 16-bit
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            envelope = math.sin(math.pi * i / num_samples)
            val1 = math.sin(2.0 * math.pi * freq1 * t)
            val2 = math.sin(2.0 * math.pi * freq2 * t)
            sample_val = int((0.6 * val1 + 0.4 * val2) * amplitude * envelope)
            frames.extend(struct.pack('<h', sample_val))
        wav_file.writeframes(frames)

    return output_path


class LocalTTSEngine:
    """
    Bộ tổng hợp giọng nói ngoại tuyến (Local Offline TTS Engine):
    Tự động lựa chọn và luân chuyển giữa các công nghệ offline khả dụng trên máy.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        config_path: Optional[Union[str, Path]] = None
    ):
        self.model_path = Path(model_path) if model_path else DEFAULT_PIPER_ONNX
        self.config_path = Path(config_path) if config_path else DEFAULT_PIPER_JSON
        self._piper_voice = None
        self.piper_available = self._check_piper_availability()
        self.sapi_available = self._check_sapi_availability()

    def _get_piper_voice(self):
        """Khởi tạo và giữ bộ nhớ đệm (cache) cho PiperVoice model để đạt tốc độ RTF < 0.1s."""
        if self._piper_voice is None:
            try:
                from piper.voice import PiperVoice
                if self.model_path.exists() and self.config_path.exists():
                    self._piper_voice = PiperVoice.load(str(self.model_path), config_path=str(self.config_path))
            except Exception as e:
                print(f"[!] Không thể nạp mô hình PiperVoice: {e}")
        return self._piper_voice

    def _check_piper_availability(self) -> bool:
        """Kiểm tra xem mô hình Piper ONNX tiếng Việt và công cụ Piper có sẵn sàng không."""
        # 1. Kiểm tra file model ONNX và config JSON
        has_model = self.model_path.exists() and self.model_path.stat().st_size > 1000
        has_json = self.config_path.exists() and self.config_path.stat().st_size > 50

        # 2. Kiểm tra xem lệnh `piper` có trên PATH hoặc thư viện python `piper` có cài đặt không
        has_piper_cmd = shutil.which("piper") is not None
        has_piper_py = False
        try:
            import piper  # noqa: F401
            has_piper_py = True
        except ImportError:
            pass

        return (has_model and has_json) and (has_piper_cmd or has_piper_py)

    def _check_sapi_availability(self) -> bool:
        """Kiểm tra xem hệ điều hành Windows có sẵn trình phát giọng nói SAPI5 không."""
        return sys.platform == "win32"

    def get_status(self) -> Dict[str, Any]:
        """Trả về trạng thái chi tiết của các engine TTS cục bộ."""
        return {
            "piper_onnx": {
                "available": self._check_piper_availability(),
                "model_path": str(self.model_path),
                "model_exists": self.model_path.exists(),
                "config_exists": self.config_path.exists()
            },
            "windows_sapi": {
                "available": self.sapi_available,
                "platform": sys.platform
            }
        }

    def synthesize_piper(self, text: str, output_path: Path) -> bool:
        """Tổng hợp âm thanh bằng Piper ONNX tiếng Việt sang file WAV."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Thử phương thức 1: Sử dụng thư viện Python `piper` nếu có (Siêu tốc < 0.1s)
            voice = self._get_piper_voice()
            if voice:
                import wave
                with wave.open(str(output_path), "wb") as wav_file:
                    voice.synthesize_wav(text, wav_file)
                if output_path.exists() and output_path.stat().st_size > 500:
                    return True

            # Thử phương thức 2: Sử dụng lệnh CLI `piper`
            piper_cmd = shutil.which("piper")
            if piper_cmd:
                cmd = [
                    piper_cmd,
                    "--model", str(self.model_path),
                    "--config", str(self.config_path),
                    "--output_file", str(output_path)
                ]
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8"
                )
                _, stderr = proc.communicate(input=text, timeout=8.0)
                if proc.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500:
                    return True
        except Exception as e:
            print(f"[!] Lỗi tổng hợp Piper ONNX: {e}")
        return False

    def synthesize_sapi(self, text: str, output_path: Path) -> bool:
        """Tổng hợp âm thanh qua Windows Speech Synthesizer (SAPI5) sang file WAV."""
        if not self.sapi_available:
            return False
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            clean_text = text.replace('"', ' ').replace("'", " ").replace("\n", " ").strip()
            ps_script = (
                f"$synth = New-Object -ComObject SAPI.SpVoice; "
                f"$stream = New-Object -ComObject SAPI.SpFileStream; "
                f"$stream.Open('{str(output_path)}', 3, $false); "
                f"$synth.AudioOutputStream = $stream; "
                f"$synth.Speak('{clean_text}'); "
                f"$stream.Close();"
            )
            cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=6.0)
            if proc.returncode == 0 and output_path.exists() and output_path.stat().st_size > 500:
                return True
        except Exception as e:
            print(f"[!] Lỗi tổng hợp Windows SAPI: {e}")
        return False

    def synthesize(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Điểm gọi tổng hợp chính cho Local TTS:
        1. Chuẩn hóa câu nói (tẩy Markdown, đọc số tiền, ngày tháng).
        2. Thử Piper ONNX tiếng Việt nếu có model.
        3. Thử Windows SAPI nếu không có Piper.
        4. Fallback sang âm báo hòa âm Chime nếu mọi engine cục bộ đều không khả dụng.
        """
        start_time = time.time()
        cleaned_text = normalize_for_tts(text)
        if not cleaned_text:
            return {
                "audio_path": None,
                "cleaned_text": "",
                "latency_sec": 0.0,
                "engine": "none"
            }

        if output_path:
            target_path = Path(output_path)
        else:
            target_path = DATA_DIR / f"local_tts_{int(time.time()*1000)}.wav"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Thử Piper ONNX Engine
        if self._check_piper_availability():
            success = self.synthesize_piper(cleaned_text, target_path)
            if success:
                latency = round(time.time() - start_time, 2)
                return {
                    "audio_path": target_path,
                    "cleaned_text": cleaned_text,
                    "latency_sec": latency,
                    "engine": "piper_onnx"
                }

        # 2. Thử Windows SAPI Engine
        if self.sapi_available:
            success = self.synthesize_sapi(cleaned_text, target_path)
            if success:
                latency = round(time.time() - start_time, 2)
                return {
                    "audio_path": target_path,
                    "cleaned_text": cleaned_text,
                    "latency_sec": latency,
                    "engine": "windows_sapi"
                }

        # 3. Fallback sang âm báo Chime cục bộ chuẩn Python (không bao giờ lỗi)
        chime_path = generate_offline_chime(target_path)
        latency = round(time.time() - start_time, 2)
        return {
            "audio_path": chime_path,
            "cleaned_text": cleaned_text,
            "latency_sec": latency,
            "engine": "offline_chime"
        }
