"""
Bộ kiểm thử Tích hợp Toàn trình Toàn bộ 4 Giai đoạn Hướng 2 (Direction 2 End-to-End Integration Tests).
Bao gồm:
  1. Giai đoạn 1: Quản lý phiên đàm thoại đa lượt (Multi-turn Session & Pinned Slots).
  2. Giai đoạn 2: Phát hiện mơ hồ (Ambiguity Detection) & Hỏi làm rõ (Rule of Three) & Tái thiết kế truy vấn (Query Reconstruction).
  3. Giai đoạn 3: Sentence-Boundary Streaming TTS (< 1.5s TTFA) & Tách câu mượt mà.
  4. Giai đoạn 4: Tích hợp hoàn chỉnh vào VoiceAgentPipeline, định danh Track ID và tự động dọn dẹp phiên.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.rag.dialogue_manager import DialogueSessionManager, SessionState
from src.rag.ambiguity_detector import AmbiguityDetector
from src.audio.tts import split_sentences
from src.pipeline import VoiceAgentPipeline
from src.vision.tracker import TrackedPerson
from src.vision.detector import DetectionResult


class TestDirection2Integration(unittest.TestCase):

    def setUp(self):
        # Khởi tạo Pipeline ở chế độ tắt âm thanh và không nạp mô hình nặng vào GPU để test nhanh
        with patch("src.pipeline.AudioRecorder"), \
             patch("src.pipeline.SpeechToText"), \
             patch("src.pipeline.VideoCaptureThread"), \
             patch("src.pipeline.ObjectDetector"), \
             patch("src.pipeline.TextToSpeech"):
            self.pipeline = VoiceAgentPipeline(record_mode="ptt", tts_enabled=False, vision_enabled=False)

    def tearDown(self):
        self.pipeline.cleanup()

    def test_1_ambiguity_detection_and_clarification_flow(self):
        """
        Kiểm tra luồng xử lý câu hỏi mơ hồ:
        Lượt 1: Công dân hỏi mơ hồ 'Làm cái này bao nhiêu tiền?' -> Robot phát hiện thiếu slot, hỏi làm rõ.
        Lượt 2: Công dân trả lời 'Thẻ Căn cước' -> Robot tái thiết kế truy vấn và trả lời chính xác.
        """
        track_id = 101

        # Lượt 1: Câu hỏi mơ hồ
        res1 = self.pipeline.process_text("Làm cái này bao nhiêu tiền?", speak=False, track_id=track_id)
        
        self.assertTrue(res1.get("is_clarification"))
        self.assertEqual(res1.get("source_type"), "clarification")
        self.assertIn("thẻ căn cước", res1["answer"].lower())
        self.assertGreaterEqual(len(res1.get("clarification_options", [])), 2)

        # Kiểm tra phiên đang ở trạng thái AWAITING_CLARIFICATION
        session = self.pipeline.dialogue_mgr.get_session(track_id)
        self.assertEqual(session.state, SessionState.AWAITING_CLARIFICATION)

        # Mock RAG response cho lượt 2
        mock_rag_res = {
            "question": "Lệ phí làm thủ tục Thẻ Căn cước hết bao nhiêu tiền?",
            "answer": "Theo quy định, cấp mới thẻ căn cước lần đầu được miễn lệ phí hoàn toàn.",
            "sources": ["Thông tư 73/2024/TT-BTC"],
            "found_in_docs": True,
            "source_type": "local",
            "warning_issued": False,
            "latency": {"retrieval_sec": 0.1, "web_search_sec": 0.0, "generation_sec": 0.5, "total_sec": 0.6}
        }

        with patch.object(self.pipeline.rag, "query", return_value=mock_rag_res):
            # Lượt 2: Công dân cung cấp câu trả lời làm rõ
            res2 = self.pipeline.process_text("Thẻ Căn cước", speak=False, track_id=track_id)

            self.assertFalse(res2.get("is_clarification", False))
            self.assertIn("căn cước", res2["effective_question"].lower())
            self.assertIn("lệ phí", res2["effective_question"].lower())
            self.assertEqual(res2["answer"], mock_rag_res["answer"])
            
            # Trạng thái phiên phải quay về NORMAL
            self.assertEqual(session.state, SessionState.NORMAL)
            self.assertIn("căn cước", session.slots.procedure_name.lower())

    def test_2_multiturn_anaphora_resolution(self):
        """
        Kiểm tra suy luận nối tiếp đa lượt:
        Lượt 1: Công dân hỏi về 'thủ tục đăng ký kết hôn'.
        Lượt 2: Công dân hỏi rút gọn 'Lệ phí bao nhiêu?' -> Hệ thống tự động làm giàu truy vấn thành 'kết hôn Lệ phí bao nhiêu?'.
        """
        track_id = 202
        session = self.pipeline.dialogue_mgr.get_session(track_id)

        # Giả lập lượt 1 đã hoàn thành và ghim thủ tục kết hôn
        session.slots.procedure_name = "đăng ký kết hôn"
        session.add_turn("Thủ tục đăng ký kết hôn cần gì?", "Cần chuẩn bị tờ khai đăng ký kết hôn và CCCD.", "local")

        mock_rag_res = {
            "question": "đăng ký kết hôn Lệ phí bao nhiêu?",
            "answer": "Miễn lệ phí đối với công dân đăng ký kết hôn tại UBND cấp xã nơi cư trú.",
            "sources": ["Thông tư 85/2019/TT-BTC"],
            "found_in_docs": True,
            "source_type": "local",
            "warning_issued": False,
            "latency": {"retrieval_sec": 0.08, "web_search_sec": 0.0, "generation_sec": 0.4, "total_sec": 0.48}
        }

        with patch.object(self.pipeline.rag, "query", return_value=mock_rag_res) as mock_query:
            res = self.pipeline.process_text("Lệ phí bao nhiêu?", speak=False, track_id=track_id)

            # Phải gọi rag.query với session đi kèm
            mock_query.assert_called_once()
            call_args = mock_query.call_args
            self.assertEqual(call_args[0][0], "Lệ phí bao nhiêu?")
            self.assertEqual(call_args[1]["session"], session)
            self.assertIn("kết hôn", session.slots.procedure_name)

    def test_3_person_track_id_isolation_and_departure_flush(self):
        """
        Kiểm tra cô lập bộ nhớ giữa 2 người khác nhau và tự động dọn dẹp khi người rời đi.
        """
        mgr = self.pipeline.dialogue_mgr

        # Người 1 (Track ID 1): Đang hỏi Căn cước
        s1 = mgr.get_session(1)
        s1.slots.procedure_name = "thẻ căn cước"
        s1.add_turn("Hỏi căn cước", "Đáp căn cước", "local")

        # Người 2 (Track ID 2): Đang hỏi Đất đai
        s2 = mgr.get_session(2)
        s2.slots.procedure_name = "sang tên sổ đỏ"
        s2.add_turn("Hỏi đất đai", "Đáp đất đai", "local")

        # Kiểm tra hoàn toàn độc lập
        self.assertEqual(mgr.get_session(1).slots.procedure_name, "thẻ căn cước")
        self.assertEqual(mgr.get_session(2).slots.procedure_name, "sang tên sổ đỏ")

        # Giả lập Người 1 rời đi (Camera chỉ còn thấy Track ID 2)
        flushed = mgr.flush_inactive_sessions(active_track_ids=[2])
        self.assertIn(1, flushed)
        self.assertNotIn(2, flushed)

        # Track 1 phải bị xóa khỏi bộ nhớ RAM
        self.assertNotIn(1, mgr.sessions)
        self.assertIn(2, mgr.sessions)

    def test_4_sentence_splitting_and_streaming_integration(self):
        """
        Kiểm tra tích hợp tách câu streaming TTS và bảo vệ định dạng.
        """
        text = "Lệ phí làm thẻ là 50.000 đồng theo quy định. Thời gian cấp lại là 1.5 ngày làm việc tại Một cửa."
        sentences = split_sentences(text, min_chars=20)
        self.assertEqual(len(sentences), 2)
        self.assertIn("50.000 đồng", sentences[0])
        self.assertIn("1.5 ngày", sentences[1])

    def test_5_auto_assign_nearest_person_area_ratio(self):
        """Kiểm tra pipeline tự động gán Track ID cho người đứng gần nhất (area_ratio lớn nhất) mà không crash."""
        p1 = TrackedPerson(track_id=10, bbox=[0, 0, 100, 100], area_ratio=0.15, confidence=0.9, last_seen_time=1.0)
        p2 = TrackedPerson(track_id=20, bbox=[0, 0, 200, 200], area_ratio=0.45, confidence=0.95, last_seen_time=1.0)
        
        self.pipeline.vision_mgr = MagicMock()
        self.pipeline.vision_mgr.latest_result = DetectionResult(
            annotated_frame=None,
            has_person=True,
            person_count=2,
            max_person_ratio=0.45,
            tracked_persons=[p1, p2]
        )

        # Gọi process_text không truyền track_id -> Phải tự gán active_track_id = 20
        res = self.pipeline.process_text("xin chào", speak=False)
        self.assertEqual(res["track_id"], 20)

    def test_6_layer2_vector_entropy_clarification_in_pipeline(self):
        """Kiểm tra Layer 2 Vector Entropy được kích hoạt trong pipeline khi truy vấn phân tán ngữ nghĩa."""
        mock_doc1 = MagicMock()
        mock_doc1.metadata = {"source": "data/thu_tuc_cap_the_can_cuoc.txt"}
        mock_doc2 = MagicMock()
        mock_doc2.metadata = {"source": "data/thu_tuc_dang_ky_tam_tru.txt"}
        
        # Mock ChromaDB similarity_search_with_relevance_scores trả về điểm sàn sàn nhau < 0.55
        with patch.object(self.pipeline.rag.vector_store, "similarity_search_with_relevance_scores", return_value=[(mock_doc1, 0.48), (mock_doc2, 0.46)]):
            res = self.pipeline.process_text("Thời hạn giải quyết là mấy ngày?", speak=False, track_id=303)
            self.assertTrue(res.get("is_clarification"))
            self.assertEqual(res.get("source_type"), "clarification")
            self.assertIn("Thẻ Căn cước", res["clarification_options"])
            self.assertIn("Đăng ký Tạm trú", res["clarification_options"])


if __name__ == "__main__":
    unittest.main()
