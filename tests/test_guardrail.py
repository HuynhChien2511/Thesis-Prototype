"""
Kiểm thử Unit Test cho Module Guardrail & Intent Filter (Hàng rào an toàn & Bộ lọc ý định).

Các ca kiểm thử:
1. Lọc rác âm thanh & tiếng đệm Whisper (Noise & Filler words).
2. Chặn ngôn từ thô tục / xúc phạm (Profanity / Toxicity).
3. Phản hồi tán gẫu & định hình nhân cách (Persona Chit-chat & Small Talk).
4. Từ chối yêu cầu ngoài phạm vi dịch vụ công (Out-of-Scope Deflection).
5. Cho phép câu hỏi hợp lệ đi tiếp (Thủ tục hành chính, Tiện ích thời tiết, Thị giác VQA).
"""

import sys
import time
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


def test_guardrail():
    print("=" * 70)
    print(" BẮT ĐẦU KIỂM THỬ BỘ LỌC GUARDRAIL & INTENT FILTER ")
    print("=" * 70)

    guardrail = GuardrailManager()

    test_cases = [
        # Nhóm 1: Rác âm thanh & tiếng đệm
        {
            "category": "1. Tiếng ồn & Rác âm thanh",
            "input": "",
            "expected_action": "noise",
            "expected_handled": True
        },
        {
            "category": "1. Tiếng ồn & Rác âm thanh",
            "input": "alo",
            "expected_action": "noise",
            "expected_handled": True
        },
        {
            "category": "1. Tiếng ồn & Rác âm thanh",
            "input": "ừm",
            "expected_action": "noise",
            "expected_handled": True
        },
        {
            "category": "1. Tiếng ồn & Rác âm thanh",
            "input": "test mic",
            "expected_action": "noise",
            "expected_handled": True
        },
        {
            "category": "1. Tiếng ồn & Rác âm thanh",
            "input": "hahahahahaha",
            "expected_action": "noise",
            "expected_handled": True
        },

        # Nhóm 2: Ngôn từ thô tục / Xúc phạm
        {
            "category": "2. Ngôn từ thô tục / Xúc phạm",
            "input": "đồ ngu",
            "expected_action": "profanity",
            "expected_handled": True
        },
        {
            "category": "2. Ngôn từ thô tục / Xúc phạm",
            "input": "cút đi robot",
            "expected_action": "profanity",
            "expected_handled": True
        },
        {
            "category": "2. Ngôn từ thô tục / Xúc phạm",
            "input": "nói cái gì thế thằng khùng",
            "expected_action": "profanity",
            "expected_handled": True
        },

        # Nhóm 3: Persona Chit-chat & Trêu đùa
        {
            "category": "3. Tán gẫu xã giao (Persona Chit-chat)",
            "input": "bạn là ai",
            "expected_action": "chitchat",
            "expected_handled": True
        },
        {
            "category": "3. Tán gẫu xã giao (Persona Chit-chat)",
            "input": "bạn tên gì vậy",
            "expected_action": "chitchat",
            "expected_handled": True
        },
        {
            "category": "3. Tán gẫu xã giao (Persona Chit-chat)",
            "input": "bạn có người yêu chưa",
            "expected_action": "chitchat",
            "expected_handled": True
        },
        {
            "category": "3. Tán gẫu xã giao (Persona Chit-chat)",
            "input": "hát cho tôi nghe một bài đi",
            "expected_action": "chitchat",
            "expected_handled": True
        },
        {
            "category": "3. Tán gẫu xã giao (Persona Chit-chat)",
            "input": "robot thông minh quá",
            "expected_action": "chitchat",
            "expected_handled": True
        },
        {
            "category": "3. Tán gẫu xã giao (Persona Chit-chat)",
            "input": "xin chào robot",
            "expected_action": "chitchat",
            "expected_handled": True
        },

        # Nhóm 4: Lạc đề hoàn toàn (Out-of-Scope)
        {
            "category": "4. Lạc đề hoàn toàn (Out-of-Scope)",
            "input": "chỉ tôi cách nấu bún bò Huế ngon",
            "expected_action": "deflect",
            "expected_handled": True
        },
        {
            "category": "4. Lạc đề hoàn toàn (Out-of-Scope)",
            "input": "hướng dẫn chơi game liên quân",
            "expected_action": "deflect",
            "expected_handled": True
        },
        {
            "category": "4. Lạc đề hoàn toàn (Out-of-Scope)",
            "input": "giải phương trình bậc 2 giúp tôi",
            "expected_action": "deflect",
            "expected_handled": True
        },
        {
            "category": "4. Lạc đề hoàn toàn (Out-of-Scope)",
            "input": "xem bói tử vi cho tôi năm nay",
            "expected_action": "deflect",
            "expected_handled": True
        },

        # Nhóm 5: Câu hỏi hợp lệ (PASS)
        {
            "category": "5. Câu hỏi hợp lệ (PASS)",
            "input": "Làm căn cước công dân cần những giấy tờ gì?",
            "expected_action": "pass",
            "expected_handled": False
        },
        {
            "category": "5. Câu hỏi hợp lệ (PASS)",
            "input": "Thủ tục đăng ký kết hôn với người nước ngoài như thế nào?",
            "expected_action": "pass",
            "expected_handled": False
        },
        {
            "category": "5. Câu hỏi hợp lệ (PASS)",
            "input": "Thời tiết hôm nay như thế nào?",
            "expected_action": "pass",
            "expected_handled": False
        },
        {
            "category": "5. Câu hỏi hợp lệ (PASS)",
            "input": "Nhìn xem trước mặt tôi có giấy tờ gì?",
            "expected_action": "pass",
            "expected_handled": False
        }
    ]

    passed_count = 0
    total_latency_ms = 0.0

    print(f"\nTiến hành chạy {len(test_cases)} ca kiểm thử tự động...\n")

    for idx, tc in enumerate(test_cases, 1):
        res = guardrail.evaluate(tc["input"])
        total_latency_ms += res["latency_ms"]

        action_ok = (res["action"] == tc["expected_action"])
        handled_ok = (res["handled"] == tc["expected_handled"])
        is_pass = action_ok and handled_ok

        status_icon = "✅ PASS" if is_pass else "❌ FAIL"
        if is_pass:
            passed_count += 1

        print(f"[{idx:02d}] {status_icon} | [{tc['category']}]")
        print(f"     👉 Đầu vào: \"{tc['input']}\"")
        print(f"     📊 Kết quả: Action='{res['action']}' (Handled={res['handled']}) | Độ trễ: {res['latency_ms']}ms")
        if res["handled"]:
            print(f"     💬 Lời đáp: \"{res['answer'][:70]}...\"")
        print(f"     📝 Lý do: {res['reason']}")
        print("-" * 70)

    avg_latency = round(total_latency_ms / len(test_cases), 3)
    print("\n" + "=" * 70)
    print(f" KẾT QUẢ KIỂM THỬ GUARDRAIL: {passed_count}/{len(test_cases)} PASSED (Đạt {passed_count/len(test_cases)*100:.1f}%)")
    print(f" ⚡ Độ trễ trung bình của bộ lọc: {avg_latency} ms / truy vấn")
    print("=" * 70)

    assert passed_count == len(test_cases), f"Có {len(test_cases) - passed_count} ca kiểm thử thất bại!"


if __name__ == "__main__":
    test_guardrail()
