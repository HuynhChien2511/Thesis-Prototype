"""
Module Phát hiện Câu hỏi Mơ hồ & Chủ động Hỏi lại Làm rõ (Ambiguity Detection & Guided Clarification).
Kiến trúc Lọc 2 Lớp:
  - Lớp 1 (Fast Rule-based Gate < 0.1ms): Quét thực thể thủ tục & kiểm tra SessionState ghim sẵn.
  - Lớp 2 (Vector Distribution Divergence): Đánh giá độ phân tán tài liệu từ ChromaDB.
Áp dụng quy tắc công thái học giọng nói (Voice UI - Rule of Three): Gợi ý tối đa 2-3 phương án ngắn gọn.
"""
import re
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field

from src.rag.dialogue_manager import DialogueSession


@dataclass
class AmbiguityResult:
    """Kết quả đánh giá tính mơ hồ của câu hỏi."""
    is_ambiguous: bool = False
    ambiguity_type: Optional[str] = None       # "missing_procedure", "polysemous", "missing_age_condition"
    missing_slots: List[str] = field(default_factory=list)
    clarification_prompt: Optional[str] = None
    suggested_options: List[str] = field(default_factory=list)

    @property
    def candidates(self) -> List[str]:
        return self.suggested_options


# Danh sách thủ tục cụ thể đã có dữ liệu hoặc phổ biến tại bộ phận Một cửa
SPECIFIC_PROCEDURE_ENTITIES = [
    (r"\b(căn cước|cccd|cmnd|thẻ căn cước)\b", "Thẻ Căn cước"),
    (r"\b(tạm trú|đkttr)\b", "Đăng ký Tạm trú"),
    (r"\b(thường trú|đktt|hộ khẩu)\b", "Đăng ký Thường trú"),
    (r"\b(kết hôn|đăng ký kết hôn|hôn thú)\b", "Đăng ký Kết hôn"),
    (r"\b(khai sinh|giấy khai sinh)\b", "Đăng ký Khai sinh"),
    (r"\b(khai tử|chứng tử)\b", "Đăng ký Khai tử"),
    (r"\b(hộ chiếu|passport)\b", "Cấp Hộ chiếu"),
    (r"\b(giấy phép lái xe|bằng lái|gplx)\b", "Giấy phép lái xe"),
    (r"\b(đăng ký xe|cà vẹt xe)\b", "Đăng ký xe"),
    (r"\b(sổ đỏ|đất đai|nhà đất)\b", "Cấp Giấy chứng nhận quyền sử dụng đất"),
    (r"\b(chứng thực|sao y|chứng thực chữ ký|chứng thực bản sao)\b", "Chứng thực bản sao"),
    (r"\b(xác nhận độc thân|tình trạng hôn nhân|chứng nhận độc thân)\b", "Xác nhận tình trạng hôn nhân"),
]

