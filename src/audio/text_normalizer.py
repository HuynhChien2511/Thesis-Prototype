"""
Module chuẩn hóa văn bản trước khi đưa vào Text-to-Speech (Sprint 3 - Khuôn miệng).
- Loại bỏ các ký tự Markdown (#, **, *, -, ---)
- Phiên âm các từ viết tắt chuyên ngành hành chính công (CCCD, UBND, VNeID, NĐ-CP,...)
- Xử lý số hiệu văn bản pháp lý (123/2015 -> 123 năm 2015)
- Chuẩn hóa ngắt nghỉ câu để giọng đọc tự nhiên, chuẩn mực.
"""
import re
import sys

# Đảm bảo UTF-8 console trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Bảng tra cứu từ viết tắt hành chính công thông dụng
ADMIN_ABBREVIATIONS = [
    (r"\bMẫu\s+CT01\b", "mẫu C T không một"),
    (r"\bCT01\b", "mẫu C T không một"),
    (r"\bCCCD\b", "căn cước công dân"),
    (r"\bCMND\b", "chứng minh nhân dân"),
    (r"\bUBND\b", "ủy ban nhân dân"),
    (r"\bHĐND\b", "hội đồng nhân dân"),
    (r"\bVNeID\b", "vê en e ai đi"),
    (r"\bVNEID\b", "vê en e ai đi"),
    (r"\bBHYT\b", "bảo hiểm y tế"),
    (r"\bBHXH\b", "bảo hiểm xã hội"),
    (r"\bNĐ-CP\b", "nghị định chính phủ"),
    (r"\bTT-BCA\b", "thông tư bộ công an"),
    (r"\bĐKTT\b", "đăng ký thường trú"),
    (r"\bĐKTTr\b", "đăng ký tạm trú"),
    (r"\bDVC\b", "dịch vụ công"),
    (r"\bBCA\b", "bộ công an"),
    (r"\bCSGT\b", "cảnh sát giao thông"),
    (r"\bTAND\b", "tòa án nhân dân"),
    (r"\bVKSND\b", "viện kiểm sát nhân dân"),
    (r"\bTP\.HCM\b", "thành phố Hồ Chí Minh"),
    (r"\bQH15\b", "quốc hội khóa mười lăm"),
    (r"\bQH14\b", "quốc hội khóa mười bốn"),
    (r"\bQH13\b", "quốc hội khóa mười ba"),
    (r"\bdichvucong\.gov\.vn\b", "cổng dịch vụ công quốc gia"),
    (r"\bbocongan\.gov\.vn\b", "cổng thông tin bộ công an"),
]


def clean_markdown_for_speech(text: str) -> str:
    """Tẩy sạch các ký tự và cú pháp định dạng Markdown (kể cả có dấu thụt lề)."""
    if not text:
        return ""

    # Xóa các đường phân cách ngang (---, ===, ***)
    text = re.sub(r"^\s*[=\-_*]{3,}\s*$", ". ", text, flags=re.MULTILINE)

    # Xóa các thẻ tiêu đề (#, ##, ###,...)
    text = re.sub(r"^\s*#{1,6}\s*", " ", text, flags=re.MULTILINE)

    # Xóa định dạng in đậm / in nghiêng (**text**, *text*, _text_)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Xóa các liên kết markdown [tên](url) -> giữ lại tên
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Xóa ký tự phân cách bảng Markdown (|)
    text = re.sub(r"\|", " ", text)

    # Chuyển gạch đầu dòng bullet point (- , * , + ) thành dấu ngắt câu nhẹ
    text = re.sub(r"^\s*[\*\-\+]\s+", ". ", text, flags=re.MULTILINE)

    # 1. Xử lý ngày tháng định dạng dd/mm/yyyy trước khi xử lý số hiệu văn bản (tránh méo dạng 15/10/2024 -> 15 trên 10 năm 2024)
    # Nếu đã có từ "ngày" phía trước: "ngày 15/10/2024" -> "ngày 15 tháng 10 năm 2024"
    text = re.sub(r"(?<=\bngày\s)(\d{1,2})/(\d{1,2})/(\d{4})\b", r"\1 tháng \2 năm \3", text, flags=re.IGNORECASE)
    # Nếu đứng độc lập chưa có "ngày": "15/10/2024" -> "ngày 15 tháng 10 năm 2024"
    text = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", r"ngày \1 tháng \2 năm \3", text)
    # Xử lý ngày tháng định dạng dd/mm khi đi liền sau từ "ngày"
    text = re.sub(r"(?<=\bngày\s)(\d{1,2})/(\d{1,2})\b", r"\1 tháng \2", text, flags=re.IGNORECASE)

    # 2. Xử lý số hiệu văn bản: ví dụ "123/2015" -> "123 năm 2015", "68/2020/QH14" -> "68 năm 2020 QH14"
    text = re.sub(r"(\d+)/(\d{4})", r"\1 năm \2", text)
    text = re.sub(r"(\d+)/(\d+)", r"\1 trên \2", text)

    # Chuyển đổi dấu xuyệt (/) giữa các từ thành dấu phẩy hoặc từ nối
    text = re.sub(r"xã/phường/thị trấn", "xã, phường, thị trấn", text, flags=re.IGNORECASE)
    text = re.sub(r"xã/phường", "xã, phường", text, flags=re.IGNORECASE)
    text = re.sub(r"quận/huyện", "quận, huyện", text, flags=re.IGNORECASE)
    text = re.sub(r"tỉnh/thành phố", "tỉnh, thành phố", text, flags=re.IGNORECASE)
    text = re.sub(r"nam/nữ", "nam hoặc nữ", text, flags=re.IGNORECASE)
    text = re.sub(r"cha/mẹ", "cha hoặc mẹ", text, flags=re.IGNORECASE)
    text = re.sub(r"đổi/cấp", "đổi hoặc cấp", text, flags=re.IGNORECASE)

    return text


