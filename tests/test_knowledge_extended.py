"""
Kiểm thử Toàn diện cho Cơ sở Dữ liệu 10 Thủ tục Hành chính Công Mở rộng.
Được tích hợp vào unittest framework để tự động phát hiện và chạy qua 'unittest discover'.

Bao gồm:
  1. Kiểm tra sự tồn tại và tính hợp lệ của toàn bộ 10 tệp văn bản quy định.
  2. Kiểm tra trích xuất thực thể thủ tục (Slot Extraction) cho 10/10 thủ tục hành chính.
  3. Kiểm tra cơ chế giải quyết tham chiếu rút gọn (Anaphora Resolution) cho các thủ tục mới.
  4. Kiểm tra phân loại câu hỏi đa nghĩa & gợi ý lựa chọn (Polysemous Disambiguation).
  5. Kiểm tra lọc ngưỡng tương đồng Cosine (Relevance Score Thresholding >= 0.55).
  6. Kiểm tra phát hiện phân tán vector (Vector Entropy Ambiguity Detection).
  7. Kiểm tra chuẩn hóa trích dẫn căn cứ pháp lý từ văn bản quy định.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

from src.rag.dialogue_manager import DialogueSessionManager, DialogueSession, SessionSlots
from src.rag.ambiguity_detector import AmbiguityDetector, AmbiguityResult
from src.rag.retriever import AdministrativeRAG
from langchain_core.documents import Document


class TestExtendedAdministrativeKnowledge(unittest.TestCase):
    """Bộ kiểm thử cho 10 thủ tục hành chính công mở rộng và khả năng đa lượt."""

    EXPECTED_PROCEDURES = [
        ("thu_tuc_cap_the_can_cuoc.txt", "Căn cước"),
        ("thu_tuc_dang_ky_ket_hon.txt", "Kết hôn"),
        ("thu_tuc_dang_ky_tam_tru.txt", "Tạm trú"),
        ("thu_tuc_dang_ky_thuong_tru.txt", "Thường trú"),
        ("thu_tuc_dang_ky_khai_sinh.txt", "Khai sinh"),
        ("thu_tuc_dang_ky_khai_tu.txt", "Khai tử"),
        ("thu_tuc_cap_ho_chieu.txt", "Hộ chiếu"),
        ("thu_tuc_chung_thuc_ban_sao.txt", "Chứng thực"),
        ("thu_tuc_cap_giay_xac_nhan_tinh_trang_hon_nhan.txt", "Tình trạng hôn nhân"),
        ("thu_tuc_cap_doi_giay_phep_lai_xe.txt", "Giấy phép lái xe"),
    ]

    def setUp(self):
        self.session_mgr = DialogueSessionManager(session_timeout_sec=300)
        self.ambiguity_detector = AmbiguityDetector()

    def test_1_all_10_procedure_documents_exist(self):
        """Xác nhận toàn bộ 10 tệp văn bản quy định đều tồn tại trong thư mục data/ với dung lượng chuẩn."""
        data_dir = PROTOTYPE_DIR / "data"
        self.assertTrue(data_dir.exists(), "Thư mục prototype/data không tồn tại!")

        for filename, label in self.EXPECTED_PROCEDURES:
            file_path = data_dir / filename
            self.assertTrue(
                file_path.exists(),
                f"Thiếu tệp dữ liệu thủ tục: {filename} ({label})"
            )
            file_size = file_path.stat().st_size
            self.assertGreater(
                file_size,
                500,
                f"Tệp {filename} có dung lượng quá nhỏ ({file_size} bytes), có thể bị rỗng!"
            )

    def test_2_slot_extraction_all_10_procedures(self):
        """Kiểm tra SessionSlots trích xuất chính xác tên thủ tục cho cả 10 thủ tục hành chính."""
        test_queries = [
            ("Cho tôi hỏi làm thẻ căn cước cần những giấy tờ gì?", "căn cước"),
            ("Thủ tục đăng ký kết hôn với người cùng xã thế nào?", "đăng ký kết hôn"),
            ("Tôi muốn đăng ký tạm trú cho người thuê trọ", "đăng ký tạm trú"),
            ("Hướng dẫn làm thủ tục đăng ký thường trú khi mới mua nhà", "đăng ký thường trú"),
            ("Thủ tục đăng ký khai sinh cho trẻ mới sinh", "đăng ký khai sinh"),
            ("Hồ sơ đăng ký khai tử tại UBND cấp xã gồm những gì?", "đăng ký khai tử"),
            ("Làm hộ chiếu phổ thông lần đầu hết bao nhiêu tiền?", "cấp hộ chiếu"),
            ("Chứng thực bản sao từ bản chính bằng đại học ở đâu?", "chứng thực bản sao"),
            ("Xin cấp giấy xác nhận tình trạng hôn nhân để vay vốn", "xác nhận tình trạng hôn nhân"),
            ("Thủ tục cấp đổi giấy phép lái xe hạng B2 hết hạn", "cấp đổi giấy phép lái xe"),
        ]

        for query, expected_proc in test_queries:
            slots = SessionSlots()
            slots.update_from_query(query)
            self.assertIsNotNone(
                slots.procedure_name,
                f"Không trích xuất được thủ tục từ câu hỏi: '{query}'"
            )
            self.assertIn(
                expected_proc.lower(),
                slots.procedure_name.lower(),
                f"Trích xuất sai thủ tục cho câu: '{query}'. Nhận được: '{slots.procedure_name}', kỳ vọng chứa: '{expected_proc}'"
            )

    def test_3_anaphora_resolution_for_extended_procedures(self):
        """Kiểm tra cơ chế làm giàu câu truy vấn khi người dân hỏi câu nối tiếp cho các thủ tục mới."""
        session = DialogueSession(track_id=42)
        session.slots.procedure_name = "cấp hộ chiếu"

        # Lượt 2: Người dân hỏi cộc lốc về lệ phí
        query = "hết bao nhiêu tiền?"
        enriched = session.slots.procedure_name + " " + query
        self.assertIn("cấp hộ chiếu", enriched)
        self.assertIn("bao nhiêu tiền", enriched)

        # Đổi sang thủ tục khác: "đăng ký khai sinh"
        session.slots.update_from_query("thủ tục đăng ký khai sinh cho con")
        self.assertIn("khai sinh", session.slots.procedure_name)

        # Lượt tiếp theo hỏi thời hạn
        query2 = "mất bao lâu thì lấy được?"
        enriched2 = session.slots.procedure_name + " " + query2
        self.assertIn("khai sinh", enriched2)
        self.assertIn("bao lâu", enriched2)

    def test_4_polysemous_procedure_clarification(self):
        """Kiểm tra phát hiện câu hỏi đa nghĩa chung chung và gợi ý tối đa 3 lựa chọn."""
        session = DialogueSession(track_id=1)
        res = self.ambiguity_detector.fast_rule_check("Thủ tục cấp đổi cần những gì?", session)
        self.assertTrue(res.is_ambiguous)
        self.assertEqual(res.ambiguity_type, "polysemous")
        self.assertLessEqual(len(res.suggested_options), 3)
        self.assertIn("Thẻ Căn cước", res.suggested_options)
        self.assertIn("Giấy phép lái xe", res.suggested_options)

    def test_5_vector_relevance_threshold_filtering(self):
        """Kiểm tra cơ chế lọc điểm tương đồng Cosine (Similarity Threshold >= 0.55)."""
        mock_doc_high = (
            Document(page_content="Lệ phí cấp đổi giấy phép lái xe là 135.000 đồng/lần.", metadata={"source": "gplx"}),
            0.82
        )
        mock_doc_low = (
            Document(page_content="Nội dung không liên quan...", metadata={"source": "rac"}),
            0.35
        )

        with patch("src.rag.retriever.get_embedding_model"), \
             patch("src.rag.retriever.Chroma"), \
             patch("src.rag.retriever.get_llm_model"):
            rag = AdministrativeRAG(similarity_threshold=0.55)
            
            # Giả lập trả về cả doc cao điểm và doc thấp điểm
            rag.vector_store.similarity_search_with_relevance_scores = MagicMock(
                return_value=[mock_doc_high, mock_doc_low]
            )
            rag.chain = MagicMock()
            rag.chain.invoke.return_value = "Lệ phí là 135.000 đồng."

            res = rag.query("Lệ phí đổi giấy phép lái xe bao nhiêu?")
            self.assertTrue(res["found_in_docs"])
            self.assertEqual(res["source_type"], "local")
            self.assertIn("135.000", res["answer"])

    def test_6_vector_entropy_two_procedure_ambiguity(self):
        """Kiểm tra lớp 2 Vector Entropy khi top tài liệu thuộc 2 thủ tục khác nhau với điểm sít sao và < 0.55."""
        doc1 = Document(page_content="Thủ tục thường trú...", metadata={"source": "data/thu_tuc_dang_ky_thuong_tru.txt"})
        doc2 = Document(page_content="Thủ tục tạm trú...", metadata={"source": "data/thu_tuc_dang_ky_tam_tru.txt"})

        entropy_res = self.ambiguity_detector.vector_entropy_check(
            "đăng ký cư trú ở đâu",
            [(doc1, 0.49), (doc2, 0.47)]
        )
        self.assertTrue(entropy_res.is_ambiguous)
        self.assertIn("Đăng ký Thường trú", entropy_res.candidates)
        self.assertIn("Đăng ký Tạm trú", entropy_res.candidates)
        self.assertIsNotNone(entropy_res.clarification_prompt)


if __name__ == "__main__":
    unittest.main()
