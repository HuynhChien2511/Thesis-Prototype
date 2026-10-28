"""
Module Guardrail & Intent Filter (Hàng rào an toàn & Bộ lọc ý định cho Robot Hành chính công).

Chức năng:
1. Tier 1 - Lọc rác âm thanh, tiếng ồn Whisper, và ngôn từ tiêu cực/thô tục (< 1ms).
2. Tier 2 - Xử lý tán gẫu xã giao (Chit-chat) và định hình nhân cách (Persona Alignment) (< 2ms).
3. Tier 3 - Phân loại & chặn các yêu cầu lạc đề hoàn toàn (Out-of-Scope Deflection) (< 2ms).
4. Cho phép các câu hỏi hợp lệ (Thủ tục hành chính, Thị giác VQA, Tiện ích đời sống như thời tiết) đi tiếp vào RAG.

Đảm bảo: Phản hồi tức thì (< 5ms), tiết kiệm 100% chi phí API Tavily/Gemini cho các câu vô nghĩa hoặc trêu đùa.
"""

import re
import time
from typing import Dict, Any, Optional, Tuple


class GuardrailManager:
    """
    Quản lý hàng rào an toàn và bộ lọc ý định trước khi truy vấn Não bộ RAG / Web Search.
    """

    def __init__(self):
        # 1. Danh sách tiếng đệm, rác âm thanh (Filler / Audio Noise)
        self.noise_exact_words = {
            "alo", "alo 123", "alo alo", "123", "test", "test mic", "mic",
            "ừm", "ờ", "à", "ê", "nè", "ủa", "hả", "ơ", "chao", "hello",
            "hi", "helo", "o", "a", "um", "uh", "ha", "hơ"
        }

        # 2. Danh sách ngôn từ thô tục / xúc phạm (Profanity / Toxicity)
        # Bao gồm viết tắt và tiếng lóng phổ biến
        self.profanity_patterns = [
            r"\b(đ[ụịm]|đ[cme]|đmm|đcm|vcl|vkl|vl|cl|đb|cc)\b",
            r"\b(địt\s*(mẹ|me|cụ|ba)?|đụ\s*(má|ma|mẹ)?|đậu\s*má|đậu\s*phộng)\b",
            r"\b(ngu\s*(vl|vcl|như\s*chó|ngốc|xuẩn|đần)?|đồ\s*ngu|con\s*ngu|thằng\s*ngu)\b",
            r"\b(chó\s*chết|óc\s*chó|thằng\s*khùng|con\s*khùng|thằng\s*điên|con\s*điên|dở\s*hơi)\b",
            r"\b(cút\s*(đi|ngay)?|biến\s*(đi|ngay)?|im\s*mồm|ngậm\s*miệng)\b",
            r"\b(mẹ\s*kiếp|khốn\s*nạn|vô\s*học)\b"
        ]
        self._profanity_regex = re.compile("|".join(self.profanity_patterns), re.IGNORECASE)

        # 3. Kịch bản Persona & Xã giao (Chit-chat & Identity)
        self.chitchat_rules = [
            # 3.1. Danh tính & Nguồn gốc
            (
                [
                    r"\b(bạn|mày|em|cậu|cháu)\s+(là\s+ai|tên\s+(là\s+)?gì|tên\s+chi)\b",
                    r"\bai\s+(tạo\s+ra|chế\s+tạo|làm\s+ra|phát\s+triển)\s+(bạn|mày|em|robot)\b",
                    r"\b(giới\s+thiệu\s+(về\s+)?bản\s+thân|bạn\s+làm\s+được\s+gì)\b",
                    r"\brobot\s+(tên\s+gì|là\s+ai)\b"
                ],
                "identity",
                (
                    "Dạ, em là Robot Trợ lý Dịch vụ công, được phát triển phục vụ bà con tại Bộ phận Một cửa. "
                    "Em có thể hướng dẫn các thủ tục hành chính như Căn cước công dân, Đăng ký kết hôn, Hộ tịch, "
                    "Cư trú, Đất đai, cũng như quan sát giấy tờ qua camera. Quý khách cần em hỗ trợ thủ tục gì ạ?"
                )
            ),
            # 3.2. Đời tư / Tán tỉnh / Trêu đùa
            (
                [
                    r"\b(có\s+người\s+yêu\s+chưa|yêu\s+(tôi|tao|anh|chị|chú|bác)\s+không)\b",
                    r"\b(lấy\s+(tôi|anh|chú)\s+không|kết\s+hôn\s+với\s+(tôi|anh))\b",
                    r"\b(làm\s+bạn\s+gái|làm\s+vợ)\b",
                    r"\b(xinh\s+gái|đẹp\s+trai|dễ\s+thương|thích\s+bạn|thương\s+bạn)\b"
                ],
                "flirting",
                (
                    "Dạ em là robot công vụ nên chưa có người yêu đâu ạ! "
                    "Nhiệm vụ chính của em là phục vụ nhân dân làm thủ tục hành chính. "
                    "Bác hoặc Anh/Chị cần làm thủ tục hồ sơ gì cứ nói với em nhé!"
                )
            ),
            # 3.3. Giải trí / Hát / Kể chuyện
            (
                [
                    r"\b(hát\s+(cho\s+nghe|một\s+bài|đi)?|biết\s+hát\s+không)\b",
                    r"\b(kể\s+chuyện\s*(cười|ma|hài|vui)?|nói\s+đùa\s+đi)\b",
                    r"\b(múa\s+đi|nhảy\s+đi|lắc\s+lư\s+đi)\b",
                    r"\b(đọc\s+thơ\s+đi|làm\s+thơ\s+đi)\b"
                ],
                "entertainment",
                (
                    "Dạ giọng hát của em chưa hay và em cũng chưa biết nhảy múa đâu ạ! "
                    "Thay vào đó, em nắm rất rõ các quy định hồ sơ, giấy tờ hành chính công. "
                    "Quý khách cần tra cứu thủ tục gì em xin phép hỗ trợ ngay ạ."
                )
            ),
            # 3.4. Khen ngợi
            (
                [
                    r"\b(giỏi\s+quá|thông\s+minh\s+(thế|quá)|đỉnh\s+(thế|thật)|tuyệt\s+vời|good\s+job)\b",
                    r"\b(cảm\s+ơn\s+robot|robot\s+xịn\s+quá)\b"
                ],
                "compliment",
                (
                    "Dạ em cảm ơn quý khách rất nhiều! Em vẫn đang nỗ lực học hỏi để phục vụ bà con ngày một tốt hơn. "
                    "Quý khách cần hỏi thêm thông tin gì về thủ tục hôm nay không ạ?"
                )
            ),
            # 3.5. Chào hỏi đơn thuần
            (
                [
                    r"^(chào\s+(bạn|em|robot)|xin\s+chào(\s+robot)?|hello(\s+robot)?|hi(\s+robot)?)$"
                ],
                "greeting",
                (
                    "Dạ, xin chào quý khách! Em là Trợ lý Hành chính công. "
                    "Em có thể hỗ trợ gì cho bác/anh/chị về thủ tục giấy tờ hôm nay ạ?"
                )
            )
        ]

        # 4. Lạc đề hoàn toàn (Out-of-Scope Deflection)
        self.outofscope_patterns = [
            # Nấu ăn / Ẩm thực
            r"\b(cách\s+nấu|nấu\s+(bún|phở|cơm|cháo|canh|thịt|cá)|công\s+thức\s+nấu|món\s+ăn|cách\s+làm\s+bánh)\b",
            # Trò chơi / Game giải trí
            r"\b(chơi\s+game|liên\s+quân|free\s+fire|genshin|game\s+gì\s+hay|tải\s+game)\b",
            # Giải toán / Học tập phổ thông
            r"\b(giải\s+phương\s+trình|tính\s+đạo\s+hàm|tích\s+phân|giải\s+bài\s+tập\s+toán|viết\s+code|viết\s+phần\s+mềm)\b",
            # Bói toán / Tử vi
            r"\b(xem\s+bói|bói\s+toán|tử\s+vi|cung\s+hoàng\s+đạo|xem\s+chỉ\s+tay)\b"
        ]
        self._outofscope_regex = re.compile("|".join(self.outofscope_patterns), re.IGNORECASE)

    def _clean_text(self, text: str) -> str:
        """Chuẩn hóa chuỗi văn bản đầu vào: loại bỏ ký tự lạ và khoảng trắng thừa."""
        if not text:
            return ""
        # Bỏ dấu câu ở đầu/cuối
        cleaned = re.sub(r"^[?.,!\s]+|[?.,!\s]+$", "", text.strip())
        return cleaned

    def evaluate(self, question: str) -> Dict[str, Any]:
        """
        Đánh giá câu hỏi đầu vào qua 3 tầng guardrail.
        
        Trả về dictionary:
        {
            "handled": bool,          # True nếu guardrail đã xử lý xong (không cần gọi RAG/Web)
            "action": str,            # "pass" | "noise" | "profanity" | "chitchat" | "deflect"
            "answer": Optional[str],  # Câu trả lời phản hồi lại người dùng (nếu handled=True)
            "reason": str,            # Mô tả chi tiết lý do phân loại
            "latency_ms": float       # Thời gian xử lý của bộ lọc (miligiây)
        }
        """
        t0 = time.time()
        cleaned_q = self._clean_text(question)
        q_lower = cleaned_q.lower()
        words = q_lower.split()

        # =========================================================================
        # TIER 1: Lọc rác âm thanh, tiếng ồn & Ngôn từ thô tục
        # =========================================================================
        
        # 1.1 Chuỗi rỗng hoặc chỉ có ký tự đặc biệt
        if not cleaned_q or len(cleaned_q) < 2:
            latency_ms = round((time.time() - t0) * 1000, 2)
            return {
                "handled": True,
                "action": "noise",
                "answer": "Dạ, em chưa nghe rõ. Quý khách vui lòng nói lại hoặc gõ câu hỏi giúp em nhé ạ.",
                "reason": "Chuỗi quá ngắn hoặc không có nội dung rõ ràng",
                "latency_ms": latency_ms
            }

        # 1.2 Từ lặp ký tự vô nghĩa (ví dụ: aaaaa, hahahaha, kkkkkk, uhmmm)
        if re.search(r"(.)\1{4,}", q_lower) or re.match(r"^(ha|he|hi|ho|kk|uh|um){3,}$", q_lower):
            latency_ms = round((time.time() - t0) * 1000, 2)
            return {
                "handled": True,
                "action": "noise",
                "answer": "Dạ, em nghe đây ạ. Quý khách cần em hỗ trợ thủ tục gì không ạ?",
                "reason": "Chuỗi ký tự lặp vô nghĩa (tiếng cười hoặc nhiễu âm thanh)",
                "latency_ms": latency_ms
            }

        # 1.3 Tiếng đệm đơn lẻ (Filler words / Test mic)
        if q_lower in self.noise_exact_words:
            latency_ms = round((time.time() - t0) * 1000, 2)
            return {
                "handled": True,
                "action": "noise",
                "answer": "Dạ, em đang lắng nghe ạ. Quý khách cần em hướng dẫn thủ tục hành chính nào ạ?",
                "reason": f"Từ đệm thử mic đơn lẻ ('{q_lower}')",
                "latency_ms": latency_ms
            }

        # 1.4 Ngôn từ tiêu cực / Xúc phạm / Thô tục
        if self._profanity_regex.search(q_lower):
            latency_ms = round((time.time() - t0) * 1000, 2)
            return {
                "handled": True,
                "action": "profanity",
                "answer": (
                    "Dạ, em là robot hỗ trợ dịch vụ công của cơ quan. "
                    "Em xin phép chỉ trao đổi bằng ngôn từ lịch sự, văn minh ạ. "
                    "Quý khách vui lòng cho biết cần hỗ trợ thủ tục hành chính gì ạ?"
                ),
                "reason": "Phát hiện ngôn từ thô tục / xúc phạm",
                "latency_ms": latency_ms
            }

        # =========================================================================
        # TIER 2: Persona Chit-chat & Small Talk (Xã giao công sở)
        # =========================================================================
        for patterns, intent_type, reply in self.chitchat_rules:
            for pat in patterns:
                if re.search(pat, q_lower):
                    latency_ms = round((time.time() - t0) * 1000, 2)
                    return {
                        "handled": True,
                        "action": "chitchat",
                        "answer": reply,
                        "reason": f"Tán gẫu xã giao theo kịch bản ({intent_type})",
                        "latency_ms": latency_ms
                    }

        # =========================================================================
        # TIER 3: Phân loại & Chặn yêu cầu Lạc đề hoàn toàn (Out-of-Scope Deflection)
        # =========================================================================
        if self._outofscope_regex.search(q_lower):
            latency_ms = round((time.time() - t0) * 1000, 2)
            return {
                "handled": True,
                "action": "deflect",
                "answer": (
                    "Dạ, em là robot chuyên trách hỗ trợ thủ tục hành chính công. "
                    "Vấn đề này nằm ngoài phạm vi công vụ của em. "
                    "Quý công dân cần hướng dẫn về Căn cước, Cư trú, Đất đai, Hộ tịch hay giấy tờ gì em xin phép giải đáp ngay ạ!"
                ),
                "reason": "Chủ đề hoàn toàn nằm ngoài phạm vi công vụ (Nấu ăn, game, giải toán...)",
                "latency_ms": latency_ms
            }

        # =========================================================================
        # TIER 4: Hợp lệ -> Cho phép đi tiếp vào RAG / Visual / Web Search
        # =========================================================================
        latency_ms = round((time.time() - t0) * 1000, 2)
        return {
            "handled": False,
            "action": "pass",
            "answer": None,
            "reason": "Câu hỏi hợp lệ, chuyển tiếp sang Não bộ RAG / Web Search",
            "latency_ms": latency_ms
        }
