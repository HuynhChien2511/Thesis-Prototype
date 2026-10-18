"""
Điểm khởi chạy chính (Entry Point) của Prototype Trợ lý AI Hành chính công.
Tích hợp trọn gói 4 Sprint:
  - Sprint 1: Não bộ tri thức (RAG + ChromaDB + Gemini LLM)
  - Sprint 2: Đôi tai thính nhạy (Microphone + Faster-Whisper GPU)
  - Sprint 3: Khuôn miệng phát thanh (Text Normalizer + Edge-TTS)
  - Sprint 4: Trái tim điều phối (Pipeline toàn trình End-to-End)
"""
import sys
import argparse
from pathlib import Path

# Thêm thư mục prototype vào sys.path để import thuận tiện
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

# Đảm bảo in tiếng Việt chuẩn trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from src.config import (
    LLM_PROVIDER,
    GEMINI_MODEL,
    WHISPER_MODEL,
    WHISPER_DEVICE,
    TTS_VOICE,
    SIMILARITY_THRESHOLD,
    DATA_DIR,
    VECTOR_DB_DIR
)
from src.pipeline import VoiceAgentPipeline


BANNER = """
================================================================================
      HỆ THỐNG TRỢ LÝ AI TƯ VẤN DỊCH VỤ HÀNH CHÍNH CÔNG VIỆT NAM
              (Đề tài tốt nghiệp: AI Robot tương tác giọng nói)
================================================================================
  🧠 Mô hình LLM          : {llm_provider} ({gemini_model})
  🎧 Nhận diện tiếng nói  : Faster-Whisper ({whisper_model}) trên [{whisper_device}]
  🗣️  Tổng hợp giọng nói   : Edge-TTS ({tts_voice})
  📚 Cơ sở dữ liệu RAG    : ChromaDB ({vector_dir})
  🛡️  Ngưỡng chống ảo giác: {threshold} (Nghiêm ngặt trích dẫn Điều/Khoản)
================================================================================
""".format(
    llm_provider=LLM_PROVIDER.upper(),
    gemini_model=GEMINI_MODEL,
    whisper_model=WHISPER_MODEL,
    whisper_device=WHISPER_DEVICE.upper(),
    tts_voice=TTS_VOICE,
    vector_dir=VECTOR_DB_DIR.name,
    threshold=SIMILARITY_THRESHOLD
)


def run_automated_demo(pipeline: VoiceAgentPipeline):
    """Chạy kịch bản tự động một câu hỏi mẫu để chứng minh luồng hoạt động."""
    sample_question = "Làm thẻ căn cước cho trẻ dưới 14 tuổi thì cần làm những gì?"
    print("\n" + "=" * 70)
    print(" [DEMO TỰ ĐỘNG]: THỬ NGHIỆM TRUY VẤN VĂN BẢN VÀ PHÁT RA LOA ")
    print(f"[*] Câu hỏi mẫu: \"{sample_question}\"")
    print("=" * 70)
    
    res = pipeline.process_text(sample_question, speak=True)
    pipeline.print_latency_summary(res["latency"])
    print("\n[SUCCESS] Hoàn thành lượt chạy Demo tự động!")


def print_menu():
    """Hiển thị menu lựa chọn phương thức tương tác."""
    print("\n" + "-" * 50)
    print("  XIN MỜI CHỌN CHẾ ĐỘ HOẠT ĐỘNG:")
    print("  [1] Tương tác giọng nói: Push-to-Talk (Mặc định - Nhấn Enter để nói)")
    print("  [2] Tương tác giọng nói: VAD (Tự động nhận diện khi cất lời)")
    print("  [3] Chế độ gõ phím: Nhập câu hỏi từ bàn phím (Dự phòng khi ồn)")
    print("  [4] Chạy Demo tự động (Kiểm tra nhanh 1 câu hỏi mẫu)")
    print("  [5] Thoát hệ thống")
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(description="Prototype Trợ lý AI Robot Hành chính công")
    parser.add_argument(
        "--mode",
        choices=["ptt", "vad", "text", "auto"],
        help="Chế độ khởi chạy trực tiếp: ptt (Push-to-Talk), vad (Tự động), text (Gõ phím), auto (Demo mẫu)"
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Tắt âm thanh phát ra loa (chỉ in câu trả lời dạng văn bản)"
    )
    args = parser.parse_args()

    print(BANNER)
    
    # Khởi tạo Pipeline tích hợp toàn trình
    tts_enabled = not args.no_tts
    pipeline = VoiceAgentPipeline(record_mode="ptt", tts_enabled=tts_enabled)

    # Nếu người dùng truyền tham số trực tiếp qua dòng lệnh
    if args.mode:
        if args.mode == "ptt":
            pipeline.run_interactive_voice(mode="ptt")
        elif args.mode == "vad":
            pipeline.run_interactive_voice(mode="vad")
        elif args.mode == "text":
            pipeline.run_interactive_text()
        elif args.mode == "auto":
            run_automated_demo(pipeline)
        return

    # Nếu không có tham số, hiển thị Menu tương tác thân thiện
    while True:
        print_menu()
        try:
            choice = input("👉 Nhập lựa chọn của bạn (1-5): ").strip()
            if choice == "1":
                pipeline.run_interactive_voice(mode="ptt")
            elif choice == "2":
                pipeline.run_interactive_voice(mode="vad")
            elif choice == "3":
                pipeline.run_interactive_text()
            elif choice == "4":
                run_automated_demo(pipeline)
            elif choice in ["5", "q", "exit", "quit"]:
                print("\n[+] Đã thoát hệ thống. Cảm ơn bạn!")
                break
            else:
                print("[!] Lựa chọn không hợp lệ. Vui lòng nhập từ 1 đến 5.")
        except KeyboardInterrupt:
            print("\n[!] Đã đóng ứng dụng.")
            break


if __name__ == "__main__":
    main()
