"""
Module Pipeline Tích hợp Toàn trình (Sprint 4 - Trái tim hệ thống).
Kết nối 4 module cơ bản:
  1. Thu âm (AudioRecorder: Push-to-Talk / VAD)
  2. Nhận diện giọng nói (SpeechToText: Faster-Whisper GPU)
  3. Não bộ tri thức (AdministrativeRAG: ChromaDB + Gemini LLM)
  4. Khuôn miệng phát âm (TextToSpeech: Edge-TTS + Pygame Mixer)
"""
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Thêm prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

# Đảm bảo UTF-8 console trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import numpy as np

from src.audio.recorder import AudioRecorder
from src.audio.stt import SpeechToText
from src.rag.retriever import AdministrativeRAG
from src.audio.tts import TextToSpeech
from src.config import (
    LLM_PROVIDER,
    GEMINI_MODEL,
    WHISPER_MODEL,
    WHISPER_DEVICE,
    TTS_VOICE,
    SIMILARITY_THRESHOLD
)

# Danh sách từ khóa người dùng muốn kết thúc phiên làm việc
EXIT_KEYWORDS = [
    "tạm biệt", "dừng lại", "kết thúc", "thoát", "nghỉ",
    "dừng", "bye", "hẹn gặp lại", "không còn câu hỏi", "hết rồi",
    "thôi", "cảm ơn"
]


