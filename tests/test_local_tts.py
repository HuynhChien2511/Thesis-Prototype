"""
Bộ Kiểm Thử Tự Động cho Phân Hệ Local Offline TTS & Hybrid Dual-Engine (Sprint 4 - Khắc phục phụ thuộc Internet)
Kiểm tra:
  1. Khởi tạo LocalTTSEngine và báo cáo trạng thái.
  2. Tổng hợp giọng nói cục bộ (WAV PCM).
  3. Xử lý chuỗi rỗng và chuẩn hóa văn bản.
  4. Chế độ thuần Offline `engine_mode='local'`.
  5. Cơ chế chuyển mạch Hybrid Dual-Engine khi Edge-TTS rớt mạng.
  6. Âm báo dự phòng `generate_offline_chime()`.
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.audio.local_tts import LocalTTSEngine, generate_offline_chime
from src.audio.tts import TextToSpeech


class TestLocalTTS(unittest.TestCase):
    def setUp(self):
        self.engine = LocalTTSEngine()
        self.tts = TextToSpeech(engine_mode="local")
        self.created_files = []

    def tearDown(self):
        for f in self.created_files:
            if f and Path(f).exists():
                try:
                    Path(f).unlink()
                except Exception:
                    pass

    def test_local_tts_initialization(self):
        """TC-L01: Kiểm tra khởi tạo LocalTTSEngine và thông tin trạng thái các engine."""
        status = self.engine.get_status()
        self.assertIn("piper_onnx", status)
        self.assertIn("windows_sapi", status)
        self.assertIsInstance(status["piper_onnx"]["available"], bool)
        self.assertIsInstance(status["windows_sapi"]["available"], bool)

    def test_local_tts_synthesize_speech(self):
        """TC-L02: Kiểm tra tổng hợp câu nói cục bộ không cần internet."""
        text = "Thủ tục cấp thẻ căn cước tại bộ phận Một cửa."
        out_file = PROTOTYPE_DIR / "data" / "test_unit_local.wav"
        self.created_files.append(out_file)

        res = self.engine.synthesize(text, output_path=out_file)
        self.assertIsNotNone(res["audio_path"])
        self.assertTrue(Path(res["audio_path"]).exists())
        self.assertGreater(Path(res["audio_path"]).stat().st_size, 500)
        self.assertIn(res["engine"], ["piper_onnx", "windows_sapi", "offline_chime"])

    def test_local_tts_empty_text(self):
        """TC-L03: Kiểm tra xử lý an toàn khi đầu vào rỗng."""
        res = self.engine.synthesize("   ")
        self.assertIsNone(res["audio_path"])
        self.assertEqual(res["cleaned_text"], "")
        self.assertEqual(res["engine"], "none")

    def test_text_to_speech_local_mode(self):
        """TC-L04: Kiểm tra TextToSpeech hoạt động ở chế độ thuần Offline."""
        out_file = PROTOTYPE_DIR / "data" / "test_unit_tts_local.wav"
        self.created_files.append(out_file)

        res = self.tts.synthesize("Xin chào công dân", output_path=out_file)
        self.assertIsNotNone(res["audio_path"])
        self.assertTrue(Path(res["audio_path"]).exists())

    def test_hybrid_auto_switch_on_edge_failure(self):
        """TC-L05: Kiểm tra cơ chế Hybrid tự động chuyển sang Local TTS khi Edge-TTS lỗi."""
        hybrid_tts = TextToSpeech(engine_mode="hybrid")
        out_file = PROTOTYPE_DIR / "data" / "test_unit_hybrid_fallback.wav"
        self.created_files.append(out_file)

        mock_local_res = {
            "audio_path": out_file,
            "cleaned_text": "Câu hỏi thử nghiệm chuyển mạch.",
            "latency_sec": 0.15,
            "engine": "piper_onnx"
        }
        # Tạo file giả lập để kiểm tra tồn tại
        out_file.write_bytes(b"RIFF" + b"\x00" * 1000)

        # Giả lập Edge-TTS rớt mạng hoàn toàn qua asyncio.run
        with patch("asyncio.run", side_effect=ConnectionResetError("Socket reset")), \
             patch.object(hybrid_tts.local_engine, "synthesize", return_value=mock_local_res):
            res = hybrid_tts.synthesize("Câu hỏi thử nghiệm chuyển mạch.", output_path=out_file, fallback_on_error=True)
            self.assertTrue(res.get("is_fallback", False))
            self.assertIsNotNone(res["audio_path"])
            self.assertEqual(res["engine"], "piper_onnx")

    def test_offline_chime_generation(self):
        """TC-L06: Kiểm tra tạo âm báo Chime 24kHz bằng thư viện chuẩn wave + math."""
        out_file = PROTOTYPE_DIR / "data" / "test_unit_chime.wav"
        self.created_files.append(out_file)

        chime_path = generate_offline_chime(out_file)
        self.assertTrue(chime_path.exists())
        self.assertGreater(chime_path.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