def expand_admin_abbreviations(text: str) -> str:
    """Phiên âm các từ viết tắt chuyên ngành hành chính công."""
    for pattern, replacement in ADMIN_ABBREVIATIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def normalize_for_tts(text: str) -> str:
    """
    Quy trình chuẩn hóa toàn diện cho Text-to-Speech:
    1. Tẩy Markdown
    2. Phiên âm từ viết tắt
    3. Tối ưu ngắt nghỉ dấu câu (bảo vệ số tiền, số thập phân)
    """
    if not text:
        return ""

    # 1. Tẩy Markdown
    text = clean_markdown_for_speech(text)

    # 2. Mở rộng từ viết tắt
    text = expand_admin_abbreviations(text)

    # 3. Chuẩn hóa khoảng trắng và dấu câu
    text = re.sub(r"/\s*(quốc hội)", r", \1", text, flags=re.IGNORECASE)
    
    # Xóa các dấu câu lặp lại (ví dụ .., ;;, ,,)
    text = re.sub(r"([.,;])\s*([.,;])+", r"\1", text)

    # Chuẩn hóa khoảng trắng quanh dấu chấm (.) và dấu phẩy (,):
    # KHÔNG chèn khoảng trắng giữa các chữ số để bảo vệ số tiền và số thập phân (ví dụ: 50.000, 1.5, 50,000)
    text = re.sub(r"(?<!\d)\s*\.\s*", ". ", text)
    text = re.sub(r"(?<=\d)\s*\.\s*(?!\d)", ". ", text)
    text = re.sub(r"(?<!\d)\s*,\s*", ", ", text)
    text = re.sub(r"(?<=\d)\s*,\s*(?!\d)", ", ", text)
    text = re.sub(r"\s*;\s*", "; ", text)

    # Xóa dấu chấm hoặc dấu câu dư thừa ở đầu chuỗi (do bullet point chuyển thành)
    text = re.sub(r"^[.,;\s]+", "", text)

    # Thu gọn nhiều khoảng trắng và dấu chấm kéo dài
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


if __name__ == "__main__":
    sample = """
    ### 1. Thành phần hồ sơ cần chuẩn bị
    - Tờ khai thay đổi thông tin cư trú (**Mẫu CT01**).
    - Xuất trình thẻ **CCCD** gắn chip hoặc tài khoản **VNeID** mức 2.
    - Nộp tại **UBND** cấp xã/phường hoặc qua cổng **dichvucong.gov.vn**.
    ---
    *Căn cứ pháp lý: Luật Cư trú số 68/2020/QH14 và NĐ-CP số 123/2015.*
    """
    print("Văn bản gốc:\n", sample)
    print("\nVăn bản chuẩn hóa cho TTS:\n", normalize_for_tts(sample))
