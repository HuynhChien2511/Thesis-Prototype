"""
CHƯƠNG TRÌNH KHỞI CHẠY CHẾ ĐỘ NHÀ PHÁT TRIỂN (DEVELOPER TELEMETRY DASHBOARD).
Chuyên dụng cho các buổi Báo cáo Tiến độ, Thuyết trình Hội đồng & Live Demo:
  1. Mở duy nhất 1 cửa sổ trực quan hóa HUD (960x720) hiển thị Camera thời gian thực.
  2. Vẽ Bounding Box, Track ID, trạng thái Đã chào đón, FPS và độ trễ YOLOv8.
  3. Bảng đồng hồ Telemetry đo lường: STT, Guardrail, RAG, TTS, TTFA toàn trình.
  4. Phụ đề tiếng Việt hiển thị câu hỏi công dân & lời đáp robot theo thời gian thực.
  5. Nhận diện phím tắt NGAY TỨC THÌ từ cả cửa sổ Camera lẫn Terminal!
"""
import sys
import time
import threading
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

import cv2
import numpy as np
from src.pipeline import VoiceAgentPipeline
from src.vision.hud_renderer import DevHUDVisualizer


SAMPLE_DEMO_QUERIES = {
    "1": ("Thủ tục Căn cước (RAG CSDL Nội bộ - 0% ảo giác)", "Cho tôi hỏi trẻ em dưới 14 tuổi thì làm thẻ căn cước thế nào, có bắt buộc không?"),
    "a": ("Thủ tục Căn cước (RAG CSDL Nội bộ - 0% ảo giác)", "Cho tôi hỏi trẻ em dưới 14 tuổi thì làm thẻ căn cước thế nào, có bắt buộc không?"),
    "2": ("Thủ tục Visa (Adaptive Web Search Fallback + Cảnh báo)", "Thủ tục xin visa du lịch Nhật Bản tự túc mới nhất cần những giấy tờ gì?"),
    "b": ("Thủ tục Visa (Adaptive Web Search Fallback + Cảnh báo)", "Thủ tục xin visa du lịch Nhật Bản tự túc mới nhất cần những giấy tờ gì?"),
    "3": ("Tán gẫu xã giao (Hàng rào Guardrail 0.09ms)", "Bạn có người yêu chưa vậy robot?"),
    "c": ("Tán gẫu xã giao (Hàng rào Guardrail 0.09ms)", "Bạn có người yêu chưa vậy robot?"),
    "4": ("Hỏi đáp Thị giác Camera (Gemini Multimodal VQA)", "Trước mặt tôi có gì vậy robot?"),
    "d": ("Hỏi đáp Thị giác Camera (Gemini Multimodal VQA)", "Trước mặt tôi có gì vậy robot?"),
    "5": ("Tra cứu Thời tiết (Web Fallback Đời sống)", "Thời tiết hôm nay như thế nào?"),
    "e": ("Tra cứu Thời tiết (Web Fallback Đời sống)", "Thời tiết hôm nay như thế nào?"),
    "6": ("Hỏi Mơ hồ (Ambiguity Clarification Rule of Three)", "Tôi muốn làm thẻ căn cước"),
    "f": ("Hỏi Mơ hồ (Ambiguity Clarification Rule of Three)", "Tôi muốn làm thẻ căn cước")
}


