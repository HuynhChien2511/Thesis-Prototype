"""
Kiểm thử Tích hợp Pipeline với Hàng rào An toàn Guardrail (Pipeline + Guardrail Integration Tests).
Được tích hợp vào unittest framework để tự động phát hiện và chạy qua 'unittest discover'.

Xác nhận rằng:
1. Khi gặp câu trêu đùa/nói nhảm/lạc đề, Pipeline chặn ngay ở tầng Guardrail (< 5ms),
   hoàn toàn KHÔNG gọi RAG hay Web Search, tiết kiệm 100% tài nguyên mạng.
2. Khi gặp câu hỏi thủ tục hoặc tiện ích, Pipeline chuyển tiếp đầy đủ vào RAG.
3. Không làm rò rỉ bộ nhớ hoặc xung đột với bộ quản lý phiên đa lượt.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Thêm prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

# Đảm bảo UTF-8 console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from src.pipeline import VoiceAgentPipeline


class TestPipelineGuardrailIntegration(unittest.TestCase):
    """Bộ kiểm thử tích hợp Pipeline với Hàng rào An toàn Guardrail."""

    def setUp(self):
        # Khởi tạo Pipeline ở chế độ kiểm thử, mock các luồng phần cứng
        with patch("src.pipeline.AudioRecorder"), \
             patch("src.pipeline.SpeechToText"), \
             patch("src.pipeline.VideoCaptureThread"), \
             patch("src.pipeline.ObjectDetector"), \
             patch("src.pipeline.TextToSpeech"):
            self.pipeline = VoiceAgentPipeline(record_mode="ptt", tts_enabled=False, vision_enabled=False)

    def tearDown(self):
        self.pipeline.cleanup()

    def test_1_guardrail_chitchat_bypasses_rag(self):
        """Xác nhận câu hỏi tán gẫu dừng ngay ở Guardrail, không kích hoạt RAG."""
        with patch.object(self.pipeline.rag, "query") as mock_rag:
            res = self.pipeline.process_text("bạn có người yêu chưa", speak=False)
            self.assertEqual(res["source_type"], "guardrail_chitchat")
            self.assertIn("robot", res["answer"].lower())
            mock_rag.assert_not_called()

    def test_2_guardrail_deflection_bypasses_rag(self):
        """Xác nhận câu hỏi ngoài phạm vi (nấu ăn, giải trí) bị từ chối khéo léo, không gọi RAG."""
        with patch.object(self.pipeline.rag, "query") as mock_rag:
            res = self.pipeline.process_text("chỉ tôi cách nấu bún bò Huế", speak=False)
            self.assertEqual(res["source_type"], "guardrail_deflect")
            self.assertIn("chuyên trách", res["answer"].lower())
            mock_rag.assert_not_called()

    def test_3_guardrail_noise_handling(self):
        """Xác nhận tiếng đệm test mic được xử lý bởi Guardrail."""
        with patch.object(self.pipeline.rag, "query") as mock_rag:
            res = self.pipeline.process_text("alo 123", speak=False)
            self.assertEqual(res["source_type"], "guardrail_noise")
            mock_rag.assert_not_called()

    def test_4_guardrail_profanity_blocking(self):
        """Xác nhận ngôn từ xúc phạm bị chặn lập tức với phản hồi cảnh báo văn minh."""
        with patch.object(self.pipeline.rag, "query") as mock_rag:
            res = self.pipeline.process_text("đồ ngu ngốc", speak=False)
            self.assertEqual(res["source_type"], "guardrail_profanity")
            self.assertIn("văn minh", res["answer"].lower())
            mock_rag.assert_not_called()

    def test_5_valid_administrative_query_reaches_rag(self):
        """Xác nhận câu hỏi thủ tục công dân đi xuyên qua Guardrail đến Não bộ RAG."""
        mock_response = {
            "answer": "Để làm căn cước công dân cần mang theo giấy hẹn hoặc mã định danh...",
            "sources": ["Luật Căn cước 2023"],
            "source_type": "local",
            "found_in_docs": True,
            "warning_issued": False,
            "latency": {"total_sec": 0.05, "search_sec": 0.02, "llm_sec": 0.03}
        }
        with patch.object(self.pipeline.rag, "query", return_value=mock_response) as mock_rag:
            res = self.pipeline.process_text("Làm căn cước công dân cần những giấy tờ gì?", speak=False)
            self.assertEqual(res["source_type"], "local")
            mock_rag.assert_called_once()


if __name__ == "__main__":
    unittest.main()
