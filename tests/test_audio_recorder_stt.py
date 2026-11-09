"""
Kiểm thử Unit Test cho Phân hệ Âm thanh: Microphone Recorder & Faster-Whisper STT (8 bài test).
Bao gồm:
  1. Chuẩn hóa biên độ âm lượng Peak Normalization & Auto-Gain.
  2. Bảo vệ chống bùng nổ nhiễu khi âm thanh quá nhỏ (dưới MIN_PEAK_THRESHOLD).
  3. Chèn đệm an toàn chống nuốt chữ Audio Padding (0.3s tại 16kHz).
  4. Xử lý an toàn mảng âm thanh rỗng.
  5. Xử lý đầu vào rỗng trong SpeechToText.transcribe().
  6. Áp đặt ngôn ngữ tiếng Việt (language='vi') trong Faster-Whisper.
  7. Nhúng từ vựng chuyên ngành hành chính công vào Initial Prompt.
  8. Chuẩn hóa chữ hoa đầu câu và làm sạch dấu chấm lửng thừa.
"""
import sys
import unittest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.audio.recorder import AudioRecorder
from src.audio.stt import SpeechToText


class TestAudioRecorderAndSTT(unittest.TestCase):
    """Bộ kiểm thử phân hệ Thu âm và Nhận dạng Giọng nói."""

    def setUp(self):
        self.recorder = AudioRecorder(sample_rate=16000, channels=1)

    def test_1_audio_peak_normalization_and_autogain(self):
        """1. Kiểm tra Peak Normalization khuếch đại tín hiệu nhỏ về mức chuẩn 0.95."""
        # Tạo tín hiệu có đỉnh biên độ 0.2 (nằm trong ngưỡng khuếch đại trần x8)
        raw_audio = np.array([0.1, -0.2, 0.15, -0.05], dtype=np.float32)
        padded_audio = self.recorder.post_process_audio(raw_audio, save_last=False)

        # Biên độ đỉnh sau khuếch đại phải đạt chuẩn 0.95
        max_peak = float(np.max(np.abs(padded_audio)))
        self.assertAlmostEqual(max_peak, 0.95, delta=0.01)

    def test_2_audio_silence_protection_below_threshold(self):
        """2. Kiểm tra tín hiệu cực nhỏ (<0.01) không bị khuếch đại quá đà gây nổ nhiễu nền."""
        # Tín hiệu nhiễu cực nhỏ peak = 0.005 (< MIN_PEAK_THRESHOLD 0.01)
        raw_noise = np.array([0.002, -0.005, 0.003], dtype=np.float32)
        processed = self.recorder.post_process_audio(raw_noise, save_last=False)

        # Biên độ không bị thổi phồng lên 0.95 mà giữ nguyên
        max_peak = float(np.max(np.abs(processed)))
        self.assertLess(max_peak, 0.01)

    def test_3_audio_padding_prevents_clipping(self):
        """3. Kiểm tra chèn 0.3s (4800 mẫu tại 16kHz) đệm ở đầu và đuôi chống nuốt từ."""
        raw_audio = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        processed = self.recorder.post_process_audio(raw_audio, save_last=False)

        expected_padding_samples = int(16000 * 0.3)  # 4800 mẫu
        expected_total_len = len(raw_audio) + 2 * expected_padding_samples
        self.assertEqual(len(processed), expected_total_len)
        # Các mẫu ở đầu và đuôi phải là 0
        self.assertEqual(processed[0], 0.0)
        self.assertEqual(processed[-1], 0.0)

    def test_4_empty_audio_array_handling(self):
        """4. Kiểm tra xử lý an toàn mảng âm thanh rỗng không gây crash."""
        empty_audio = np.array([], dtype=np.float32)
        processed = self.recorder.post_process_audio(empty_audio, save_last=False)
        self.assertEqual(len(processed), 0)

    def test_5_stt_transcribe_empty_audio_returns_empty(self):
        """5. Kiểm tra STT nhận diện mảng rỗng trả về kết quả rỗng tức thì (0.0s)."""
        with patch.object(SpeechToText, "_load_model"):
            stt = SpeechToText()
            stt.model = MagicMock()
            res = stt.transcribe(np.array([], dtype=np.float32))

            self.assertEqual(res["text"], "")
            self.assertEqual(res["duration_sec"], 0.0)
            self.assertEqual(res["latency_sec"], 0.0)
            stt.model.transcribe.assert_not_called()

    def test_6_stt_vietnamese_language_enforcement(self):
        """6. Kiểm tra Faster-Whisper được cấu hình cố định tiếng Việt (language='vi')."""
        with patch.object(SpeechToText, "_load_model"):
            stt = SpeechToText()
            mock_segment = MagicMock()
            mock_segment.text = "làm căn cước công dân"
            stt.model = MagicMock()
            stt.model.transcribe.return_value = ([mock_segment], MagicMock(duration=1.5))

            dummy_audio = np.ones(16000, dtype=np.float32) * 0.5
            res = stt.transcribe(dummy_audio)

            # Khẳng định tham số language='vi' được truyền vào mô hình
            _, kwargs = stt.model.transcribe.call_args
            self.assertEqual(kwargs.get("language"), "vi")
            self.assertEqual(kwargs.get("task"), "transcribe")
            self.assertIn("Làm căn cước", res["text"])

    def test_7_stt_admin_initial_prompt_injection(self):
        """7. Kiểm tra từ khóa hành chính công được truyền vào initial_prompt của Whisper."""
        with patch.object(SpeechToText, "_load_model"):
            stt = SpeechToText()
            stt.model = MagicMock()
            stt.model.transcribe.return_value = ([], MagicMock(duration=1.0))

            dummy_audio = np.ones(8000, dtype=np.float32) * 0.2
            stt.transcribe(dummy_audio)

            _, kwargs = stt.model.transcribe.call_args
            prompt = kwargs.get("initial_prompt", "")
            self.assertIn("căn cước", prompt)
            self.assertIn("VNeID", prompt)
            self.assertIn("UBND", prompt)

    def test_8_stt_capitalization_and_ellipsis_cleanup(self):
        """8. Kiểm tra văn bản sau giải mã được viết hoa chữ đầu và xóa dấu chấm lửng rác."""
        with patch.object(SpeechToText, "_load_model"):
            stt = SpeechToText()
            mock_segment = MagicMock()
            mock_segment.text = "hồ sơ đăng ký kết hôn..."
            stt.model = MagicMock()
            stt.model.transcribe.return_value = ([mock_segment], MagicMock(duration=2.0))

            dummy_audio = np.ones(16000, dtype=np.float32) * 0.3
            res = stt.transcribe(dummy_audio)

            # Chữ đầu 'h' phải thành 'H', dấu '...' phải bị tẩy sạch
            self.assertTrue(res["text"].startswith("H"))
            self.assertFalse(res["text"].endswith("..."))
            self.assertEqual(res["text"], "Hồ sơ đăng ký kết hôn")


if __name__ == "__main__":
    unittest.main()
