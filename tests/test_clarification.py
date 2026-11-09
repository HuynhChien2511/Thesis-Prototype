"""
Bộ kiểm thử Tự động cho Giai đoạn 2: Phát hiện Mơ hồ & Hỏi lại Làm rõ (AmbiguityDetector).
Kiểm tra:
  1. Phát hiện câu hỏi thiếu thực thể thủ tục ("Làm cái này bao nhiêu tiền?").
  2. Phát hiện câu hỏi thủ tục đa nghĩa ("Thủ tục cấp đổi").
  3. Câu hỏi rõ ràng ("Làm thẻ căn cước") được cho qua ngay, không hỏi lại.
  4. Ngữ cảnh đã ghim trong SessionState miễn trừ việc hỏi lại cho các câu tiếp nối.
  5. Tái cấu trúc truy vấn hoàn chỉnh (Query Reconstruction) sau khi người dùng làm rõ.
  6. Phân tích độ phân tán vector (Vector Entropy Check).
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.rag.dialogue_manager import DialogueSession
from src.rag.ambiguity_detector import AmbiguityDetector, AmbiguityResult


class TestAmbiguityClarification(unittest.TestCase):

    def setUp(self):
        self.detector = AmbiguityDetector()
        self.session = DialogueSession(track_id=1)

    def test_1_detect_missing_procedure_fee(self):
        """Kiểm tra nhận diện câu hỏi chi phí chung chung không rõ thủ tục."""
        query = "Làm cái này bao nhiêu tiền?"
        res = self.detector.fast_rule_check(query, self.session)
        self.assertTrue(res.is_ambiguous)
        self.assertEqual(res.ambiguity_type, "missing_procedure")
        self.assertIn("procedure_name", res.missing_slots)
        self.assertIsNotNone(res.clarification_prompt)
        self.assertIn("Thẻ Căn cước", res.suggested_options)
        self.assertLessEqual(len(res.suggested_options), 3, "Chỉ gợi ý tối đa 3 lựa chọn theo Voice UI!")

    def test_2_detect_polysemous_procedure(self):
        """Kiểm tra nhận diện câu hỏi thủ tục cấp đổi chung chung."""
        query = "Thủ tục cấp đổi cần những gì?"
        res = self.detector.fast_rule_check(query, self.session)
        self.assertTrue(res.is_ambiguous)
        self.assertEqual(res.ambiguity_type, "polysemous")
        self.assertIn("Thẻ Căn cước", res.suggested_options)
        self.assertIn("Giấy phép lái xe", res.suggested_options)

    def test_3_clear_procedure_not_ambiguous(self):
        """Kiểm tra câu hỏi đã có tên thủ tục rõ ràng thì không bị chặn hỏi lại."""
        query = "Làm thẻ căn cước cho trẻ dưới 14 tuổi cần những giấy tờ gì?"
        res = self.detector.fast_rule_check(query, self.session)
        self.assertFalse(res.is_ambiguous, "Câu hỏi đầy đủ không được coi là mơ hồ!")
        self.assertEqual(self.session.slots.procedure_name, "Thẻ Căn cước")

    def test_4_session_context_exempts_ambiguity(self):
        """Kiểm tra nếu SessionState đã ghim thủ tục trước đó thì câu hỏi ngắn sau đó KHÔNG bị hỏi lại."""
        # Lượt 1: Đã xác định thủ tục Căn cước
        self.session.update_slots(procedure_name="Thẻ Căn cước")

        # Lượt 2: Người dân hỏi cộc lốc: "Hết bao nhiêu tiền?"
        query_2 = "Hết bao nhiêu tiền?"
        res = self.detector.fast_rule_check(query_2, self.session)
        
        # Vì đã có ngữ cảnh Căn cước ghim sẵn, câu này KHÔNG được coi là mơ hồ
        self.assertFalse(res.is_ambiguous, "Ngữ cảnh đã ghim phải miễn trừ việc hỏi lại!")

    def test_5_query_reconstruction(self):
        """Kiểm tra ghép câu hỏi gốc với câu trả lời làm rõ thành truy vấn RAG hoàn chỉnh."""
        original_q = "Làm cái này hết bao nhiêu tiền?"
        clarification_ans = "Căn cước công dân"

        reconstructed = self.detector.reconstruct_query(
            original_raw_query=original_q,
            clarification_answer=clarification_ans,
            session=self.session
        )

        self.assertIn("Thẻ Căn cước", reconstructed)
        self.assertIn("Lệ phí", reconstructed)
        self.assertEqual(self.session.slots.procedure_name, "Thẻ Căn cước")

    def test_6_vector_entropy_check(self):
        """Kiểm tra Lớp 2: Khi điểm vector phân tán sàn sàn nhau giữa nhiều tệp luật."""
        query = "Thời hạn giải quyết là mấy ngày?"
        
        # Giả lập 2 doc từ 2 file khác nhau có điểm sàn sàn nhau
        doc1 = MagicMock()
        doc1.metadata = {"source": "data/thu_tuc_cap_the_can_cuoc.txt"}
        doc2 = MagicMock()
        doc2.metadata = {"source": "data/thu_tuc_dang_ky_tam_tru.txt"}
        
        docs_with_scores = [(doc1, 0.48), (doc2, 0.46)]

        res = self.detector.vector_entropy_check(query, docs_with_scores, self.session)
        self.assertTrue(res.is_ambiguous)
        self.assertEqual(res.ambiguity_type, "polysemous")
        self.assertIn("Thẻ Căn cước", res.suggested_options)
        self.assertIn("Đăng ký Tạm trú", res.suggested_options)


if __name__ == "__main__":
    unittest.main()
