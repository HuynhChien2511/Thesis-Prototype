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
from typing import Union, Dict, Any, Optional, List

# Tắt thông báo chào mừng của pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# Thêm thư mục prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

import pygame
import edge_tts

from src.config import TTS_VOICE, TTS_RATE, TTS_PITCH, TTS_ENGINE, DATA_DIR
from src.audio.text_normalizer import normalize_for_tts
from src.audio.local_tts import LocalTTSEngine, generate_offline_chime

DEFAULT_TTS_AUDIO = DATA_DIR / "last_tts_response.mp3"

# Đảm bảo UTF-8 console trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


def split_sentences(text: str, min_chars: int = 30) -> List[str]:
    """
    Tách văn bản thành các câu hoàn chỉnh phục vụ cho Sentence-Boundary Streaming TTS:
    - Bảo vệ số tiền (50.000 đồng, 2.500.000 VNĐ), số thập phân (1.5 ngày), ngày tháng (15/10/2024, 01.07.2024).
    - Bảo vệ các từ viết tắt tiếng Việt hành chính và học hàm (TP.HCM, TP. HCM, UBND, TS., ThS., BS., PGS., GS., Đ/c, v.v., NĐ-CP).
    - Bảo vệ tên miền (dichvucong.gov.vn, bocongan.gov.vn) và dấu chấm lửng (...).
    - Ngắt theo dấu chấm, chấm than, chấm hỏi kèm khoảng trắng.
    - Gom các đoạn quá ngắn (< min_chars) vào câu tiếp theo để tránh đọc giật cục.
    """
    if not text:
        return []
    import re

    # Sử dụng sentinel placeholder để bảo vệ các dấu chấm không phải ranh giới câu
    DOT_PLACEHOLDER = "@@DOT@@"
    protected = text.strip()

    # 1. Bảo vệ dấu chấm lửng (...)
    protected = re.sub(r"\.{3,}", "@@ELLIPSIS@@", protected)

    # 2. Bảo vệ số thập phân và phân cách hàng nghìn (ví dụ: 50.000, 1.5, 2.500.000)
    protected = re.sub(r"(\d+)\.(\d+)", r"\1" + DOT_PLACEHOLDER + r"\2", protected)
    protected = re.sub(r"(\d+)\.(\d+)", r"\1" + DOT_PLACEHOLDER + r"\2", protected)

    # 3. Bảo vệ các từ viết tắt phổ biến có dấu chấm (TP., Tp., TS., Ts., ThS., BS., PGS., GS., Đ/c, v.v., Số., v.v)
    common_abbrs = [
        r"TP", r"Tp", r"TS", r"Ts", r"ThS", r"BS", r"PGS", r"GS",
        r"Đ/c", r"đ/c", r"Số", r"số", r"v\.v", r"tr", r"k/g", r"K/g"
    ]
    for abbr in common_abbrs:
        protected = re.sub(rf"\b{abbr}\.", abbr.replace(".", DOT_PLACEHOLDER) + DOT_PLACEHOLDER, protected)

    # 4. Bảo vệ tên miền internet (ví dụ .gov.vn, .vn, .com, .edu.vn)
    protected = re.sub(r"\.(gov|vn|com|org|edu|net)\b", DOT_PLACEHOLDER + r"\1", protected)

    # 5. Tách thành các đoạn thô dựa trên ranh giới câu thực sự: dấu câu (. ! ? hoặc xuống dòng) theo sau bởi khoảng trắng
    raw_chunks = re.split(r"(?<=[.!?\n])\s+", protected)

    sentences = []
    current_buf = ""
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if not current_buf:
            current_buf = chunk
        else:
            current_buf += " " + chunk

        # Kiểm tra xem câu đệm hiện tại có kết thúc bằng dấu chấm/than/hỏi thực sự không
        has_ending_punct = any(current_buf.endswith(p) for p in [".", "!", "?", "@@ELLIPSIS@@"])
        if len(current_buf) >= min_chars and has_ending_punct:
            sentences.append(current_buf)
            current_buf = ""

    if current_buf:
        if sentences and len(current_buf) < min_chars:
            sentences[-1] += " " + current_buf
        else:
            sentences.append(current_buf)

    # Khôi phục các sentinel placeholder về lại dấu chấm gốc
    restored_sentences = []
    for s in sentences:
        s_restored = s.replace(DOT_PLACEHOLDER, ".").replace("@@ELLIPSIS@@", "...").strip()
        if s_restored:
            restored_sentences.append(s_restored)

    return restored_sentences if restored_sentences else [text.strip()]