# Các mẫu câu hỏi mơ hồ, cộc lốc hoặc thiếu thực thể xác định
AMBIGUOUS_PATTERNS = [
    # 1. Hỏi chi phí/lệ phí mà không rõ thủ tục
    (
        r"^(làm\s+)?(cái này|cái đó|thủ tục này|hồ sơ này)?\s*(hết|mất|tốn)?\s*bao nhiêu\s+(tiền|lệ phí|phí)\??$",
        "missing_procedure",
        "Dạ, Quý khách đang cần hỏi lệ phí làm Thẻ Căn cước, Đăng ký Tạm trú hay Đăng ký Kết hôn ạ?",
        ["Thẻ Căn cước", "Đăng ký Tạm trú", "Đăng ký Kết hôn"]
    ),
    # 2. Hỏi thời hạn giải quyết mà không rõ thủ tục
    (
        r"^(làm\s+)?(cái này|cái đó|thủ tục này)?\s*(mất|hết|trong)?\s*(bao lâu|mấy ngày|bao nhiêu ngày)\s*(thì có|thì xong|thì lấy được)?\??$",
        "missing_procedure",
        "Dạ, Quý khách đang cần hỏi thời hạn giải quyết của thủ tục làm Thẻ Căn cước, Đăng ký Tạm trú hay thủ tục nào khác ạ?",
        ["Thẻ Căn cước", "Đăng ký Tạm trú"]
    ),
    # 3. Hỏi thủ tục cấp đổi chung chung
    (
        r"^(cho tôi hỏi\s+)?(thủ tục\s+)?(cấp đổi|đổi lại|cấp lại|làm lại)(\s+cần\s+(gì|những gì))?\??$",
        "polysemous",
        "Dạ, Quý khách đang cần cấp đổi Thẻ Căn cước công dân, Giấy phép lái xe hay Đăng ký xe ạ?",
        ["Thẻ Căn cước", "Giấy phép lái xe", "Đăng ký xe"]
    ),
    # 4. Hỏi về độ tuổi điều kiện
    (
        r"^(cho tôi hỏi\s+)?(bao nhiêu tuổi|mấy tuổi|độ tuổi nào)\s+(thì được|mới được|phải làm)\??$",
        "missing_age_condition",
        "Dạ, Quý khách đang muốn hỏi về độ tuổi làm Thẻ Căn cước hay độ tuổi Đăng ký Kết hôn ạ?",
        ["Làm Thẻ Căn cước", "Đăng ký Kết hôn"]
    ),
    # 5. Hỏi chung chung "cần giấy tờ gì"
    (
        r"^(làm\s+)?(cái này|cái đó|thủ tục này)\s+cần\s+(giấy tờ|hồ sơ gì|những gì)\??$",
        "missing_procedure",
        "Dạ, Quý khách đang cần chuẩn bị hồ sơ làm Thẻ Căn cước, Đăng ký Tạm trú hay Đăng ký Kết hôn ạ?",
        ["Thẻ Căn cước", "Đăng ký Tạm trú", "Đăng ký Kết hôn"]
    ),
    # 6. Hỏi nơi nộp hồ sơ chung chung
    (
        r"^(nộp|làm)\s+(ở đâu|chỗ nào|cơ quan nào)\??$",
        "missing_procedure",
        "Dạ, Quý khách đang cần hỏi địa điểm nộp hồ sơ của Thẻ Căn cước, Tạm trú hay Kết hôn ạ?",
        ["Thẻ Căn cước", "Đăng ký Tạm trú", "Đăng ký Kết hôn"]
    )
]


