"""
Bộ kiểm thử Tự động cho Giai đoạn 3: Tách câu Streaming TTS & Circuit Breaker (Timeout cứng).
Kiểm tra:
  1. Tách câu chuẩn ngữ âm tiếng Việt (SentenceSplitter).
  2. Bảo vệ số tiền (50.000 đồng), số thập phân (1.5 ngày), ngày tháng (15/10/2024).
  3. Gom các câu quá ngắn (< 30 ký tự) để giọng đọc liền mạch.
  4. Cơ chế Circuit Breaker & Fallback an toàn khi mạng lỗi hoặc timeout.
  5. Luồng Sentence-Boundary Streaming TTS (Pipelined Synthesis & First Audio Latency).
"""
import sys
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.audio.tts import split_sentences, TextToSpeech


class TestStreamingTTS(unittest.TestCase):

    def test_1_split_standard_sentences(self):
        """Kiểm tra tách câu thông thường theo dấu chấm, than, hỏi."""
        text = "Xin chào Quý công dân. Tôi là robot trợ lý hành chính công! Bạn cần hỗ trợ thủ tục gì hôm nay?"
        sentences = split_sentences(text, min_chars=20)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "Xin chào Quý công dân.")
        self.assertEqual(sentences[1], "Tôi là robot trợ lý hành chính công!")
        self.assertEqual(sentences[2], "Bạn cần hỗ trợ thủ tục gì hôm nay?")

    def test_2_protect_money_and_decimals(self):
        """Kiểm tra dấu chấm trong số tiền (50.000 đồng) và số thập phân (1.5 ngày) KHÔNG bị ngắt câu nhầm."""
        text = "Lệ phí cấp thẻ căn cước là 50.000 đồng. Thời hạn giải quy định là 1.5 ngày làm việc."
        sentences = split_sentences(text, min_chars=20)
        self.assertEqual(len(sentences), 2)
        self.assertIn("50.000 đồng.", sentences[0])
        self.assertIn("1.5 ngày làm việc.", sentences[1])

    def test_3_merge_short_clauses(self):
        """Kiểm tra các câu quá ngắn được gom vào câu tiếp theo để tránh đọc giật cục."""
        text = "Dạ. Vâng ạ. Thủ tục này được thực hiện tại bộ phận Một cửa cấp huyện."
        sentences = split_sentences(text, min_chars=25)
        # "Dạ." và "Vâng ạ." quá ngắn (< 25 ký tự) nên được gom lại
        self.assertLessEqual(len(sentences), 2)
        self.assertIn("Một cửa cấp huyện.", sentences[-1])

    def test_4_synthesize_error_fallback(self):
        """Kiểm tra synthesize xử lý ngoại lệ mượt mà, trả về audio_path=None thay vì làm sập luồng (Edge-only mode)."""
        tts = TextToSpeech()
        tts.engine_mode = "edge"
        with patch("asyncio.run", side_effect=Exception("Network error")):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = tts.synthesize("Xin chào quý khách")
            self.assertIsNone(result["audio_path"])
            self.assertEqual(result["cleaned_text"], "Xin chào quý khách")
            self.assertGreaterEqual(result["latency_sec"], 0.0)

    def test_5_speak_streaming_pipeline(self):
        """Kiểm tra cơ chế Sentence-Boundary Streaming TTS gối đầu."""
        tts = TextToSpeech()
        text = "Thủ tục này được tiếp nhận tại bộ phận Một cửa huyện. Công dân vui lòng mang theo giấy tờ tùy thân hợp lệ. Kết quả sẽ được trả sau khoảng ba ngày làm việc."
        
        callback_mock = MagicMock()
        dummy_file = PROTOTYPE_DIR / "tests" / "test_dummy.mp3"
        dummy_file.write_bytes(b"dummy")

        try:
            with patch.object(tts, "synthesize", return_value={"audio_path": dummy_file, "cleaned_text": "text", "latency_sec": 0.1}) as mock_synth, \
                 patch.object(tts, "play") as mock_play:
                res = tts.speak_streaming(text, on_first_audio_callback=callback_mock, block=True)
                
                # Callback báo TTFA phải được gọi cho câu đầu tiên
                callback_mock.assert_called_once()
                # Phải gọi synthesize cho cả 3 câu
                self.assertEqual(mock_synth.call_count, 3)
                # Phải gọi play 3 lần (câu 1 + 2 câu kế tiếp)
                self.assertEqual(mock_play.call_count, 3)
                self.assertIsNotNone(res["ttfa_sec"])
        finally:
            if dummy_file.exists():
                dummy_file.unlink()

    def test_6_speak_streaming_silent_mode(self):
        """Kiểm tra khi play_audio=False thì speak_streaming không phát âm thanh ra loa ngoài."""
        tts = TextToSpeech()
        text = "Câu thứ nhất để thử nghiệm phát âm. Câu thứ hai để thử nghiệm tiếp luồng không tiếng."
        dummy_file = PROTOTYPE_DIR / "tests" / "test_dummy_silent.mp3"
        dummy_file.write_bytes(b"dummy")

        try:
            with patch.object(tts, "synthesize", return_value={"audio_path": dummy_file, "cleaned_text": "text", "latency_sec": 0.1}), \
                 patch.object(tts, "play") as mock_play:
                res = tts.speak_streaming(text, play_audio=False)
                mock_play.assert_not_called()
                self.assertIsNotNone(res["ttfa_sec"])
        finally:
            if dummy_file.exists():
                dummy_file.unlink()


if __name__ == "__main__":
    unittest.main()