class TextToSpeech:
    def __init__(
        self,
        voice: str = TTS_VOICE,
        rate: str = TTS_RATE,
        pitch: str = TTS_PITCH,
        engine_mode: Optional[str] = None
    ):
        """
        Khởi tạo cấu hình Text-to-Speech:
        - engine_mode: 'hybrid' (ưu tiên Online, rớt mạng chuyển Local), 'edge' (chỉ Online), 'local' (thuần Offline)
        """
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.engine_mode = (engine_mode or TTS_ENGINE).lower()
        self.local_engine = LocalTTSEngine()
        self._synth_lock = threading.Lock()
        self._play_lock = threading.Lock()
        self._streaming_stop_event: Optional[threading.Event] = None
        self._init_mixer()
        self.fallback_audio_path: Optional[Path] = None
        try:
            self.fallback_audio_path = generate_offline_chime()
        except Exception:
            pass

    def get_fallback_audio(self) -> Optional[Path]:
        """Lấy đường dẫn tệp âm báo dự phòng offline (Circuit Breaker Local Fallback)."""
        if self.fallback_audio_path and self.fallback_audio_path.exists():
            return self.fallback_audio_path
        try:
            self.fallback_audio_path = generate_offline_chime()
            return self.fallback_audio_path
        except Exception:
            return None

    def _init_mixer(self):
        """Khởi tạo bộ phát âm thanh pygame mixer với tần số 24kHz (chuẩn edge-tts) nếu chưa bật."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=24000)
            except Exception as e:
                print(f"[!] Lỗi khởi tạo pygame mixer: {e}")

    def _cleanup_old_cache(self, max_files: int = 15):
        """Tự động dọn dẹp các tệp âm thanh MP3 tạm thời cũ, chỉ giữ lại max_files tệp mới nhất."""
        try:
            mp3_files = sorted(DATA_DIR.glob("tts_*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
            if len(mp3_files) > max_files:
                for old_file in mp3_files[max_files:]:
                    try:
                        old_file.unlink()
                    except Exception:
                        pass
        except Exception:
            pass

    async def _async_synthesize(self, text: str, output_path: Path, timeout: float = 4.5, max_retries: int = 2):
        """
        Hàm bất đồng bộ gọi API edge-tts với cơ chế Circuit Breaker & Voice Consistency:
        - Giới hạn timeout cứng (mặc định 4.5s) cho mỗi lần gọi để triệt tiêu vĩnh viễn nguy cơ treo socket 60-80s.
        - Tự động thử lại max_retries lần nếu rớt gói mạng ngắn hạn.
        - Giữ nguyên giọng đọc được chọn (self.voice) để đảm bảo tính nhất quán (tránh nhảy xen kẽ giọng Nam/Nữ).
        """
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.voice,
                    rate=self.rate,
                    pitch=self.pitch
                )
                # Bọc timeout bảo vệ nghiêm ngặt chống treo mạng WebSocket
                await asyncio.wait_for(communicate.save(str(output_path)), timeout=timeout)
                if output_path.exists() and output_path.stat().st_size > 300:
                    return
            except (asyncio.TimeoutError, Exception) as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(0.3)
        if last_error:
            raise last_error

    async def synthesize_async(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Phiên bản async trực tiếp phục vụ cho FastAPI / ROS 2 Bridge trong tương lai."""
        start_time = time.time()
        cleaned_text = normalize_for_tts(text)
        if not cleaned_text:
            return {"audio_path": None, "cleaned_text": "", "latency_sec": 0.0}

        if output_path:
            target_path = Path(output_path)
        else:
            target_path = DATA_DIR / f"tts_{int(time.time()*1000)}.mp3"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            await self._async_synthesize(cleaned_text, target_path)
            if target_path != DEFAULT_TTS_AUDIO and target_path.exists():
                try:
                    import shutil
                    shutil.copyfile(target_path, DEFAULT_TTS_AUDIO)
                except Exception:
                    pass
            self._cleanup_old_cache(max_files=15)
        except Exception as e:
            print(f"[!] Lỗi kết nối tổng hợp giọng nói Edge-TTS (async): {e}")
            return {"audio_path": None, "cleaned_text": cleaned_text, "latency_sec": round(time.time() - start_time, 2)}

        return {
            "audio_path": target_path,
            "cleaned_text": cleaned_text,
            "latency_sec": round(time.time() - start_time, 2)
        }

    def synthesize(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        fallback_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Tổng hợp giọng nói từ văn bản (Hỗ trợ Kiến trúc Hybrid Dual-Engine):
        1. Chuẩn hóa text (tẩy markdown, đọc từ viết tắt)
        2. Nếu engine_mode == 'local': Sinh bằng Local TTS (Piper ONNX / Windows SAPI).
        3. Nếu engine_mode in ('hybrid', 'edge'): Thử Edge-TTS, nếu lỗi tự động chuyển mạch sang Local TTS.
        4. Kích hoạt Local Fallback Chime nếu mọi engine đều gặp sự cố.
        """
        start_time = time.time()
        
        # 1. Chuẩn hóa câu nói
        cleaned_text = normalize_for_tts(text)
        if not cleaned_text:
            return {
                "audio_path": None,
                "cleaned_text": "",
                "latency_sec": 0.0,
                "is_fallback": False
            }

        # Nếu chế độ là thuần Offline cục bộ
        if self.engine_mode == "local":
            return self.local_engine.synthesize(cleaned_text, output_path)

        with self._synth_lock:
            # 2. Đường dẫn file đầu ra (dùng timestamp tránh va chạm giữa các luồng)
            if output_path:
                target_path = Path(output_path)
            else:
                target_path = DATA_DIR / f"tts_{int(time.time()*1000)}.mp3"
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 3. Chạy tổng hợp giọng nói an toàn (tránh lỗi lồng Event Loop khi chạy trong web server)
            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                coro = self._async_synthesize(cleaned_text, target_path)
                try:
                    if loop and loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            pool.submit(asyncio.run, coro).result()
                    else:
                        asyncio.run(coro)
                except Exception:
                    try:
                        coro.close()
                    except Exception:
                        pass
                    raise

                # Tạo bản copy vào file mặc định để tương thích các script cũ
                if target_path != DEFAULT_TTS_AUDIO and target_path.exists():
                    try:
                        import shutil
                        shutil.copyfile(target_path, DEFAULT_TTS_AUDIO)
                    except Exception:
                        pass
                
                # Tự động dọn dẹp các tệp mp3 cũ để bảo vệ dung lượng đĩa
                self._cleanup_old_cache(max_files=15)
            except Exception as e:
                print(f"[!] Lỗi kết nối tổng hợp giọng nói Edge-TTS: {e}")
                # Kích hoạt cơ chế Chuyển mạch Lai (Hybrid Dual-Engine Fallback)
                if self.engine_mode == "hybrid":
                    print("[🔄 HYBRID TTS] Đang tự động chuyển mạch sang Local TTS cục bộ...")
                    try:
                        local_res = self.local_engine.synthesize(cleaned_text, target_path.with_suffix(".wav"))
                        if local_res.get("audio_path") and Path(local_res["audio_path"]).exists():
                            local_res["is_fallback"] = True
                            return local_res
                    except Exception as local_err:
                        print(f"[!] Lỗi Local TTS: {local_err}")

                fallback_path = self.get_fallback_audio() if fallback_on_error else None
                return {
                    "audio_path": fallback_path,
                    "cleaned_text": cleaned_text,
                    "latency_sec": round(time.time() - start_time, 2),
                    "is_fallback": fallback_path is not None
                }

        latency_sec = round(time.time() - start_time, 2)
        return {
            "audio_path": target_path,
            "cleaned_text": cleaned_text,
            "latency_sec": latency_sec,
            "is_fallback": False
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
        if self._streaming_stop_event is not None:
            self._streaming_stop_event.set()
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
        res = self.synthesize(text, fallback_on_error=True)
        if res["audio_path"] and res["audio_path"].exists():
            print(f"[*] Đang phát ra loa ({self.voice})...")
            self.play(res["audio_path"], block=block)
        return res

    def speak_streaming(
        self,
        text: str,
        on_first_audio_callback: Optional[Any] = None,
        block: bool = True,
        play_audio: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Phát âm thanh theo cơ chế Sentence-Boundary Streaming (Phát gối đầu song song):
        1. Tách văn bản thành các câu độc lập.
        2. Tổng hợp câu 1 và phát ngay lập tức (đưa TTFA xuống < 1.5s).
        3. Luồng nền tổng hợp tiếp câu 2, câu 3 gối đầu nạp vào hàng đợi AudioQueue.
        4. Loa phát tuần tự liền mạch không có khoảng lặng.
        """
        start_time = time.time()
        should_play = play_audio if play_audio is not None else block

        cleaned_text = normalize_for_tts(text)
        if not cleaned_text:
            return {"audio_path": None, "cleaned_text": "", "ttfa_sec": 0.0, "total_sec": 0.0}

        sentences = split_sentences(cleaned_text)
        if len(sentences) <= 1:
            res = self.synthesize(cleaned_text, fallback_on_error=True)
            ttfa = round(time.time() - start_time, 2)
            if on_first_audio_callback:
                try:
                    on_first_audio_callback(ttfa)
                except Exception:
                    pass
            if should_play and res["audio_path"] and res["audio_path"].exists():
                self.play(res["audio_path"], block=block)
            return {
                "audio_path": res["audio_path"],
                "cleaned_text": cleaned_text,
                "ttfa_sec": ttfa,
                "total_sec": round(time.time() - start_time, 2),
                "is_fallback": res.get("is_fallback", False)
            }

        # Nếu có từ 2 câu trở lên: Áp dụng cơ chế Pipelined Audio Queue gối đầu
        import queue
        audio_queue = queue.Queue()
        stop_worker = threading.Event()
        self._streaming_stop_event = stop_worker

        try:
            # 1. Tổng hợp câu đầu tiên ngay lập tức
            first_sentence = sentences[0]
            first_res = self.synthesize(first_sentence, fallback_on_error=True)
            ttfa = round(time.time() - start_time, 2)
            if on_first_audio_callback:
                try:
                    on_first_audio_callback(ttfa)
                except Exception:
                    pass

            first_audio = first_res["audio_path"]
            is_fallback = first_res.get("is_fallback", False)

            # 2. Kiểm tra nếu câu đầu tiên hoàn toàn không tổng hợp được (mọi engine đều lỗi)
            if not first_audio or not first_audio.exists():
                fallback = self.get_fallback_audio()
                if should_play and fallback and fallback.exists():
                    print("[🛡️ CIRCUIT BREAKER] Kích hoạt âm báo cục bộ (Offline Fallback Chime) khi mọi engine TTS gián đoạn.")
                    self.play(fallback, block=block)
                return {
                    "audio_path": fallback,
                    "cleaned_text": cleaned_text,
                    "ttfa_sec": ttfa,
                    "total_sec": round(time.time() - start_time, 2),
                    "is_fallback": True
                }

            # 3. Khởi tạo luồng ngầm để tổng hợp các câu tiếp theo (gối đầu)
            # Khóa tính nhất quán giọng đọc (Voice Consistency Lock):
            # Nếu câu 1 đã chuyển mạch sang Local TTS (Piper) do mạng lỗi,
            # các câu tiếp theo trong lượt nói này sẽ dùng thẳng Local TTS để tránh phát xen kẽ 2 giọng!
            use_local_only_for_rest = is_fallback or (self.engine_mode == "local")

            def background_synthesizer():
                nonlocal use_local_only_for_rest
                for idx, s in enumerate(sentences[1:], 2):
                    if stop_worker.is_set():
                        break
                    try:
                        if use_local_only_for_rest:
                            s_res = self.local_engine.synthesize(s)
                        else:
                            s_res = self.synthesize(s, fallback_on_error=True)
                            if s_res.get("is_fallback", False):
                                use_local_only_for_rest = True
                        if s_res.get("audio_path") and Path(s_res["audio_path"]).exists():
                            audio_queue.put(Path(s_res["audio_path"]))
                    except Exception as e:
                        pass
                audio_queue.put(None)  # Sentinel báo hiệu kết thúc

            worker_thread = threading.Thread(target=background_synthesizer, daemon=True)
            worker_thread.start()

            # 4. Phát câu 1 ra loa ngay lập tức trong khi câu 2 đang tải ngầm (nếu bật phát âm thanh)
            if should_play and first_audio and first_audio.exists():
                self.play(first_audio, block=True)

            # 5. Lần lượt lấy các câu tiếp theo từ hàng đợi để phát liền mạch
            while True:
                if stop_worker.is_set():
                    break
                next_audio = audio_queue.get()
                if next_audio is None:
                    break
                if should_play and next_audio.exists() and not stop_worker.is_set():
                    self.play(next_audio, block=True)

            total_time = round(time.time() - start_time, 2)
            return {
                "audio_path": first_audio,
                "cleaned_text": cleaned_text,
                "ttfa_sec": ttfa,
                "total_sec": total_time,
                "is_fallback": False
            }
        finally:
            stop_worker.set()
            if self._streaming_stop_event is stop_worker:
                self._streaming_stop_event = None


if __name__ == "__main__":
    tts = TextToSpeech()
    test_phrase = "Xin chào Quý công dân. Tôi là trợ lý AI hỗ trợ dịch vụ hành chính công."
    print("=" * 60)
    print(f"[*] Thử nghiệm giọng nói ({tts.voice}): \"{test_phrase}\"")
    tts.speak(test_phrase, block=True)
    print("[SUCCESS] Đã phát xong ra loa.")
    print("=" * 60)