class VoiceAgentPipeline:
    def __init__(
        self,
        record_mode: str = "ptt",
        tts_enabled: bool = True
    ):
        """
        Khởi tạo Pipeline tích hợp toàn trình:
        - record_mode: "ptt" (Push-to-Talk mặc định) hoặc "vad" (Voice Activity Detection)
        - tts_enabled: Bật/tắt phát âm thanh ra loa
        """
        print("=" * 70)
        print(" KHỞI ĐỘNG HỆ THỐNG TRỢ LÝ ROBOT HÀNH CHÍNH CÔNG (SPRINT 4) ")
        print("=" * 70)
        
        self.record_mode = record_mode.lower()
        self.tts_enabled = tts_enabled
        
        # 1. Khởi tạo Đôi tai (Mic Recorder)
        print("[1/4] 🎤 Đang kết nối thiết bị thu âm Microphone...")
        self.recorder = AudioRecorder()
        
        # 2. Khởi tạo Bộ nhận diện giọng nói (STT - Faster-Whisper)
        print(f"[2/4] 🎧 Đang nạp mô hình nhận diện giọng nói ({WHISPER_MODEL.upper()} trên {WHISPER_DEVICE.upper()})...")
        self.stt = SpeechToText()
        
        # 3. Khởi tạo Não bộ pháp lý (RAG - Vector DB + LLM)
        print(f"[3/4] 🧠 Đang kích hoạt Não bộ tri thức (Gemini & ChromaDB, Threshold={SIMILARITY_THRESHOLD})...")
        self.rag = AdministrativeRAG(similarity_threshold=SIMILARITY_THRESHOLD)
        
        # 4. Khởi tạo Khuôn miệng phát âm (TTS - Edge-TTS)
        print(f"[4/4] 🗣️  Đang thiết lập giọng đọc phát âm ({TTS_VOICE})...")
        self.tts = TextToSpeech(voice=TTS_VOICE)
        
        print("=" * 70)
        print("[SUCCESS] Toàn bộ hệ thống Pipeline đã sẵn sàng phục vụ Quý công dân!")
        print("=" * 70)

    def is_exit_command(self, text: str) -> bool:
        """Kiểm tra xem câu nói của người dùng có chứa từ khóa chào tạm biệt / kết thúc không."""
        if not text:
            return False
        clean = text.lower().strip(" .,!?")
        for kw in EXIT_KEYWORDS:
            if kw in clean:
                return True
        return False

    def process_text(self, question: str, speak: bool = True, play_audio: bool = True) -> Dict[str, Any]:
        """
        Xử lý truy vấn từ chuỗi văn bản (dùng cho chế độ Text mode hoặc bước sau STT):
        1. Gửi vào Não bộ RAG (tìm kiếm văn bản + sinh lời đáp)
        2. Tổng hợp file âm thanh TTS
        3. Phát âm thanh ra loa ngoài (nếu play_audio=True) và đo lường chi tiết
        """
        start_time = time.time()
        
        # 1. Truy vấn RAG
        print(f"\n[🧠 NÃO BỘ ĐANG XỬ LÝ] Tìm kiếm văn bản quy định & tổng hợp câu trả lời...")
        rag_res = self.rag.query(question)
        rag_latency = rag_res["latency"]["total_sec"]
        
        answer = rag_res["answer"]
        sources = rag_res["sources"]
        found_in_docs = rag_res["found_in_docs"]
        
        print(f"\n[🤖 TRỢ LÝ PHẢN HỒI]:\n{answer}")
        if sources:
            print(f"\n[📚 NGUỒN CĂN CỨ]: {', '.join(sources)}")
        else:
            print(f"\n[ℹ️ PHẠM VI DỮ LIỆU]: Câu hỏi nằm ngoài cơ sở dữ liệu nội bộ.")

        # 2. Tổng hợp giọng nói TTS
        tts_synth_latency = 0.0
        tts_playback_duration = 0.0
        
        if speak and self.tts_enabled and answer:
            print(f"\n[🗣️ ĐANG TỔNG HỢP GIỌNG ĐỌC] ({self.tts.voice})...")
            synth_res = self.tts.synthesize(answer)
            tts_synth_latency = synth_res["latency_sec"]
            response_time = round(time.time() - start_time, 2)
            
            # Phát âm thanh ra loa nếu play_audio=True
            if play_audio and synth_res["audio_path"] and synth_res["audio_path"].exists():
                print(f"[🔊 BẮT ĐẦU PHÁT RA LOA] (Sau {response_time}s chuẩn bị)...")
                t_play = time.time()
                self.tts.play(synth_res["audio_path"], block=True)
                tts_playback_duration = round(time.time() - t_play, 2)
        else:
            response_time = round(time.time() - start_time, 2)

        total_wall_time = round(time.time() - start_time, 2)
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "found_in_docs": found_in_docs,
            "latency": {
                "rag_sec": rag_latency,
                "tts_sec": tts_synth_latency,
                "tts_synth_sec": tts_synth_latency,
                "response_sec": response_time,
                "playback_sec": tts_playback_duration,
                "total_sec": total_wall_time
            }
        }

    def process_audio(self, audio_data: np.ndarray, speak: bool = True) -> Optional[Dict[str, Any]]:
        """
        Xử lý trọn gói từ tín hiệu âm thanh Micro:
        1. Nhận diện giọng nói STT
        2. Kiểm tra từ khóa thoát
        3. Truy vấn RAG và phát loa TTS
        4. Trả về báo cáo hiệu năng toàn trình
        """
        if len(audio_data) == 0:
            print("[!] Không thu được tín hiệu âm thanh nào.")
            return None

        start_roundtrip = time.time()
        
        # 1. Chuyển giọng nói thành văn bản (STT)
        print("\n[🎧 ĐANG NHẬN DIỆN GIỌNG NÓI] Đưa âm thanh qua Faster-Whisper...")
        stt_res = self.stt.transcribe(audio_data)
        question = stt_res["text"].strip()
        stt_latency = stt_res["latency_sec"]
        
        if not question:
            print("[⚠️ CẢNH BÁO] Không nhận diện được câu hỏi nào từ âm thanh thu được.")
            return None

        print(f"\n[👤 CÔNG DÂN ĐÃ NÓI]: \"{question}\" (Nhận diện trong {stt_latency}s)")

        # 2. Kiểm tra câu lệnh chào tạm biệt / thoát
        if self.is_exit_command(question):
            farewell = "Cảm ơn Quý công dân đã sử dụng dịch vụ hành chính công. Chúc Quý công dân một ngày làm việc hiệu quả và nhiều niềm vui!"
            print(f"\n[🤖 TRỢ LÝ PHẢN HỒI]: {farewell}")
            if speak and self.tts_enabled:
                self.tts.speak(farewell, block=True)
            return {
                "question": question,
                "answer": farewell,
                "is_exit": True,
                "latency": {
                    "stt_sec": stt_latency,
                    "rag_sec": 0.0,
                    "tts_synth_sec": 0.5,
                    "response_sec": round(stt_latency + 0.5, 2),
                    "playback_sec": 5.0,
                    "total_sec": round(time.time() - start_roundtrip, 2)
                }
            }

        # 3. Chuyển tiếp câu hỏi vào RAG và TTS
        res = self.process_text(question, speak=speak)
        res["stt_text"] = question
        res["is_exit"] = False
        res["latency"]["stt_sec"] = stt_latency
        # Tính thời gian phản ứng toàn trình (từ dứt lời đến khi loa bắt đầu phát)
        res["latency"]["response_sec"] = round(stt_latency + res["latency"]["rag_sec"] + res["latency"]["tts_synth_sec"], 2)
        res["latency"]["total_sec"] = round(time.time() - start_roundtrip, 2)
        
        # In bảng đo lường hiệu năng (Latency Benchmark)
        self.print_latency_summary(res["latency"])
        
        return res

    def print_latency_summary(self, latency: Dict[str, float]):
        """In bảng tóm tắt độ trễ các công đoạn một cách trực quan."""
        print("-" * 65)
        print("⏱️  BẢNG ĐO LƯỜNG HIỆU NĂNG TOÀN TRÌNH (LATENCY BENCHMARK)")
        print(f"  • Nhận diện giọng nói (STT)      : {latency.get('stt_sec', 0.0):.2f}s")
        print(f"  • Truy xuất & suy luận RAG (LLM) : {latency.get('rag_sec', 0.0):.2f}s")
        print(f"  • Tổng hợp giọng nói TTS (Model) : {latency.get('tts_synth_sec', 0.0):.2f}s")
        print(f"  ⚡ THỜI GIAN PHẢN ỨNG (Bắt đầu nói): {latency.get('response_sec', 0.0):.2f}s")
        print(f"  🔊 Thời lượng Robot đọc toàn bài : {latency.get('playback_sec', 0.0):.2f}s")
        print("-" * 65)

    def run_interactive_voice(self, mode: Optional[str] = None):
        """
        Vòng lặp hội thoại giọng nói 2 chiều liên tục:
        - Người dân nói câu hỏi -> Robot lắng nghe -> Trả lời bằng giọng nói
        - Lặp lại cho đến khi người dùng nói 'tạm biệt' hoặc bấm Ctrl+C
        """
        active_mode = (mode or self.record_mode).lower()
        mode_label = "Push-to-Talk (Nhấn Enter)" if active_mode == "ptt" else "VAD (Tự động ngắt theo khoảng lặng)"
        
        print("\n" + "=" * 70)
        print(f" BẮT ĐẦU PHIÊN HỘI THOẠI GIỌNG NÓI [{mode_label.upper()}] ")
        print("  • Để kết thúc, hãy nói: 'Tạm biệt', 'Dừng lại' hoặc bấm [Ctrl + C]")
        print("=" * 70)

        # Chào mừng mở đầu phiên làm việc
        welcome_phrase = "Xin kính chào Quý công dân. Tôi là Trợ lý AI hỗ trợ dịch vụ hành chính công. Quý công dân cần hỗ trợ thủ tục gì hôm nay?"
        print(f"\n[🤖 TRỢ LÝ]: {welcome_phrase}")
        if self.tts_enabled:
            self.tts.speak(welcome_phrase, block=True)

        session_count = 0
        try:
            while True:
                session_count += 1
                print(f"\n{'='*25} LƯỢT HỎI THỨ {session_count} {'='*25}")
                
                # 1. Thu âm từ mic
                if active_mode == "vad":
                    audio = self.recorder.record_vad(silence_duration=1.8, max_duration=25.0)
                else:
                    audio = self.recorder.record_push_to_talk()

                if len(audio) == 0:
                    print("[*] Chưa bắt được âm thanh, đang sẵn sàng cho lượt tiếp theo...")
                    continue

                # 2. Xử lý toàn trình
                res = self.process_audio(audio, speak=True)
                
                # 3. Kiểm tra điều kiện kết thúc
                if res and res.get("is_exit", False):
                    print("\n[+] Đã nhận lệnh kết thúc từ Quý công dân. Phiên làm việc hoàn tất.")
                    break

        except KeyboardInterrupt:
            print("\n\n[!] Nhận tín hiệu dừng từ bàn phím (Ctrl+C). Đang đóng phiên làm việc...")
            farewell = "Tạm biệt Quý công dân. Chúc Quý công dân một ngày tốt lành!"
            if self.tts_enabled:
                self.tts.speak(farewell, block=True)
        finally:
            self.tts.stop()

    def run_interactive_text(self):
        """
        Chế độ gõ phím trực tiếp (Text Mode):
        Phục vụ kiểm thử nhanh, gỡ lỗi và dự phòng khi ở hội trường/phòng thi ồn ào.
        """
        print("\n" + "=" * 70)
        print(" BẮT ĐẦU CHẾ ĐỘ NHẬP VĂN BẢN (TEXT MODE) ")
        print("  • Gõ câu hỏi của bạn và nhấn [Enter]")
        print("  • Gõ 'q', 'exit' hoặc 'tạm biệt' để thoát")
        print("=" * 70)

        while True:
            try:
                question = input("\n[👤 CÔNG DÂN HỎI]: ").strip()
                if not question:
                    continue
                
                if question.lower() in ["q", "exit", "quit", "thoát"] or self.is_exit_command(question):
                    farewell = "Cảm ơn Quý công dân đã sử dụng dịch vụ. Chào tạm biệt!"
                    print(f"\n[🤖 TRỢ LÝ]: {farewell}")
                    if self.tts_enabled:
                        self.tts.speak(farewell, block=True)
                    break

                res = self.process_text(question, speak=self.tts_enabled)
                print(f"⏱️  Thời gian chuẩn bị: {res['latency']['response_sec']}s (RAG: {res['latency']['rag_sec']}s | TTS: {res['latency']['tts_synth_sec']}s)")

            except KeyboardInterrupt:
                print("\n[!] Đã dừng chế độ văn bản.")
                break


if __name__ == "__main__":
    pipeline = VoiceAgentPipeline(record_mode="ptt", tts_enabled=True)
    # Thử nghiệm câu hỏi mẫu đầu tiên
    test_q = "Làm thẻ căn cước cho trẻ dưới 14 tuổi thì cần làm những gì?"
    print(f"\n[*] Chạy thử nghiệm câu hỏi mẫu: \"{test_q}\"")
    pipeline.process_text(test_q, speak=True)
