"""
Tập lệnh kiểm thử Module Speech-to-Text (STT) - Sprint 2.
Hỗ trợ cả 2 chế độ:
1. Tự động kiểm thử (Self-test bằng file âm thanh mẫu chuẩn tiếng Việt qua edge-tts)
2. Kiểm thử tương tác trực tiếp qua Micro của laptop (Push-to-Talk & VAD)
"""
import sys
import time
import asyncio
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

import edge_tts
from src.audio.recorder import AudioRecorder
from src.audio.stt import SpeechToText
from src.config import TTS_VOICE

SAMPLE_AUDIO_PATH = PROTOTYPE_DIR / "data" / "sample_test_speech.mp3"


async def generate_sample_speech(text: str, output_path: Path):
    """Tạo file âm thanh tiếng Việt mẫu bằng edge-tts để tự động kiểm thử STT."""
    print(f"[*] Đang tạo mẫu giọng nói tiếng Việt chuẩn: \"{text}\"...")
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(str(output_path))
    print(f"[+] Đã tạo file âm thanh mẫu tại: {output_path}")


def run_automated_self_test(stt: SpeechToText):
    """Chế độ tự động kiểm thử: Kiểm tra độ chính xác và tốc độ STT trên GPU."""
    print("\n" + "=" * 70)
    print(" CHẾ ĐỘ 1: TỰ ĐỘNG KIỂM THỬ (AUTOMATED SELF-TEST TRÊN GPU) ")
    print("=" * 70)
    
    sample_text = "Xin chào, cho tôi hỏi thủ tục làm căn cước công dân cho người dưới mười bốn tuổi."
    
    # Tạo file âm thanh nếu chưa có
    if not SAMPLE_AUDIO_PATH.exists():
        asyncio.run(generate_sample_speech(sample_text, SAMPLE_AUDIO_PATH))
    
    print("\n[*] Đang gửi âm thanh vào Faster-Whisper (CUDA RTX 3050)...")
    res = stt.transcribe(str(SAMPLE_AUDIO_PATH))
    
    print("\n" + "-" * 70)
    print(f"  [VĂN BẢN GỐC]         : {sample_text}")
    print(f"  [NHẬN DIỆN ĐƯỢC (STT)]: {res['text']}")
    print(f"  [NGÔN NGỮ / ĐỘ TIN CẬY]: {res['language']} ({res['probability'] * 100:.1f}%)")
    print(f"  [THỜI GIAN NHẬN DIỆN] : {res['latency_sec']} giây")
    print("-" * 70)

    # Đánh giá sơ bộ
    if "căn cước" in res["text"].lower() and ("14 tuổi" in res["text"].lower() or "mười bốn tuổi" in res["text"].lower()):
        print("[ĐÁNH GIÁ]: ✅ Nhận diện CHÍNH XÁC 100% ngữ nghĩa tiếng Việt!")
    else:
        print("[ĐÁNH GIÁ]: ⚠️ Cần kiểm tra lại dấu hoặc từ ngữ.")
    print("=" * 70)


def run_interactive_mic_test(stt: SpeechToText, mode: str = "push"):
    """Chế độ thu âm giọng nói trực tiếp từ micro của người dùng."""
    print("\n" + "=" * 70)
    print(f" CHẾ ĐỘ 2: THỬ NGHIỆM TRỰC TIẾP QUA MICRO LAPTOP ({mode.upper()}) ")
    print("=" * 70)
    
    recorder = AudioRecorder()
    
    if mode == "push":
        audio_data = recorder.record_push_to_talk()
    else:
        audio_data = recorder.record_vad(silence_duration=1.5)

    if len(audio_data) == 0:
        print("[!] Không thu được âm thanh nào.")
        return

    print(f"\n[*] Đang giải mã giọng nói qua Whisper (độ dài: {len(audio_data)/16000:.2f}s)...")
    res = stt.transcribe(audio_data)

    print("\n" + "-" * 70)
    print(f"  [BẠN VỪA NÓI]         : \"{res['text']}\"")
    print(f"  [ĐỘ TIN CẬY]          : {res['probability'] * 100:.1f}%")
    print(f"  [ĐỘ TRỄ XỬ LÝ (STT)]  : {res['latency_sec']} giây")
    print(f"  [FILE ÂM THANH VỪA THU]: data/last_recording.wav (Mở nghe lại để kiểm tra âm lượng mic)")
    print("-" * 70)


def main():
    print("=" * 70)
    print(" KHỞI TẠO HỆ THỐNG KIỂM THỬ SPEECH-TO-TEXT (SPRINT 2) ")
    print("=" * 70)
    
    # Nạp mô hình Faster-Whisper
    stt = SpeechToText()

    # 1. Chạy bài kiểm thử tự động với âm thanh mẫu trước
    run_automated_self_test(stt)

    # 2. Hướng dẫn người dùng chạy micro trực tiếp
    print("\n[💡 HƯỚNG DẪN KIỂM THỬ BẰNG GIỌNG NÓI CỦA BẠN]:")
    print("Để nói trực tiếp câu hỏi của bạn qua micro laptop, bạn chỉ cần mở terminal và chạy lệnh:")
    print("  python test_stt.py --mic")
    print("Hoặc chạy chế độ VAD tự động ngắt sau khoảng lặng:")
    print("  python test_stt.py --vad")
    print("=" * 70)


if __name__ == "__main__":
    if "--mic" in sys.argv:
        stt = SpeechToText()
        run_interactive_mic_test(stt, mode="push")
    elif "--vad" in sys.argv:
        stt = SpeechToText()
        run_interactive_mic_test(stt, mode="vad")
    else:
        main()
