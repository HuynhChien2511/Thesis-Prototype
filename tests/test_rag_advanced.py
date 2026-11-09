"""
Kiểm thử Unit Test Chuyên sâu cho Phân hệ RAG & Quản lý Tri thức Pháp luật (8 bài test).
Bao gồm:
  1. Bộ lọc ngưỡng tương đồng nghiêm ngặt (Similarity Threshold = 0.55 Rejection).
  2. Tiếp nhận và trích dẫn tài liệu khi khoảng cách Cosine <= 0.55.
  3. Phân loại câu hỏi hành chính công vs câu hỏi đời thường (is_admin_procedure_query).
  4. Cơ chế gắn tiêu đề Contextual Header Prepension (Chống 'Lost in Chunking' - Điểm nghẽn 3).
  5. Khả năng nhận diện câu hỏi tiếng Việt không dấu (Accentless Vietnamese).
  6. Xử lý an toàn câu hỏi chứa ký tự đặc biệt, dấu ngoặc, dấu nháy.
  7. Ràng buộc các quy tắc đạo đức & chống bịa đặt trong ADMIN_RAG_SYSTEM_PROMPT.
  8. Kích hoạt Web Search Fallback khi tri thức nội bộ không tìm thấy dữ liệu.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.rag.retriever import (
    AdministrativeRAG,
    is_admin_procedure_query,
    ADMIN_RAG_SYSTEM_PROMPT
)


def split_document_with_header(title: str, text: str) -> list:
    """Mô phỏng cơ chế chia nhỏ văn bản luật kèm tiêu đề [THỦ TỤC: {title}]."""
    import re
    articles = re.split(r"(?=\nĐiều\s+\d+)", text.strip())
    chunks = []
    for art in articles:
        art = art.strip()
        if art:
            chunks.append(f"[THỦ TỤC: {title}]\n{art}")
    return chunks


class TestRAGAdvanced(unittest.TestCase):
    """Bộ kiểm thử nâng cao cho Não bộ RAG và Vector Store."""

    def test_1_similarity_threshold_rejection(self):
        """1. Kiểm tra tài liệu có điểm tương đồng < 0.55 bị từ chối (không nhận vơ)."""
        rag = AdministrativeRAG(similarity_threshold=0.55)
        mock_doc = MagicMock()
        mock_doc.page_content = "Nội dung không liên quan"
        mock_doc.metadata = {"source_file": "Luật Hôn nhân.txt"}

        # Điểm relevance score 0.35 < 0.55 -> Bị từ chối
        with patch.object(rag.vector_store, "similarity_search_with_relevance_scores", return_value=[(mock_doc, 0.35)]), \
             patch.object(rag, "enable_web_search", False):
            res = rag.query("Làm thẻ căn cước ở đâu?")
            self.assertFalse(res["found_in_docs"])
            self.assertIn("chưa có quy định cụ thể", res["answer"].lower())

    def test_2_similarity_threshold_acceptance(self):
        """2. Kiểm tra tài liệu có điểm tương đồng >= 0.55 được chấp thuận và trích dẫn."""
        rag = AdministrativeRAG(similarity_threshold=0.55)
        mock_doc = MagicMock()
        mock_doc.page_content = "Điều 10. Lệ phí cấp mới căn cước được miễn hoàn toàn."
        mock_doc.metadata = {"source_file": "Thông tư 73/2024/TT-BTC.txt"}

        rag.chain = MagicMock()
        rag.chain.invoke.return_value = "Cấp mới căn cước được miễn phí. Căn cứ: Thông tư 73/2024/TT-BTC"

        # Điểm relevance score 0.85 >= 0.55 -> Được chấp thuận
        with patch.object(rag.vector_store, "similarity_search_with_relevance_scores", return_value=[(mock_doc, 0.85)]):
            res = rag.query("Lệ phí làm căn cước?")
            self.assertTrue(res["found_in_docs"])
            self.assertEqual(res["source_type"], "local")
            self.assertIn("Thông tư 73/2024/TT-BTC.txt", res["sources"])

    def test_3_is_admin_procedure_query_detection(self):
        """3. Kiểm tra hàm phân loại câu hỏi thủ tục hành chính vs câu hỏi đời thường."""
        self.assertTrue(is_admin_procedure_query("Thủ tục làm hộ chiếu"))
        self.assertTrue(is_admin_procedure_query("Lệ phí trước bạ xe máy"))
        self.assertTrue(is_admin_procedure_query("Đăng ký thường trú cần giấy tờ gì"))
        self.assertFalse(is_admin_procedure_query("Hôm nay ăn cơm với gì ngon?"))
        self.assertFalse(is_admin_procedure_query("Cách nấu bún bò Huế thơm ngon"))

    def test_4_hierarchical_header_prepension_in_chunking(self):
        """4. Kiểm tra gắn tiêu đề thủ tục vào từng chunk Điều luật (Khắc phục Điểm nghẽn 3)."""
        raw_law_text = (
            "Điều 1. Phạm vi điều chỉnh.\nNghị định này quy định về cấp đổi GPLX.\n"
            "Điều 2. Đối tượng áp dụng.\nÁp dụng cho mọi công dân có giấy phép lái xe."
        )
        chunks = split_document_with_header("Cấp đổi Giấy phép lái xe", raw_law_text)
        self.assertEqual(len(chunks), 2)
        # Mỗi chunk bắt buộc phải có tiền tố tiêu đề nhận diện
        self.assertTrue(chunks[0].startswith("[THỦ TỤC: Cấp đổi Giấy phép lái xe]"))
        self.assertTrue(chunks[1].startswith("[THỦ TỤC: Cấp đổi Giấy phép lái xe]"))

    def test_5_accentless_vietnamese_query_handling(self):
        """5. Kiểm tra câu hỏi thủ tục tiếng Việt không dấu vẫn trích xuất chính xác tên thủ tục vào SessionSlots."""
        from src.rag.dialogue_manager import SessionSlots
        slots = SessionSlots()
        # Câu hỏi hoàn toàn không dấu
        slots.update_from_query("cap doi giay phep lai xe het bao nhieu tien")
        self.assertEqual(slots.procedure_name, "cấp đổi giấy phép lái xe")

    def test_6_query_with_special_characters_and_punctuation(self):
        """6. Kiểm tra xử lý an toàn câu hỏi chứa dấu nháy, ngoặc đơn, gạch chéo không bị lỗi SQL/Regex."""
        rag = AdministrativeRAG()
        complex_query = "Thủ tục cấp hộ chiếu (online) qua cổng 'dichvucong.gov.vn' & 'bocongan.gov.vn'?"
        # Mock vector search
        with patch.object(rag.vector_store, "similarity_search_with_relevance_scores", return_value=[]), \
             patch.object(rag, "enable_web_search", False):
            res = rag.query(complex_query)
            self.assertIsNotNone(res["answer"])
            self.assertFalse(res["found_in_docs"])

    def test_7_rag_system_prompt_core_rules(self):
        """7. Kiểm tra System Prompt chứa đầy đủ 4 nguyên tắc cốt lõi: không bịa đặt, súc tích, trích dẫn."""
        self.assertIn("CHỈ ĐƯỢC PHÉP TRẢ LỜI DỰA TRÊN [NGỮ CẢNH TÀI LIỆU]", ADMIN_RAG_SYSTEM_PROMPT)
        self.assertIn("Tuyệt đối không tự bịa đặt", ADMIN_RAG_SYSTEM_PROMPT)
        self.assertIn("dichvucong.gov.vn", ADMIN_RAG_SYSTEM_PROMPT)
        self.assertIn("TRÍCH DẪN NGUỒN", ADMIN_RAG_SYSTEM_PROMPT)

    def test_8_web_search_fallback_trigger_on_empty_docs(self):
        """8. Kiểm tra khi CSDL nội bộ không có thì tự động kích hoạt Web Search Fallback."""
        rag = AdministrativeRAG()
        rag.enable_web_search = True
        mock_results = [{"url": "https://nchmf.gov.vn", "title": "Thời tiết", "content": "Thời tiết hôm nay 28 độ C"}]
        mock_web_chain = MagicMock()
        mock_web_chain.invoke.return_value = "Dự báo thời tiết hôm nay là 28 độ C tại khu vực miền Trung."
        rag.web_chain = mock_web_chain

        with patch.object(rag.vector_store, "similarity_search_with_relevance_scores", return_value=[]), \
             patch.object(rag.web_searcher, "is_configured", return_value=True), \
             patch.object(rag.web_searcher, "search", return_value={"success": True, "results": mock_results, "sources": ["https://dichvucong.gov.vn"]}):
            res = rag.query("Quy định thủ tục cấp hộ chiếu cho người định cư nước ngoài?")
            self.assertEqual(res["source_type"], "web")
            self.assertTrue(res["warning_issued"])


if __name__ == "__main__":
    unittest.main()