class DevModeDashboard:
    """
    Bộ điều khiển trung tâm Dev Mode HUD Dashboard (Phản hồi tức thì, không giật lag).
    """
    def __init__(self, tts_enabled: bool = True):
        print("\n" + "=" * 75)
        print(" KHỞI TẠO CHẾ ĐỘ NHÀ PHÁT TRIỂN (DEVELOPER HUD DASHBOARD) ")
        print("=" * 75)
        
        self.pipeline = VoiceAgentPipeline(record_mode="ptt", tts_enabled=tts_enabled, vision_enabled=True)
        self.hud = DevHUDVisualizer(target_width=960, target_height=720)
        self.is_running = True
        
        # Tiêu đề cửa sổ dùng thuần ASCII để triệt tiêu lỗi tạo 2 cửa sổ của Ultralytics patch
        self.window_name = "ROBOT AI ASSISTANT - DEV TELEMETRY HUD"
        
        # Biến tính FPS hiển thị
        self.fps = 0.0
        self.frame_count = 0
        self.fps_timer = time.time()
        
        self._action_lock = threading.Lock()

    def _dispatch_action(self, action_type: str, arg: str = ""):
        """Thực thi tác vụ trên luồng nền (Worker Thread) để không bao giờ làm đơ cửa sổ HUD."""
        if self.pipeline.is_busy():
            print("\n[⏳ HỆ THỐNG ĐANG BẬN] Đang xử lý câu hỏi trước, vui lòng chờ trong giây lát...")
            return

        def worker():
            try:
                if action_type == "demo":
                    key = arg.lower()
                    if key in SAMPLE_DEMO_QUERIES:
                        lbl, q = SAMPLE_DEMO_QUERIES[key]
                        print("\n" + "=" * 65)
                        print(f"👉 [KÍCH HOẠT DEMO: {lbl.upper()}]:")
                        print(f"   \"{q}\"")
                        print("=" * 65)
                        self.pipeline.process_text(
                            q,
                            speak=self.pipeline.tts_enabled,
                            play_audio=self.pipeline.tts_enabled,
                            streaming_tts=True
                        )
                elif action_type == "mic":
                    print("\n" + "=" * 60)
                    print(" [🎙️ PUSH-TO-TALK ĐANG THU ÂM] Hãy nói vào micro...")
                    print("=" * 60)
                    audio = self.pipeline.recorder.record_push_to_talk()
                    if len(audio) > 0:
                        self.pipeline.process_audio(audio, speak=self.pipeline.tts_enabled)
                    else:
                        print("[!] Không thu được tín hiệu âm thanh.")
                elif action_type == "receptionist":
                    print("\n[👀 BẬT CHẾ ĐỘ LỄ TÂN] Robot đang quan sát camera để chào hỏi...")
                    self.pipeline.resume_proactive_greeting()
                elif action_type == "pause_greeting":
                    self.pipeline.pause_proactive_greeting()
                    print("\n[⏸️ ĐÃ TẠM DỪNG CHÀO HỎI CHỦ ĐỘNG]")
            except Exception as e:
                print(f"[❌ LỖI THỰC THI]: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _terminal_listener(self):
        """Luồng đọc lệnh từ Terminal chạy nền (Không làm nghẽn cửa sổ đồ họa)."""
        while self.is_running:
            try:
                cmd = input().strip().lower()
            except (KeyboardInterrupt, EOFError):
                self.is_running = False
                break

            if not cmd:
                continue

            if cmd in ["q", "exit", "quit", "thoát"]:
                self.is_running = False
                break
            elif cmd in ["1", "a"]:
                self._dispatch_action("demo", "a")
            elif cmd in ["2", "b"]:
                self._dispatch_action("demo", "b")
            elif cmd in ["3", "c"]:
                self._dispatch_action("demo", "c")
            elif cmd in ["4", "d"]:
                self._dispatch_action("demo", "d")
            elif cmd in ["5", "e"]:
                self._dispatch_action("demo", "e")
            elif cmd in ["6", "f"]:
                self._dispatch_action("demo", "f")
            elif cmd in ["space", "mic", "talk", "noi"]:
                self._dispatch_action("mic")
            elif cmd in ["l", "letan"]:
                self._dispatch_action("receptionist")
            elif cmd in ["p", "pause"]:
                self._dispatch_action("pause_greeting")
            else:
                # Nếu người dùng gõ cả câu hỏi tự do bằng văn bản
                print(f"\n[👤 CÂU HỎI TỰ NHẬP]: \"{cmd}\"")
                threading.Thread(
                    target=lambda: self.pipeline.process_text(
                        cmd,
                        speak=self.pipeline.tts_enabled,
                        play_audio=self.pipeline.tts_enabled,
                        streaming_tts=True
                    ),
                    daemon=True
                ).start()

    def start(self):
        """Khởi chạy Dev Mode: Vòng lặp đồ họa GUI trên luồng chính để nhận phím tắt tức thời."""
        # Tạm dừng chào hỏi spam khi khởi động
        self.pipeline.pause_proactive_greeting()

        # Tạo luồng đọc lệnh Terminal chạy ngầm
        term_thread = threading.Thread(target=self._terminal_listener, daemon=True)
        term_thread.start()

        print("\n" + "=" * 75)
        print(" 🤖 ROBOT TRỢ LÝ AI - DEVELOPER TELEMETRY HUD (DEV MODE) ")
        print("=" * 75)
        print("  [👀 CỬA SỔ HUD]: Đang hiển thị trực tiếp trên màn hình!")
        print("  [⚡ PHÍM TẮT TRỰC TIẾP TRÊN CỬA SỔ CAMERA HOẶC GÕ TERMINAL]:")
        print("     • [Phím Space] : Nói qua Micro (Push-to-Talk)")
        print("     • [Phím 1 / a] : Demo Thủ tục Căn cước (RAG nội bộ)")
        print("     • [Phím 2 / b] : Demo Thủ tục Visa (Adaptive Web Fallback)")
        print("     • [Phím 3 / c] : Demo Tán gẫu 'Có người yêu chưa?' (Guardrail 0.09ms)")
        print("     • [Phím 4 / d] : Demo Thị giác 'Trước mặt tôi có gì?' (Gemini Vision)")
        print("     • [Phím 5 / e] : Demo Tra cứu Thời tiết hôm nay")
        print("     • [Phím 6 / f] : Demo Hỏi Mơ hồ 'Tôi muốn làm căn cước' (Clarification Rule of Three)")
        print("     • [Phím L]     : Bật chế độ Lễ tân chào hỏi")
        print("     • [Phím Q/ESC] : Thoát chương trình")
        print("=" * 75)
        print("👉 Bạn có thể bấm thẳng phím tắt trên cửa sổ Camera, HOẶC gõ lệnh vào đây:\n")

        # Khởi tạo cửa sổ OpenCV duy nhất
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)

        try:
            while self.is_running:
                # 1. Lấy khung hình mới nhất từ Camera
                frame = None
                if self.pipeline.camera and self.pipeline.camera.is_connected:
                    frame = self.pipeline.camera.get_frame()

                # 2. Lấy kết quả nhận diện gần nhất từ Vision Context Manager
                detection_res = None
                if self.pipeline.vision_mgr:
                    detection_res = self.pipeline.vision_mgr.latest_result

                # 3. Tính toán FPS hiển thị
                self.frame_count += 1
                if time.time() - self.fps_timer >= 0.5:
                    self.fps = round(self.frame_count / (time.time() - self.fps_timer), 1)
                    self.frame_count = 0
                    self.fps_timer = time.time()

                self.pipeline.telemetry["fps"] = self.fps
                if detection_res:
                    self.pipeline.telemetry["yolo_latency_ms"] = round(detection_res.inference_time_sec * 1000, 1)

                # 4. Kết xuất giao diện HUD
                rendered_frame = self.hud.render(frame, detection_res, self.pipeline.telemetry)
                
                # 5. Hiển thị lên cửa sổ duy nhất
                cv2.imshow(self.window_name, rendered_frame)
                key = cv2.waitKey(20) & 0xFF

                # Xử lý phím tắt trực tiếp trên cửa sổ OpenCV (Phản hồi tức thì < 1ms)
                if key in [ord('q'), ord('Q'), 27]:  # Q hoặc ESC
                    self.is_running = False
                    break
                elif key == ord(' '):  # Phím Space: Thu âm Micro PTT
                    self._dispatch_action("mic")
                elif key in [ord('1'), ord('a'), ord('A')]:
                    self._dispatch_action("demo", "a")
                elif key in [ord('2'), ord('b'), ord('B')]:
                    self._dispatch_action("demo", "b")
                elif key in [ord('3'), ord('c'), ord('C')]:
                    self._dispatch_action("demo", "c")
                elif key in [ord('4'), ord('d'), ord('D')]:
                    self._dispatch_action("demo", "d")
                elif key in [ord('5'), ord('e'), ord('E')]:
                    self._dispatch_action("demo", "e")
                elif key in [ord('6'), ord('f'), ord('F')]:
                    self._dispatch_action("demo", "f")
                elif key in [ord('l'), ord('L')]:
                    self._dispatch_action("receptionist")
                elif key in [ord('p'), ord('P')]:
                    self._dispatch_action("pause_greeting")

        except (KeyboardInterrupt, EOFError):
            print("\n[+] Đã nhận tín hiệu dừng từ người dùng.")
        finally:
            self.is_running = False
            self.pipeline.cleanup()
            cv2.destroyAllWindows()
            print("\n[+] Đã đóng Dev Mode an toàn. Cảm ơn bạn!")


def run_dev_dashboard(tts_enabled: bool = True):
    dashboard = DevModeDashboard(tts_enabled=tts_enabled)
    dashboard.start()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Developer Telemetry Dashboard")
    parser.add_argument("--no-tts", action="store_true", help="Vô hiệu hóa phát giọng nói TTS")
    args, _ = parser.parse_known_args()
    run_dev_dashboard(tts_enabled=not args.no_tts)


if __name__ == "__main__":
    main()
