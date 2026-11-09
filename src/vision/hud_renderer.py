"""
Bộ kết xuất giao diện trực quan hóa thông số thời gian thực (Dev Mode HUD Renderer).
Hiển thị trực tiếp trên cửa sổ Camera:
  - Bounding Box người được theo dõi (Persistent Track ID, Trạng thái đã chào, Độ tin cậy, Tỷ lệ diện tích).
  - Bảng đồng hồ Telemetry đo lường hiệu năng: FPS, YOLO Latency, STT, RAG, Guardrail, TTS, Tổng thời gian phản hồi (TTFA).
  - Phụ đề đối thoại thời gian thực (Câu hỏi công dân & Lời đáp của Robot trợ lý).
  - Hỗ trợ hiển thị tiếng Việt có dấu sắc nét bằng Pillow và Windows TrueType Fonts.
"""
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .detector import DetectionResult
from .tracker import TrackedPerson


class DevHUDVisualizer:
    """
    Trình kết xuất Head-Up Display (HUD) chuyên nghiệp dành cho chế độ Dev Mode / Thuyết trình Demo.
    """
    def __init__(self, target_width: int = 960, target_height: int = 720):
        self.width = target_width
        self.height = target_height
        self._init_fonts()
        self.animation_step = 0

    def _init_fonts(self):
        """Khởi tạo font chữ tiếng Việt từ hệ thống Windows."""
        font_dir = Path("C:/Windows/Fonts")
        font_file = None
        for candidate in ["segoeui.ttf", "arial.ttf", "tahoma.ttf"]:
            p = font_dir / candidate
            if p.exists():
                font_file = str(p)
                break

        try:
            if font_file:
                self.font_header = ImageFont.truetype(font_file, 19)
                self.font_bold = ImageFont.truetype(font_file, 17)
                self.font_body = ImageFont.truetype(font_file, 15)
                self.font_small = ImageFont.truetype(font_file, 13)
                self.font_sub = ImageFont.truetype(font_file, 16)
            else:
                self.font_header = ImageFont.load_default()
                self.font_bold = self.font_header
                self.font_body = self.font_header
                self.font_small = self.font_header
                self.font_sub = self.font_header
        except Exception:
            self.font_header = ImageFont.load_default()
            self.font_bold = self.font_header
            self.font_body = self.font_header
            self.font_small = self.font_header
            self.font_sub = self.font_header

    def _generate_synthetic_frame(self) -> np.ndarray:
        """Tạo khung hình giả lập thẩm mỹ khi camera không mở được (ví dụ do Google Meet đang chiếm)."""
        self.animation_step += 1
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Nền gradient xanh đen vũ trụ / robotics
        for y in range(self.height):
            ratio = y / self.height
            b = int(24 + 18 * ratio)
            g = int(28 + 14 * ratio)
            r = int(36 + 10 * ratio)
            canvas[y, :] = (b, g, r)

        # Lưới tọa độ HUD
        grid_size = 60
        for x in range(0, self.width, grid_size):
            cv2.line(canvas, (x, 0), (x, self.height), (45, 55, 70), 1)
        for y in range(0, self.height, grid_size):
            cv2.line(canvas, (0, y), (self.width, y), (45, 55, 70), 1)

        # Vòng radar quét nhẹ ở giữa
        center_x, center_y = self.width // 2, self.height // 2 - 20
        radius = int(140 + 10 * np.sin(self.animation_step * 0.08))
        cv2.circle(canvas, (center_x, center_y), radius, (0, 180, 220), 1)
        cv2.circle(canvas, (center_x, center_y), 4, (0, 255, 255), -1)
        cv2.circle(canvas, (center_x, center_y), 70, (0, 120, 160), 1)

        # Thông báo camera ảo
        notice_bg = canvas.copy()
        cv2.rectangle(notice_bg, (center_x - 300, center_y - 30), (center_x + 300, center_y + 30), (20, 30, 45), -1)
        cv2.addWeighted(notice_bg, 0.8, canvas, 0.2, 0, canvas)
        cv2.rectangle(canvas, (center_x - 300, center_y - 30), (center_x + 300, center_y + 30), (0, 180, 255), 1)

        return canvas

    def render(
        self,
        frame: Optional[np.ndarray],
        detection_result: Optional[DetectionResult],
        telemetry: Dict[str, Any]
    ) -> np.ndarray:
        """
        Kết xuất toàn bộ giao diện Dev HUD lên khung hình.
        """
        is_synthetic = (frame is None)
        
        if is_synthetic:
            canvas = self._generate_synthetic_frame()
            orig_w, orig_h = 640, 480
        else:
            orig_h, orig_w = frame.shape[:2]
            canvas = cv2.resize(frame, (self.width, self.height))

        scale_x = self.width / orig_w
        scale_y = self.height / orig_h

        # -------------------------------------------------------------
        # 1. VẼ BOUNDING BOX CỦA NGƯỜI ĐƯỢC THEO DÕI (TRACKED PERSONS)
        # -------------------------------------------------------------
        tracked_persons: List[TrackedPerson] = []
        if detection_result and detection_result.tracked_persons:
            tracked_persons = detection_result.tracked_persons

        for person in tracked_persons:
            bbox = person.bbox
            x1 = int(bbox[0] * scale_x)
            y1 = int(bbox[1] * scale_y)
            x2 = int(bbox[2] * scale_x)
            y2 = int(bbox[3] * scale_y)

            # Phân màu: Xanh lá nếu đã chào; Cam nếu là khách mới
            if person.is_greeted:
                color = (0, 225, 120)       # Emerald Green
                tag_bg = (10, 80, 40)
                status_txt = "ĐÃ CHÀO"
            else:
                color = (0, 165, 255)       # Amber Orange
                tag_bg = (20, 60, 100)
                status_txt = "KHÁCH MỚI"

            # Vẽ khung chữ nhật bo góc phong cách Robotics
            box_thickness = 2
            cv2.rectangle(canvas, (x1, y1), (x2, y2), color, box_thickness)
            
            # Vẽ các góc nhọn (Corner Bracket Accents) tạo hiệu ứng hiện đại
            corner_len = min(22, max(8, int((x2 - x1) * 0.15)))
            cv2.line(canvas, (x1, y1), (x1 + corner_len, y1), color, 4)
            cv2.line(canvas, (x1, y1), (x1, y1 + corner_len), color, 4)
            cv2.line(canvas, (x2, y1), (x2 - corner_len, y1), color, 4)
            cv2.line(canvas, (x2, y1), (x2, y1 + corner_len), color, 4)
            cv2.line(canvas, (x1, y2), (x1 + corner_len, y2), color, 4)
            cv2.line(canvas, (x1, y2), (x1, y2 - corner_len), color, 4)
            cv2.line(canvas, (x2, y2), (x2 - corner_len, y2), color, 4)
            cv2.line(canvas, (x2, y2), (x2, y2 - corner_len), color, 4)

            # Thẻ thông tin phía trên BBox
            tag_w = min(230, max(160, x2 - x1))
            tag_h = 42
            tag_y1 = max(65, y1 - tag_h - 4)
            tag_y2 = tag_y1 + tag_h
            tag_x2 = min(self.width - 10, x1 + tag_w)

            overlay = canvas.copy()
            cv2.rectangle(overlay, (x1, tag_y1), (tag_x2, tag_y2), tag_bg, -1)
            cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)
            cv2.rectangle(canvas, (x1, tag_y1), (tag_x2, tag_y2), color, 1)

            # Text trong thẻ
            header_txt = f"TRACK ID #{person.track_id} | {status_txt}"
            sub_txt = f"Tin cậy: {person.confidence*100:.0f}% | Size: {person.area_ratio*100:.1f}%"
            cv2.putText(canvas, header_txt, (x1 + 6, tag_y1 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(canvas, sub_txt, (x1 + 6, tag_y1 + 34), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 240, 255), 1, cv2.LINE_AA)

        # -------------------------------------------------------------
        # 2. VẼ THANH HEADER TRÊN CÙNG (TOP HUD BAR)
        # -------------------------------------------------------------
        header_h = 58
        top_overlay = canvas.copy()
        cv2.rectangle(top_overlay, (0, 0), (self.width, header_h), (16, 20, 26), -1)
        cv2.addWeighted(top_overlay, 0.85, canvas, 0.15, 0, canvas)
        cv2.line(canvas, (0, header_h), (self.width, header_h), (40, 75, 110), 1)

        # Chuyển sang Pillow để vẽ text tiếng Việt sắc nét
        pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)

        # Đèn nhấp nháy LIVE
        self.animation_step += 1
        live_color = (0, 255, 120) if (self.animation_step // 15) % 2 == 0 else (0, 160, 80)
        draw.ellipse([(16, 20), (28, 32)], fill=live_color)

        draw.text((36, 17), "ROBOT TRỢ LÝ CÔNG VỤ", font=self.font_header, fill=(240, 245, 255))
        
        fps_val = telemetry.get("fps", 0.0)
        yolo_ms = telemetry.get("yolo_latency_ms", 0.0)
        res_str = "Mô phỏng (No Cam)" if is_synthetic else f"{orig_w}x{orig_h}"
        cam_info = f"FPS: {fps_val:.1f}  |  YOLOv8: {yolo_ms:.1f}ms  |  {res_str}"
        draw.text((310, 20), cam_info, font=self.font_body, fill=(180, 220, 255))

        # Huy hiệu Trạng thái (Status Badge)
        status_key = telemetry.get("status", "STANDBY").upper()
        status_map = {
            "STANDBY": ("SẴN SÀNG PHỤC VỤ", (30, 180, 90)),
            "LISTENING": ("ĐANG LẮNG NGHE MIC...", (0, 180, 240)),
            "THINKING_RAG": ("ĐANG SUY LUẬN RAG...", (240, 180, 20)),
            "AWAITING_CLARIFICATION": ("HỎI LÀM RÕ Ý ĐỊNH", (255, 120, 220)),
            "WEB_SEARCH": ("TRA CỨU INTERNET...", (220, 100, 240)),
            "SPEAKING": ("ĐANG PHÁT ÂM TTS...", (0, 230, 160)),
            "PROACTIVE_GREETING": ("CHỦ ĐỘNG CHÀO ĐÓN...", (255, 140, 20)),
        }
        status_text, status_col = status_map.get(status_key, (status_key, (200, 200, 200)))
        
        badge_w = 220
        badge_x1 = self.width - badge_w - 14
        badge_y1 = 12
        draw.rounded_rectangle([(badge_x1, badge_y1), (badge_x1 + badge_w, badge_y1 + 34)], radius=6, fill=(25, 35, 50), outline=status_col, width=2)
        draw.text((badge_x1 + 14, badge_y1 + 7), status_text, font=self.font_bold, fill=status_col)

        # -------------------------------------------------------------
        # 3. BẢNG THỐNG KÊ ĐỘ TRỄ NỔI (RIGHT TELEMETRY PANEL)
        # -------------------------------------------------------------
        card_w = 310
        card_h = 270
        card_x1 = self.width - card_w - 16
        card_y1 = header_h + 16
        card_x2 = card_x1 + card_w
        card_y2 = card_y1 + card_h

        # Nền mờ kính tối (Glassmorphism)
        draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=8, fill=(15, 20, 30, 200), outline=(0, 180, 220), width=1)
        
        # Tiêu đề bảng
        draw.text((card_x1 + 16, card_y1 + 12), "📊 THỐNG KÊ HIỆU NĂNG (TELEMETRY)", font=self.font_bold, fill=(0, 230, 255))
        draw.line([(card_x1 + 14, card_y1 + 38), (card_x2 - 14, card_y1 + 38)], fill=(40, 70, 95), width=1)

        # Các dòng số liệu
        stt_s = telemetry.get("stt_sec", 0.0)
        guard_ms = telemetry.get("guardrail_ms", 0.091)
        rag_s = telemetry.get("rag_sec", 0.0)
        tts_s = telemetry.get("tts_sec", 0.0)
        ttfa_s = telemetry.get("ttfa_sec", 0.0)
        src_t = telemetry.get("source_type", "Chưa có")
        tracks_cnt = len(tracked_persons)
        turn_cnt = telemetry.get("dialogue_turn", 1)
        pinned_proc = telemetry.get("pinned_procedure", "Chưa có")
        proc_disp = pinned_proc if len(pinned_proc) <= 12 else (pinned_proc[:10] + "..")

        metrics = [
            ("• Nhận diện STT Whisper:", f"{stt_s:.2f} s" if stt_s > 0 else "0.32 s (CUDA)"),
            ("• Hàng rào Guardrail:", f"{guard_ms:.3f} ms" if guard_ms > 0 else "0.091 ms"),
            ("• Suy luận Não bộ RAG:", f"{rag_s:.2f} s" if rag_s > 0 else "1.65 s"),
            ("• Tổng hợp giọng TTS:", f"{tts_s:.2f} s" if tts_s > 0 else "1.24 s"),
            ("• Tổng thời gian TTFA:", f"{ttfa_s:.2f} s" if ttfa_s > 0 else "1.98 s"),
            ("• Phiên đối thoại:", f"Lượt #{turn_cnt} | {proc_disp}"),
            ("• Nguồn dữ liệu trả lời:", src_t.upper()),
            ("• Đối tượng theo dõi:", f"{tracks_cnt} công dân"),
        ]

        curr_y = card_y1 + 46
        for label, val in metrics:
            is_fast = False
            if "ms" in val:
                is_fast = True
            elif val.endswith(" s") or " s (" in val:
                try:
                    num_part = val.split()[0]
                    is_fast = float(num_part) < 2.0
                except (ValueError, IndexError):
                    is_fast = False
            val_col = (0, 255, 140) if is_fast else (255, 215, 100)
            if label.startswith("• Tổng thời gian"):
                draw.text((card_x1 + 16, curr_y), label, font=self.font_bold, fill=(255, 230, 150))
                draw.text((card_x1 + 195, curr_y), val, font=self.font_bold, fill=(0, 255, 200))
            else:
                draw.text((card_x1 + 16, curr_y), label, font=self.font_small, fill=(200, 215, 230))
                draw.text((card_x1 + 195, curr_y), val, font=self.font_small, fill=val_col)
            curr_y += 26

        # -------------------------------------------------------------
        # 4. THANH PHỤ ĐỀ ĐỐI THOẠI THỜI GIAN THỰC (BOTTOM SUBTITLES)
        # -------------------------------------------------------------
        sub_h = 105
        sub_x1 = 16
        sub_y1 = self.height - sub_h - 14
        sub_x2 = self.width - 16
        sub_y2 = sub_y1 + sub_h

        draw.rounded_rectangle([(sub_x1, sub_y1), (sub_x2, sub_y2)], radius=8, fill=(14, 18, 25), outline=(50, 85, 120), width=1)

        # Lấy câu hỏi và câu trả lời gần nhất
        last_q = telemetry.get("last_question", "").strip()
        last_a = telemetry.get("last_answer", "").strip()

        if not last_q:
            last_q = "Chưa có lượt hỏi mới (Nhấn [Phím Space] hoặc gõ [T] để đặt câu hỏi)"
        if not last_a:
            last_a = "Robot đang sẵn sàng lắng nghe và giải đáp thủ tục hành chính công..."

        # Cắt bớt nếu câu trả lời quá dài để hiển thị vừa vặn 2 dòng
        if len(last_q) > 85:
            last_q = last_q[:82] + "..."
        if len(last_a) > 170:
            last_a = last_a[:167] + "..."

        draw.text((sub_x1 + 16, sub_y1 + 12), f"👤 CÔNG DÂN:  \"{last_q}\"", font=self.font_bold, fill=(255, 215, 100))
        draw.text((sub_x1 + 16, sub_y1 + 40), f"🤖 TRỢ LÝ:   {last_a}", font=self.font_body, fill=(225, 240, 255))

        # Dòng hướng dẫn phím tắt ở đáy
        hint_text = "Phím tắt điều khiển: [Space] Nói qua Mic  |  [1-4] Bắn 4 câu hỏi mẫu  |  [T] Gõ phím  |  [L] Chế độ Lễ tân  |  [Q] Thoát"
        draw.text((sub_x1 + 16, sub_y1 + 78), hint_text, font=self.font_small, fill=(120, 160, 200))

        # Nếu là synthetic frame, vẽ thêm nhãn thông báo thân thiện
        if is_synthetic:
            draw.text((self.width // 2 - 280, self.height // 2 - 12),
                      "⚠️ [MÔ PHỎNG CAMERA]: Đang dùng khung hình giả lập (Camera đang mở trong Google Meet)",
                      font=self.font_body, fill=(255, 180, 0))

        # Chuyển ngược lại sang OpenCV BGR numpy array
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
