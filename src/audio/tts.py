"""
Module Text-to-Speech (TTS) tổng hợp và phát giọng nói tiếng Việt (Sprint 3 - Khuôn miệng).
- Tích hợp edge-tts với giọng nơ-ron tự nhiên (Hoài My / Nam Minh)
- Tự động chuẩn hóa văn bản, tẩy Markdown và giải mã từ viết tắt
- Phát âm thanh trực tiếp qua loa laptop bằng Pygame Mixer
"""
import os
import sys
import time
import asyncio
import threading
from pathlib import Path
from typing import Union, Dict, Any, Optional

# Tắt thông báo chào mừng của pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# Thêm thư mục prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

import pygame
import edge_tts

from src.config import TTS_VOICE, TTS_RATE, TTS_PITCH, DATA_DIR
from src.audio.text_normalizer import normalize_for_tts

DEFAULT_TTS_AUDIO = DATA_DIR / "last_tts_response.mp3"

# Đảm bảo UTF-8 console trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


class TextToSpeech:
    def __init__(
        self,
        voice: str = TTS_VOICE,
        rate: str = TTS_RATE,
        pitch: str = TTS_PITCH
    ):
        """Khởi tạo cấu hình Text-to-Speech."""
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self._synth_lock = threading.Lock()
        self._play_lock = threading.Lock()
        self._init_mixer()

    def _init_mixer(self):
        """Khởi tạo bộ phát âm thanh pygame mixer với tần số 24kHz (chuẩn edge-tts) nếu chưa bật."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=24000)
            except Exception as e:
                print(f"[!] Lỗi khởi tạo pygame mixer: {e}")

    async def _async_synthesize(self, text: str, output_path: Path, max_retries: int = 3):
        """Hàm bất đồng bộ gọi API edge-tts với cơ chế thử lại tự động (retry) chống rớt mạng."""
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.voice,
                    rate=self.rate,
                    pitch=self.pitch
                )
                await communicate.save(str(output_path))
                return
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.5)
        if last_error:
            raise last_error

    def synthesize(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Tổng hợp giọng nói từ văn bản:
        1. Chuẩn hóa text (tẩy markdown, đọc từ viết tắt)
        2. Sinh file âm thanh mp3 qua edge-tts (Thread-safe)
        3. Đo độ trễ (latency)
        """
        start_time = time.time()
        
        # 1. Chuẩn hóa câu nói
        cleaned_text = normalize_for_tts(text)
        if not cleaned_text:
            return {
                "audio_path": None,
                "cleaned_text": "",
                "latency_sec": 0.0
            }

        with self._synth_lock:
            # 2. Đường dẫn file đầu ra (dùng timestamp tránh va chạm giữa các luồng)
            if output_path:
                target_path = Path(output_path)
            else:
                target_path = DATA_DIR / f"tts_{int(time.time()*1000)}.mp3"
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 3. Chạy tổng hợp giọng nói (bọc try-except chống sập do mất mạng)
            try:
                asyncio.run(self._async_synthesize(cleaned_text, target_path))
                # Tạo bản copy vào file mặc định để tương thích các script cũ
                if target_path != DEFAULT_TTS_AUDIO and target_path.exists():
                    try:
                        import shutil
                        shutil.copyfile(target_path, DEFAULT_TTS_AUDIO)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[!] Lỗi kết nối tổng hợp giọng nói Edge-TTS: {e}")
                return {
                    "audio_path": None,
                    "cleaned_text": cleaned_text,
                    "latency_sec": round(time.time() - start_time, 2)
                }

        latency_sec = round(time.time() - start_time, 2)
        return {
            "audio_path": target_path,
            "cleaned_text": cleaned_text,
            "latency_sec": latency_sec
        }

    def play(self, audio_path: Union[str, Path], block: bool = True):
        """
        Phát file âm thanh ra loa ngoài (Thread-safe):
        - block=True: Đợi phát xong hết câu mới trả quyền điều khiển
        - block=False: Phát nền không chặn luồng
        """
        with self._play_lock:
            self._init_mixer()
            audio_file = str(audio_path)
            if not Path(audio_file).exists():
                print(f"[!] Không tìm thấy file âm thanh để phát: {audio_file}")
                return
            
            try:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                
                if block:
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(20)
                    # Giải phóng khóa file trên Windows để các lần gọi sau không bị PermissionError
                    pygame.mixer.music.unload()
            except Exception as e:
                print(f"[!] Lỗi khi phát âm thanh {audio_file}: {e}")

    def stop(self):
        """Dừng phát âm thanh ngay lập tức và giải phóng file."""
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

    def speak(self, text: str, block: bool = True) -> Dict[str, Any]:
        """
        Hàm tiện ích trọn gói:
        Văn bản -> Chuẩn hóa -> Sinh giọng nói MP3 -> Phát ngay ra Loa.
        """
        res = self.synthesize(text)
        if res["audio_path"] and res["audio_path"].exists():
            print(f"[*] Đang phát ra loa ({self.voice})...")
            self.play(res["audio_path"], block=block)
        return res


if __name__ == "__main__":
    tts = TextToSpeech()
    test_phrase = "Xin chào Quý công dân. Tôi là trợ lý AI hỗ trợ dịch vụ hành chính công."
    print("=" * 60)
    print(f"[*] Thử nghiệm giọng nói ({tts.voice}): \"{test_phrase}\"")
    tts.speak(test_phrase, block=True)
    print("[SUCCESS] Đã phát xong ra loa.")
    print("=" * 60)
