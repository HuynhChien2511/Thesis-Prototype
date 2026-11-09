"""
Bộ kiểm thử Tự động cho Module Chuẩn hóa Văn bản Hành chính (Text Normalizer).
Kiểm tra:
  1. Tẩy sạch cú pháp Markdown (in đậm, tiêu đề, bullet points, phân cách).
  2. Mở rộng từ viết tắt hành chính công chuyên ngành (CCCD, VNeID, UBND, CT01, BHYT).
  3. Chuẩn hóa định dạng ngày tháng sang ngữ âm đọc tự nhiên (dd/mm/yyyy).
  4. Chuyển đổi số hiệu văn bản pháp lý (Nghị định 123/2015/NĐ-CP).
  5. Bảo vệ dấu chấm trong số tiền (50.000 đồng) và số thập phân (1.5 ngày).
  6. Xử lý dấu gạch chéo giữa các từ (xã/phường, nam/nữ, cha/mẹ).
  7. Tẩy sạch URL và chuyển đổi Hộp Cảnh báo Internet thành câu nói tự nhiên.
  8. Xử lý an toàn chuỗi rỗng, dấu chấm lặp và khoảng trắng dư thừa.
"""
import sys
import unittest
from pathlib import Path

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.audio.text_normalizer import (
    clean_markdown_for_speech,
    expand_admin_abbreviations,
    normalize_for_tts,
)


class TestTextNormalizer(unittest.TestCase):

    def test_1_markdown_cleaning(self):
        """Kiểm tra tẩy sạch các thẻ tiêu đề, in đậm, in nghiêng và gạch ngang Markdown."""
        text = "### 1. Giấy tờ cần nộp\n- Bản chính **Giấy khai sinh** và *CCCD*.\n---\n*Hết mục 1.*"
        cleaned = clean_markdown_for_speech(text)
        self.assertNotIn("###", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("---", cleaned)
        self.assertIn("Giấy khai sinh", cleaned)

    def test_2_admin_abbreviations(self):
        """Kiểm tra mở rộng chính xác các từ viết tắt công vụ sang cách phát âm tiếng Việt."""
        text = "Công dân mang theo CCCD và Mẫu CT01 đến UBND xã để cập nhật VNeID."
        expanded = expand_admin_abbreviations(text)
        self.assertIn("căn cước công dân", expanded.lower())
        self.assertIn("mẫu c t không một", expanded.lower())
        self.assertIn("ủy ban nhân dân", expanded.lower())
        self.assertIn("vê en e ai đi", expanded.lower())

    def test_3_date_normalization(self):
        """Kiểm tra ngày tháng dạng 15/10/2024 được đọc thành 'ngày 15 tháng 10 năm 2024'."""
        text = "Hạn chót nộp hồ sơ là ngày 15/10/2024 tại bộ phận Một cửa."
        cleaned = clean_markdown_for_speech(text)
        self.assertIn("ngày 15 tháng 10 năm 2024", cleaned)

    def test_4_legal_document_ids(self):
        """Kiểm tra số hiệu văn bản như 123/2015 được chuyển thành '123 năm 2015'."""
        text = "Căn cứ theo Nghị định số 123/2015 và Luật số 68/2020."
        cleaned = clean_markdown_for_speech(text)
        self.assertIn("123 năm 2015", cleaned)
        self.assertIn("68 năm 2020", cleaned)

    def test_5_money_and_decimal_protection(self):
        """Kiểm tra số tiền (50.000 đồng) và số thập phân (1.5 ngày) không bị ngắt khoảng trắng làm rách số."""
        text = "Lệ phí là 50.000 đồng. Thời gian giải quyết là 1.5 ngày làm việc."
        normalized = normalize_for_tts(text)
        self.assertIn("50.000", normalized)
        self.assertIn("1.5", normalized)

    def test_6_slash_conversion(self):
        """Kiểm tra các từ ghép có dấu gạch chéo được diễn đạt tự nhiên cho loa ngoài."""
        text = "Áp dụng cho công dân thường trú tại xã/phường hoặc quận/huyện, không phân biệt nam/nữ."
        cleaned = clean_markdown_for_speech(text)
        self.assertIn("xã, phường", cleaned)
        self.assertIn("quận, huyện", cleaned)
        self.assertIn("nam hoặc nữ", cleaned)

    def test_7_disclaimer_and_url_removal(self):
        """Kiểm tra Hộp Cảnh báo Internet được chuyển thành câu mở đầu tự nhiên và xóa URL thô."""
        raw_text = (
            "⚠️ CẢNH BÁO TRA CỨU INTERNET: Thông tin chưa có trong nội bộ.\n\n"
            "Hôm nay trời nắng đẹp.\n\n"
            "📚 NGUỒN TRA CỨU:\n- https://dichvucong.gov.vn/thong-bao"
        )
        normalized = normalize_for_tts(raw_text)
        self.assertNotIn("https://", normalized)
        self.assertNotIn("📚 NGUỒN TRA CỨU", normalized)
        self.assertIn("Lưu ý: Thông tin sau được tôi tra cứu từ internet", normalized)

    def test_8_empty_and_edge_cases(self):
        """Kiểm tra các trường hợp biên: văn bản rỗng, khoảng trắng thừa, dấu câu lặp lại."""
        self.assertEqual(normalize_for_tts(""), "")
        self.assertEqual(normalize_for_tts("   "), "")
        
        text_with_dots = "...Xin chào quý khách...   Tôi là robot......."
        normalized = normalize_for_tts(text_with_dots)
        self.assertFalse(normalized.startswith("."))
        self.assertNotIn("....", normalized)


if __name__ == "__main__":
    unittest.main()
