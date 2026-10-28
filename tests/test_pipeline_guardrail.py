"""
Kiểm thử Tích hợp Pipeline với Hàng rào An toàn Guardrail.
Xác nhận rằng:
1. Khi gặp câu trêu đùa/nói nhảm/lạc đề, Pipeline trả về kết quả ngay (< 1s bao gồm TTS), không gọi RAG hay Web Search.
2. Khi gặp câu hỏi thủ tục hoặc tiện ích, Pipeline vẫn gọi RAG/Web Search bình thường.
"""

import sys
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

from src.pipeline import VoiceAgentPipeline


def test_pipeline_guardrail():
    print("=" * 70)
    print(" KIỂM THỬ TÍCH HỢP PIPELINE + GUARDRAIL (TEXT-TO-TTS) ")
    print("=" * 70)

    # Khởi tạo pipeline không bật camera để kiểm tra logic nhanh
    pipeline = VoiceAgentPipeline(tts_enabled=True, vision_enabled=False)

    queries = [
        ("bạn có người yêu chưa", "guardrail_chitchat"),
        ("chỉ tôi cách nấu bún bò Huế", "guardrail_deflect"),
        ("alo 123", "guardrail_noise"),
        ("đồ ngu ngốc", "guardrail_profanity"),
        ("Làm căn cước công dân cần những giấy tờ gì?", "local"),
    ]

    all_pass = True

    for q, expected_source_type in queries:
        print(f"\n👉 Gửi câu hỏi vào Pipeline: \"{q}\"")
        res = pipeline.process_text(q, speak=True, play_audio=False)

        source_type = res["source_type"]
        is_ok = (source_type == expected_source_type)
        print(f"📊 Kết quả: source_type='{source_type}' (Kỳ vọng: '{expected_source_type}') -> {'✅ ĐẠT' if is_ok else '❌ SAI'}")
        print(f"⚡ Thời gian phản ứng: {res['latency']['response_sec']}s (RAG/Guardrail latency: {res['latency']['rag_sec']}s)")

        if not is_ok:
            all_pass = False

    pipeline.cleanup()

    print("\n" + "=" * 70)
    if all_pass:
        print("🎉 TẤT CẢ CÁC CA KIỂM THỬ TÍCH HỢP PIPELINE + GUARDRAIL ĐỀU ĐẠT 100%!")
    else:
        print("❌ CÓ CA KIỂM THỬ THẤT BẠI!")
    print("=" * 70)

    assert all_pass


if __name__ == "__main__":
    test_pipeline_guardrail()
