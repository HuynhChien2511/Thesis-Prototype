"""
Kiểm thử Unit Test tự động cho Module Guardrail & Intent Filter (Hàng rào an toàn & Bộ lọc ý định).
Được tích hợp vào unittest framework để tự động phát hiện và chạy qua 'unittest discover'.

Bao gồm các nhóm kiểm thử:
  1. Lọc rác âm thanh & tiếng đệm Whisper (Noise & Filler words).
  2. Chặn ngôn từ thô tục / xúc phạm (Profanity / Toxicity).
  3. Phản hồi tán gẫu & định hình nhân cách (Persona Chit-chat & Small Talk).
  4. Từ chối yêu cầu ngoài phạm vi dịch vụ công (Out-of-Scope Deflection).
  5. Cho phép câu hỏi hợp lệ đi tiếp (Thủ tục hành chính, Tiện ích thời tiết, Thị giác VQA).
  6. Kiểm thử độ trễ cực thấp (Sub-millisecond latency benchmark < 1.0ms).
  7. Kiểm thử các ca biên (Boundary & Case Sensitivity).
"""

import sys
import time
import unittest
from pathlib import Path

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

from src.rag.guardrail import GuardrailManager


class TestGuardrailIntentFilter(unittest.TestCase):
    """Bộ kiểm thử đơn vị cho Hàng rào An toàn Guardrail & Bộ lọc Ý định."""

    @classmethod
    def setUpClass(cls):
        cls.guardrail = GuardrailManager()

    def test_1_noise_and_filler_filtering(self):
        """Kiểm tra nhận diện và xử lý các tiếng ồn, từ đệm của Whisper STT."""
        noise_samples = [
            "",
            "alo",
            "ừm",
            "test mic",
            "hahahahahaha"
        ]
        for query in noise_samples:
            res = self.guardrail.evaluate(query)
            self.assertTrue(
                res["handled"],
                f"Truy vấn rác '{query}' phải được đánh dấu handled=True"
            )
            self.assertEqual(
                res["action"],
                "noise",
                f"Truy vấn rác '{query}' phải có action='noise', nhận được: {res['action']}"
            )
            self.assertIsNotNone(res["answer"])

    def test_2_profanity_and_toxicity_blocking(self):
        """Kiểm tra chặn các từ ngữ xúc phạm, thô tục và trả lời cảnh báo lịch sự."""
        profanity_samples = [
            "đồ ngu",
            "cút đi robot",
            "nói cái gì thế thằng khùng",
            "đồ ngu ngốc",
            "óc chó thật sự"
        ]
        for query in profanity_samples:
            res = self.guardrail.evaluate(query)
            self.assertTrue(
                res["handled"],
                f"Truy vấn xúc phạm '{query}' phải được handled=True"
            )
            self.assertEqual(
                res["action"],
                "profanity",
                f"Truy vấn xúc phạm '{query}' phải có action='profanity', nhận được: {res['action']}"
            )
            self.assertGreater(len(res["answer"]), 0, "Phải có câu trả lời lịch thiệp nhắc nhở")
            self.assertIn("văn minh", res["answer"].lower())

    def test_3_persona_chitchat_handling(self):
        """Kiểm tra phản hồi nhanh các câu hỏi danh tính, chào hỏi và tán gẫu xã giao."""
        chitchat_cases = [
            ("bạn là ai", "identity"),
            ("bạn tên gì vậy", "identity"),
            ("bạn có người yêu chưa", "flirting"),
            ("hát cho tôi nghe một bài đi", "entertainment"),
            ("robot thông minh quá", "compliment"),
            ("xin chào robot", "greeting")
        ]
        for query, _ in chitchat_cases:
            res = self.guardrail.evaluate(query)
            self.assertTrue(
                res["handled"],
                f"Tán gẫu '{query}' phải được handled=True"
            )
            self.assertEqual(
                res["action"],
                "chitchat",
                f"Tán gẫu '{query}' phải có action='chitchat', nhận được: {res['action']}"
            )
            self.assertGreater(len(res["answer"]), 5, f"Câu trả lời cho '{query}' không được rỗng")

    def test_4_out_of_scope_deflection(self):
        """Kiểm tra từ chối khéo léo các yêu cầu nằm ngoài phạm vi hành chính công."""
        deflection_samples = [
            "chỉ tôi cách nấu bún bò Huế ngon",
            "hướng dẫn chơi game liên quân",
            "giải phương trình bậc 2 giúp tôi",
            "xem bói tử vi cho tôi năm nay",
            "viết code giải phương trình giúp tôi"
        ]
        for query in deflection_samples:
            res = self.guardrail.evaluate(query)
            self.assertTrue(
                res["handled"],
                f"Câu hỏi ngoài phạm vi '{query}' phải được handled=True"
            )
            self.assertEqual(
                res["action"],
                "deflect",
                f"Câu hỏi ngoài phạm vi '{query}' phải có action='deflect', nhận được: {res['action']}"
            )
            self.assertIn("chuyên trách", res["answer"].lower())

    def test_5_valid_queries_passthrough(self):
        """Kiểm tra cho phép các câu hỏi hợp lệ đi tiếp vào Pipeline RAG/Vision."""
        valid_queries = [
            "Làm căn cước công dân cần những giấy tờ gì?",
            "Thủ tục đăng ký kết hôn với người nước ngoài như thế nào?",
            "Thời tiết hôm nay như thế nào?",
            "Nhìn xem trước mặt tôi có giấy tờ gì?",
            "Đăng ký thường trú về nhà mới cần hồ sơ gì?",
            "Lệ phí cấp đổi giấy phép lái xe ô tô là bao nhiêu?"
        ]
        for query in valid_queries:
            res = self.guardrail.evaluate(query)
            self.assertFalse(
                res["handled"],
                f"Câu hỏi hợp lệ '{query}' KHÔNG được chặn (handled phải là False)"
            )
            self.assertEqual(
                res["action"],
                "pass",
                f"Câu hỏi hợp lệ '{query}' phải có action='pass', nhận được: {res['action']}"
            )

    def test_6_submillisecond_latency_benchmark(self):
        """Kiểm tra độ trễ xử lý của bộ lọc Guardrail phải đạt tốc độ siêu tốc (< 1.0ms trung bình)."""
        benchmark_queries = [
            "alo",
            "đồ ngu",
            "bạn tên gì",
            "chỉ tôi nấu bún bò",
            "làm căn cước công dân hết bao nhiêu tiền",
            "hướng dẫn thủ tục đăng ký tạm trú",
            "xin chào robot"
        ]
        
        # Warm-up
        for q in benchmark_queries:
            self.guardrail.evaluate(q)

        # Chạy 100 lần lặp
        iterations = 100
        start_time = time.perf_counter()
        for _ in range(iterations):
            for q in benchmark_queries:
                self.guardrail.evaluate(q)
        total_time_ms = (time.perf_counter() - start_time) * 1000.0
        avg_latency_ms = total_time_ms / (iterations * len(benchmark_queries))

        print(f"\n⚡ [GUARDRAIL BENCHMARK]: Độ trễ trung bình = {avg_latency_ms:.3f} ms / truy vấn")
        self.assertLess(
            avg_latency_ms,
            1.0,
            f"Độ trễ trung bình Guardrail phải < 1.0ms, thực tế đo được: {avg_latency_ms:.3f}ms"
        )

    def test_7_case_and_boundary_cases(self):
        """Kiểm tra tính bền vững với chữ HOA, dấu hỏi và dấu câu."""
        test_pairs = [
            ("BẠN LÀ AI???", "chitchat"),
            ("ĐỒ NGU!", "profanity"),
            ("ALO", "noise"),
            ("CÁCH NẤU BÚN BÒ HUẾ", "deflect"),
            ("HƯỚNG DẪN CHƠI GAME LIÊN QUÂN...", "deflect")
        ]
        for query, expected_action in test_pairs:
            res = self.guardrail.evaluate(query)
            self.assertEqual(
                res["action"],
                expected_action,
                f"Đầu vào '{query}' phải nhận diện đúng action='{expected_action}', nhận: '{res['action']}'"
            )


if __name__ == "__main__":
    unittest.main()
