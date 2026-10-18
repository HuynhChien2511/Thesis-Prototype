"""
Tập lệnh kiểm thử Module Text-to-Speech (TTS) - Sprint 3.
- Kiểm tra tính năng chuẩn hóa văn bản
- Đo lường thời gian tổng hợp giọng nói (TTS latency)
- Phát âm thanh ra loa ngoài laptop với cả giọng Nữ (Hoài My) và giọng Nam (Nam Minh)
"""
import sys
import time
from pathlib import Path

# Thêm thư mục prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

# Đảm bảo UTF-8 console trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from src.audio.tts import TextToSpeech
from src.config import TTS_VOICE

SAMPLE_ADMIN_TEXT = """
Chào Quý công dân, để thực hiện thủ tục đăng ký tạm trú, bạn cần chuẩn bị:
1. Tờ khai thay đổi thông tin cư trú (**Mẫu CT01**).
2. Hợp đồng thuê nhà hoặc Giấy chứng nhận quyền sở hữu chỗ ở hợp pháp.
Bạn có thể xuất trình thẻ **CCCD** gắn chip hoặc tài khoản **VNeID** mức 2.
Nộp trực tiếp tại Công an xã/phường hoặc qua Cổng **dichvucong.gov.vn**.
Thời hạn giải quyết là 03 ngày làm việc kể từ ngày nhận đủ hồ sơ hợp lệ.
"""

def test_tts_pipeline(voice_name: str, label: str):
    print("\n" + "=" * 70)
    print(f" KIỂM THỬ GIỌNG NÓI: {label} ({voice_name}) ")
    print("=" * 70)
    
    tts = TextToSpeech(voice=voice_name)
    
    print("[1/3] Văn bản đầu vào từ Não bộ RAG:")
    print(SAMPLE_ADMIN_TEXT.strip())
    
    print("\n[2/3] Đang chuẩn hóa văn bản và tổng hợp giọng nói...")
    res = tts.synthesize(SAMPLE_ADMIN_TEXT)
    
    print("\n[+] Văn bản đã được phiên âm cho giọng đọc:")
    print(f"    \"{res['cleaned_text']}\"")
    print(f"[+] Thời gian tạo âm thanh (TTS Latency): {res['latency_sec']} giây")
    print(f"[+] File âm thanh đã lưu: {res['audio_path']}")
    
    print(f"\n[3/3] 🔊 Đang phát giọng đọc ra Loa ngoài ({label})...")
    tts.play(res["audio_path"], block=True)
    print("[+] Phát hoàn tất.")
    print("-" * 70)


def main():
    print("=" * 70)
    print(" BẮT ĐẦU KIỂM THỬ HỆ THỐNG TEXT-TO-SPEECH (SPRINT 3) ")
    print("=" * 70)
    
    # 1. Chạy với giọng mặc định đã chọn trong cấu hình
    test_tts_pipeline(TTS_VOICE, "Giọng cấu hình mặc định")

    # 2. Hướng dẫn người dùng thử nghiệm đổi giọng
    alt_voice = "vi-VN-NamMinhNeural" if "HoaiMy" in TTS_VOICE else "vi-VN-HoaiMyNeural"
    alt_label = "Giọng Nam (Nam Minh)" if "NamMinh" in alt_voice else "Giọng Nữ (Hoài My)"
    
    print(f"\n[💡 GỢI Ý]: Để thử giọng đối ứng {alt_label}, bạn có thể chạy:")
    print(f"  python test_tts.py --voice {alt_voice}")
    print("=" * 70)


if __name__ == "__main__":
    if "--voice" in sys.argv:
        idx = sys.argv.index("--voice")
        if idx + 1 < len(sys.argv):
            custom_voice = sys.argv[idx + 1]
            test_tts_pipeline(custom_voice, f"Tùy chọn {custom_voice}")
        else:
            main()
    else:
        main()