class AmbiguityDetector:
    """Bộ phát hiện mơ hồ và điều phối câu hỏi làm rõ."""

    def __init__(self, vector_store: Optional[Any] = None):
        self.vector_store = vector_store

    def extract_procedure_entity(self, text: str) -> Optional[str]:
        """Trích xuất thực thể thủ tục cụ thể nếu có trong câu hỏi."""
        if not text:
            return None
        text_lower = text.lower()
        for pattern, canon_name in SPECIFIC_PROCEDURE_ENTITIES:
            if re.search(pattern, text_lower):
                return canon_name
        return None

    def fast_rule_check(self, query: str, session: Optional[DialogueSession] = None) -> AmbiguityResult:
        """
        Lớp 1 (Fast Rule-based Gate < 0.1ms):
        - Nếu câu hỏi đã có thực thể thủ tục -> KHÔNG MƠ HỒ.
        - Nếu SessionState đã ghim thủ tục trước đó -> KHÔNG MƠ HỒ (đang nối tiếp mạch).
        - Khớp với các mẫu câu mơ hồ điển hình.
        """
        clean_q = query.strip()
        q_lower = clean_q.lower()

        # 1. Kiểm tra xem trong câu hỏi đã có tên thủ tục rõ ràng chưa
        found_entity = self.extract_procedure_entity(q_lower)
        if found_entity:
            # Có thủ tục rõ ràng -> Cập nhật vào session và cho qua ngay
            if session:
                session.update_slots(procedure_name=found_entity)
            return AmbiguityResult(is_ambiguous=False)

        # 2. Kiểm tra xem phiên hội thoại đã có thủ tục ghim từ các câu trước chưa
        if session and session.slots.procedure_name:
            # Đã có ngữ cảnh thủ tục ghim từ trước (ví dụ câu trước vừa hỏi Căn cước, câu này hỏi "hết bao nhiêu tiền?")
            return AmbiguityResult(is_ambiguous=False)

        # 3. Quét các mẫu câu mơ hồ kinh điển
        for pattern, amb_type, clarification_text, options in AMBIGUOUS_PATTERNS:
            if re.search(pattern, q_lower):
                return AmbiguityResult(
                    is_ambiguous=True,
                    ambiguity_type=amb_type,
                    missing_slots=["procedure_name"],
                    clarification_prompt=clarification_text,
                    suggested_options=options
                )

        # 4. Kiểm tra các câu hỏi siêu ngắn (< 4 từ) chứa từ khóa chỉ định mơ hồ
        words = q_lower.split()
        if len(words) <= 4:
            has_demonstrative = any(w in q_lower for w in ["cái này", "cái đó", "thủ tục này", "làm này"])
            has_action = any(w in q_lower for w in ["bao nhiêu", "làm sao", "ở đâu", "thế nào", "cần gì"])
            if has_demonstrative and has_action:
                return AmbiguityResult(
                    is_ambiguous=True,
                    ambiguity_type="missing_procedure",
                    missing_slots=["procedure_name"],
                    clarification_prompt="Dạ, Quý khách đang cần hỏi về thủ tục làm Thẻ Căn cước, Đăng ký Tạm trú hay Đăng ký Kết hôn ạ?",
                    suggested_options=["Thẻ Căn cước", "Đăng ký Tạm trú", "Đăng ký Kết hôn"]
                )

        return AmbiguityResult(is_ambiguous=False)

    def vector_entropy_check(
        self,
        query: str,
        docs_with_scores: List[Tuple[Any, float]],
        session: Optional[DialogueSession] = None
    ) -> AmbiguityResult:
        """
        Lớp 2 (Phân tích Độ phân tán Vector - Vector Entropy Check):
        Được gọi sau khi truy vấn ChromaDB nếu Lớp 1 chưa chắc chắn.
        Nếu các tài liệu tìm được thuộc nhiều file thủ tục hoàn toàn khác nhau
        và điểm số phân tán sàn sàn nhau (không có kết quả nào vượt trội).
        """
        # Nếu câu hỏi đã rõ hoặc session đã ghim, bỏ qua Lớp 2
        if session and session.slots.procedure_name:
            return AmbiguityResult(is_ambiguous=False)

        if not docs_with_scores or len(docs_with_scores) < 2:
            return AmbiguityResult(is_ambiguous=False)

        # Lấy danh sách tên file nguồn từ metadata
        sources = []
        scores = []
        for doc, score in docs_with_scores:
            src = str(doc.metadata.get("source_file", "") or doc.metadata.get("source", ""))
            if src and src not in sources:
                sources.append(src)
            scores.append(score)

        # Nếu top 2-3 tài liệu thuộc >= 2 tệp luật khác nhau và điểm tương đồng max < 0.55
        if len(sources) >= 2 and scores[0] < 0.55:
            score_diff = abs(scores[0] - scores[1])
            # Điểm số xấp xỉ nhau (chênh lệch < 0.08) -> Bằng chứng toán học câu hỏi bị phân tán ngữ nghĩa
            if score_diff < 0.08:
                options = []
                for src in sources[:3]:
                    src_lower = src.lower()
                    if "can_cuoc" in src_lower or "căn cước" in src_lower:
                        if "Thẻ Căn cước" not in options:
                            options.append("Thẻ Căn cước")
                    elif "tam_tru" in src_lower or "tạm trú" in src_lower:
                        if "Đăng ký Tạm trú" not in options:
                            options.append("Đăng ký Tạm trú")
                    elif "ket_hon" in src_lower or "kết hôn" in src_lower:
                        if "Đăng ký Kết hôn" not in options:
                            options.append("Đăng ký Kết hôn")
                    elif "khai_sinh" in src_lower or "khai sinh" in src_lower:
                        if "Đăng ký Khai sinh" not in options:
                            options.append("Đăng ký Khai sinh")
                    elif "khai_tu" in src_lower or "khai tử" in src_lower:
                        if "Đăng ký Khai tử" not in options:
                            options.append("Đăng ký Khai tử")
                    elif "thuong_tru" in src_lower or "thường trú" in src_lower:
                        if "Đăng ký Thường trú" not in options:
                            options.append("Đăng ký Thường trú")
                    elif "ho_chieu" in src_lower or "hộ chiếu" in src_lower:
                        if "Cấp Hộ chiếu" not in options:
                            options.append("Cấp Hộ chiếu")
                    elif "chung_thuc" in src_lower or "chứng thực" in src_lower:
                        if "Chứng thực bản sao" not in options:
                            options.append("Chứng thực bản sao")
                    elif "hon_nhan" in src_lower or "độc thân" in src_lower:
                        if "Xác nhận tình trạng hôn nhân" not in options:
                            options.append("Xác nhận tình trạng hôn nhân")
                    elif "lai_xe" in src_lower or "bằng lái" in src_lower or "gplx" in src_lower:
                        if "Giấy phép lái xe" not in options:
                            options.append("Giấy phép lái xe")
                if not options:
                    options = ["Thẻ Căn cước", "Đăng ký Tạm trú"]

                opts_text = ", ".join(options)
                return AmbiguityResult(
                    is_ambiguous=True,
                    ambiguity_type="polysemous",
                    missing_slots=["procedure_name"],
                    clarification_prompt=f"Dạ, câu hỏi của Quý khách có thể liên quan đến {opts_text}. Quý khách vui lòng cho biết rõ tên thủ tục cần hỗ trợ ạ?",
                    suggested_options=options
                )

        return AmbiguityResult(is_ambiguous=False)

    def evaluate(
        self,
        query: str,
        session: Optional[DialogueSession] = None,
        docs_with_scores: Optional[List[Tuple[Any, float]]] = None
    ) -> AmbiguityResult:
        """Đánh giá toàn diện cả 2 lớp."""
        # 1. Chạy Lớp 1 siêu tốc (< 0.1ms)
        l1_res = self.fast_rule_check(query, session)
        if l1_res.is_ambiguous:
            return l1_res

        # 2. Nếu có kết quả vector từ ChromaDB, chạy Lớp 2
        if docs_with_scores is not None:
            l2_res = self.vector_entropy_check(query, docs_with_scores, session)
            if l2_res.is_ambiguous:
                return l2_res

        return AmbiguityResult(is_ambiguous=False)

    def reconstruct_query(
        self,
        original_raw_query: str = "",
        clarification_answer: str = "",
        session: Optional[DialogueSession] = None,
        original_query: Optional[str] = None,
        user_clarification: Optional[str] = None,
        missing_slots: Optional[List[str]] = None
    ) -> str:
        """
        Tái cấu trúc câu hỏi hoàn chỉnh (Query Reconstruction):
        Ghép câu hỏi gốc (hỏi về lệ phí, thời hạn, nơi nộp) với câu trả lời làm rõ của người dân.
        Đồng thời ghim thủ tục vào SessionState Tầng 1.
        """
        if original_query is not None:
            original_raw_query = original_query
        if user_clarification is not None:
            clarification_answer = user_clarification
        clean_ans = clarification_answer.strip()
        found_entity = self.extract_procedure_entity(clean_ans)
        
        target_procedure = found_entity or clean_ans
        if session:
            # Nếu có danh sách missing_slots chỉ định, ưu tiên cập nhật đúng slot đó
            if missing_slots and "procedure_name" not in missing_slots:
                pass
            else:
                session.update_slots(procedure_name=target_procedure)

        orig_lower = original_raw_query.lower()
        
        # 1. Nếu hỏi về chi phí / lệ phí
        if any(w in orig_lower for w in ["tiền", "lệ phí", "phí"]):
            return f"Lệ phí làm thủ tục {target_procedure} hết bao nhiêu tiền?"
            
        # 2. Nếu hỏi về thời hạn
        if any(w in orig_lower for w in ["bao lâu", "mấy ngày", "thời hạn"]):
            return f"Thời hạn giải quyết thủ tục {target_procedure} là bao lâu?"
            
        # 3. Nếu hỏi về hồ sơ / giấy tờ
        if any(w in orig_lower for w in ["giấy tờ", "hồ sơ", "cần gì"]):
            return f"Hồ sơ và giấy tờ cần chuẩn bị cho thủ tục {target_procedure} gồm những gì?"
            
        # 4. Nếu hỏi về địa điểm nộp
        if any(w in orig_lower for w in ["ở đâu", "chỗ nào", "nơi nộp"]):
            return f"Địa điểm nộp hồ sơ thủ tục {target_procedure} ở đâu?"
            
        # 5. Mặc định ghép nối tự nhiên
        clean_orig = re.sub(r"\b(cái này|cái đó|thủ tục này|hồ sơ này)\b", target_procedure, original_raw_query, flags=re.IGNORECASE)
        if target_procedure.lower() not in clean_orig.lower():
            clean_orig = f"{clean_orig} (đối với thủ tục {target_procedure})"
        return clean_orig
