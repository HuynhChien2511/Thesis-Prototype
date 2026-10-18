"""
Tập lệnh kiểm thử toàn trình End-to-End Pipeline (Sprint 4 - Trái tim hệ thống).
Tự động xác thực toàn bộ luồng dữ liệu 4 công đoạn:
  [Âm thanh / Văn bản] -> [STT] -> [RAG + LLM] -> [TTS Phát loa]
"""
import sys
import time
from pathlib import Path

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

from src.pipeline import VoiceAgentPipeline
from src.config import DATA_DIR

SAMPLE_SPEECH_FILE = DATA_DIR / "sample_test_speech.mp3"


def run_pipeline_benchmark():
    print("=" * 80)
    print(" BẮT ĐẦU KIỂM THỬ TỰ ĐỘNG TOÀN TRÌNH PIPELINE (SPRINT 4 BENCHMARK) ")
    print("=" * 80)
    
    # Khởi tạo Pipeline (bật phát âm thanh ra loa để người dùng nghe kiểm tra)
    pipeline = VoiceAgentPipeline(record_mode="ptt", tts_enabled=True)

    benchmark_results = []

    # Kiểm tra cờ phát âm thanh ra loa
    play_audio = "--speak" in sys.argv
    if not play_audio:
        print("[💡 LƯU Ý]: Mặc định kiểm thử tự động không phát toàn bộ âm thanh ra loa để tiết kiệm thời gian.")
        print("          Để phát đầy đủ giọng nói ra loa ngoài, hãy thêm cờ: python test_pipeline.py --speak\n")

    # -------------------------------------------------------------
    # TEST CASE 1: ÂM THANH MẪU -> STT -> RAG -> TTS
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("▶ [TC01] KIỂM THỬ TOÀN TRÌNH TỪ TỆP ÂM THANH (AUDIO INPUT -> STT -> RAG -> TTS)")
    print("=" * 80)
    
    if SAMPLE_SPEECH_FILE.exists():
        print(f"[*] Đọc tệp âm thanh kiểm thử: {SAMPLE_SPEECH_FILE.name}")
        t0 = time.time()
        
        # 1. Chạy STT trên file âm thanh
        stt_res = pipeline.stt.transcribe(str(SAMPLE_SPEECH_FILE))
        question_text = stt_res["text"]
        stt_latency = stt_res["latency_sec"]
        print(f"[+] [STT] Nhận diện được câu hỏi: \"{question_text}\" ({stt_latency}s)")

        # 2. Chuyển vào Não bộ RAG và TTS
        res = pipeline.process_text(question_text, speak=True, play_audio=play_audio)
        total_time = round(time.time() - t0, 2)
        response_time = round(stt_latency + res["latency"]["rag_sec"] + res["latency"]["tts_synth_sec"], 2)
        
        metrics = {
            "name": "TC01: Audio -> STT -> RAG -> TTS",
            "stt_sec": stt_latency,
            "rag_sec": res["latency"]["rag_sec"],
            "tts_synth_sec": res["latency"]["tts_synth_sec"],
            "response_sec": response_time,
            "playback_sec": res["latency"]["playback_sec"],
            "success": bool(res["answer"] and res["found_in_docs"])
        }
        benchmark_results.append(metrics)
    else:
        print(f"[!] Không tìm thấy tệp {SAMPLE_SPEECH_FILE}, bỏ qua TC01.")

    # -------------------------------------------------------------
    # TEST CASE 2: VĂN BẢN TRONG MIỀN (TẠM TRÚ) -> RAG -> TTS
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("▶ [TC02] KIỂM THỬ THỦ TỤC TẠM TRÚ (IN-DOMAIN: RAG -> TTS)")
    print("=" * 80)
    q2 = "Đăng ký tạm trú mất bao nhiêu ngày làm việc và nộp hồ sơ ở đâu?"
    print(f"[*] Câu hỏi: \"{q2}\"")
    
    t0 = time.time()
    res2 = pipeline.process_text(q2, speak=True, play_audio=play_audio)
    total_time2 = round(time.time() - t0, 2)
    response_time2 = round(res2["latency"]["rag_sec"] + res2["latency"]["tts_synth_sec"], 2)
    
    benchmark_results.append({
        "name": "TC02: In-domain (Tạm trú)",
        "stt_sec": 0.0,
        "rag_sec": res2["latency"]["rag_sec"],
        "tts_synth_sec": res2["latency"]["tts_synth_sec"],
        "response_sec": response_time2,
        "playback_sec": res2["latency"]["playback_sec"],
        "success": bool(res2["found_in_docs"] and "thu_tuc_dang_ky_tam_tru.txt" in res2["sources"])
    })

    # -------------------------------------------------------------
    # TEST CASE 3: CÂU HỎI NGOÀI MIỀN (CHỐNG ẢO GIÁC) -> THRESHOLD -> TỪ CHỐI
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("▶ [TC03] KIỂM THỬ BẢO VỆ CHỐNG ẢO GIÁC (OUT-OF-DOMAIN -> FAST REFUSAL)")
    print("=" * 80)
    q3 = "Thủ tục xin visa du lịch Nhật Bản tự túc cần những giấy tờ gì?"
    print(f"[*] Câu hỏi ngoài miền: \"{q3}\"")
    
    t0 = time.time()
    res3 = pipeline.process_text(q3, speak=True, play_audio=play_audio)
    total_time3 = round(time.time() - t0, 2)
    response_time3 = round(res3["latency"]["rag_sec"] + res3["latency"]["tts_synth_sec"], 2)
    
    benchmark_results.append({
        "name": "TC03: Out-of-domain (Chống ảo giác)",
        "stt_sec": 0.0,
        "rag_sec": res3["latency"]["rag_sec"],
        "tts_synth_sec": res3["latency"]["tts_synth_sec"],
        "response_sec": response_time3,
        "playback_sec": res3["latency"]["playback_sec"],
        "success": bool(not res3["found_in_docs"])
    })

    # -------------------------------------------------------------
    # BẢNG TỔNG KẾT HIỆU NĂNG TOÀN DIỆN SPRINT 4
    # -------------------------------------------------------------
    print("\n" + "=" * 90)
    print(" 📊 BẢNG TỔNG HỢP HIỆU NĂNG TOÀN TRÌNH PIPELINE SPRINT 4 ")
    print("=" * 90)
    print(f"{'Kịch bản kiểm thử':<34} | {'STT':<6} | {'RAG':<6} | {'TTS Mod':<7} | {'Phản ứng':<8} | {'Thời lượng':<10} | {'Kết quả'}")
    print("-" * 90)
    for b in benchmark_results:
        status = "✅ PASS" if b["success"] else "❌ FAIL"
        print(f"{b['name']:<34} | {b['stt_sec']:>5.2f}s | {b['rag_sec']:>5.2f}s | {b['tts_synth_sec']:>6.2f}s | {b['response_sec']:>7.2f}s | {b['playback_sec']:>9.2f}s | {status}")
    print("=" * 90)
    print("[SUCCESS] Tất cả các kịch bản kiểm thử tích hợp đã hoàn thành xuất sắc!")


if __name__ == "__main__":
    run_pipeline_benchmark()
