"""
Module thu âm từ Microphone (Sprint 2 - Đôi tai).
Hỗ trợ:
- Chuẩn hóa biên độ âm lượng (Peak Normalization & Auto-Gain)
- Chèn đệm chống nuốt chữ (Audio Padding 0.3s)
- Tự động ghi đè lưu file cuối cùng (data/last_recording.wav) để kiểm tra mic
- Hai chế độ: Push-to-Talk (Nhấn phím Enter) và VAD (Tự động ngắt theo khoảng lặng).
"""
import sys
import time
from pathlib import Path
from typing import Optional

# Thêm thư mục prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

import numpy as np
import sounddevice as sd
import wave

from src.config import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, DATA_DIR

LAST_RECORDING_PATH = DATA_DIR / "last_recording.wav"

# Đảm bảo UTF-8 console trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


class AudioRecorder:
    def __init__(self, sample_rate: int = AUDIO_SAMPLE_RATE, channels: int = AUDIO_CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels

    def post_process_audio(self, raw_audio: np.ndarray, save_last: bool = True) -> np.ndarray:
        """
        Tiền xử lý âm thanh trước khi đưa vào Whisper:
        1. Đo âm lượng gốc
        2. Tự động khuếch đại (Peak Normalization) lên mức 0.95
        3. Chèn 0.3s đệm ở đầu và đuôi (Audio Padding) chống nuốt chữ
        4. Ghi đè file last_recording.wav để người dùng nghe lại
        """
        if len(raw_audio) == 0:
            return raw_audio

        peak = float(np.max(np.abs(raw_audio)))
        
        # 1. Khuếch đại âm lượng nếu có tiếng nói (giới hạn trần x8 để tránh bùng nổ nhiễu)
        MIN_PEAK_THRESHOLD = 0.01
        MAX_GAIN_FACTOR = 8.0

        if peak >= MIN_PEAK_THRESHOLD:
            gain_factor = min(0.95 / peak, MAX_GAIN_FACTOR)
            normalized_audio = raw_audio * gain_factor
            target_peak = peak * gain_factor
            print(f"[*] Âm lượng mic gốc: {peak*100:.1f}% -> Đã khuếch đại lên {target_peak*100:.1f}% (x{gain_factor:.1f})")
        else:
            print("[⚠️ CẢNH BÁO] Âm thanh thu được quá nhỏ hoặc micro không bắt được tiếng.")
            normalized_audio = raw_audio

        # 2. Chèn đệm 0.3s (4800 samples tại 16kHz) ở đầu và cuối chống nuốt chữ
        pad_samples = int(self.sample_rate * 0.3)
        padding = np.zeros(pad_samples, dtype=np.float32)
        padded_audio = np.concatenate([padding, normalized_audio, padding])

        # 3. Ghi đè file duy nhất last_recording.wav để debug
        if save_last:
            self.save_wav(padded_audio, LAST_RECORDING_PATH)

        return padded_audio

    def record_push_to_talk(self) -> np.ndarray:
        """
        Chế độ Push-to-Talk:
        - Nhấn [Enter] để bắt đầu thu âm
        - Nói câu hỏi
        - Nhấn [Enter] để kết thúc thu âm
        """
        input("\n[🎤] Nhấn [Enter] để BẮT ĐẦU thu âm...")
        print("[🔴 ĐANG THU ÂM...] Hãy nói câu hỏi của bạn. Nhấn [Enter] để DỪNG:")

        frames = []
        is_recording = True

        def audio_callback(indata, frame_count, time_info, status):
            if is_recording:
                frames.append(indata.copy())

        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=audio_callback
        )

        with stream:
            input()
            is_recording = False

        print("[⏹️ KẾT THÚC THU ÂM] Đang xử lý âm thanh...")
        
        if not frames:
            return np.array([], dtype=np.float32)

        raw_audio = np.concatenate(frames, axis=0).flatten()
        return self.post_process_audio(raw_audio, save_last=True)

    def record_vad(
        self,
        silence_duration: float = 1.8,
        energy_threshold: float = 0.015,
        max_duration: float = 25.0,
        initial_silence_timeout: float = 5.0
    ) -> np.ndarray:
        """
        Chế độ VAD (Tự động phát hiện giọng nói & ngắt sau khoảng lặng):
        - Tự động nhận diện khi người dùng cất lời
        - Tự động ngắt sau silence_duration (mặc định 1.8 giây)
        - Ngắt sớm nếu sau initial_silence_timeout (5.0s) không phát hiện giọng nói
        """
        print(f"\n[🎙️ VAD CHỜ NÓI] Đang lắng nghe... (Hãy nói vào micro)")

        chunk_size = int(self.sample_rate * 0.1)  # 100ms mỗi chunk
        frames = []
        has_started_speaking = False
        silence_start_time = None
        start_time = time.time()

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype="float32") as stream:
            while True:
                chunk, _ = stream.read(chunk_size)
                energy = float(np.sqrt(np.mean(chunk**2)))  # RMS Energy
                current_time = time.time()

                if not has_started_speaking:
                    # Nếu quá 5s mà không ai nói, dừng lắng nghe tránh treo máy và tránh thu nhiễu
                    if current_time - start_time >= initial_silence_timeout:
                        print(f"[⏱️ HẾT THỜI GIAN CHỜ] Không phát hiện tiếng nói sau {initial_silence_timeout}s. Dừng thu âm.")
                        return np.array([], dtype=np.float32)

                    if energy > energy_threshold:
                        has_started_speaking = True
                        print("[🔴 ĐÃ NHẬN DIỆN TIẾNG NÓI] Đang thu âm...")
                        frames.append(chunk.copy())
                    else:
                        frames.append(chunk.copy())
                        if len(frames) > 6:  # Giữ đệm 0.6s trước khi nói
                            frames.pop(0)
                else:
                    frames.append(chunk.copy())
                    if energy < energy_threshold:
                        if silence_start_time is None:
                            silence_start_time = current_time
                        elif current_time - silence_start_time >= silence_duration:
                            print(f"[⏹️ PHÁT HIỆN KHOẢNG LẶNG {silence_duration}s] Tự động dừng.")
                            break
                    else:
                        silence_start_time = None

                if current_time - start_time >= max_duration:
                    print(f"[⚠️ ĐẠT GIỚI HẠN {max_duration}s] Dừng thu âm.")
                    break

        if not frames:
            return np.array([], dtype=np.float32)

        raw_audio = np.concatenate(frames, axis=0).flatten()
        return self.post_process_audio(raw_audio, save_last=True)

    def save_wav(self, audio_data: np.ndarray, file_path: Path):
        """Lưu mảng numpy float32 thành file WAV 16-bit PCM."""
        audio_int16 = (audio_data * 32767).clip(-32768, 32767).astype(np.int16)
        with wave.open(str(file_path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
        print(f"[💾 ĐÃ LƯU FILE CUỐI] {file_path.name} (Bạn có thể mở nghe lại để kiểm tra mic)")


if __name__ == "__main__":
    rec = AudioRecorder()
    data = rec.record_push_to_talk()
    print(f"Tổng số mẫu sau chuẩn hóa: {len(data)} (~{len(data)/rec.sample_rate:.2f}s)")
