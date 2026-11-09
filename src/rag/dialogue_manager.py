"""
Module Quản lý Hội thoại Đa lượt & Bộ nhớ Ngữ cảnh Thông minh (Multi-turn Dialogue Manager).
Thiết kế Kiến trúc 2 Tầng:
  - Tầng 1 (Pinned Session Slots): Ghim vĩnh viễn thủ tục cốt lõi & đối tượng xuyên suốt phiên.
  - Tầng 2 (Sliding-window Buffer): Lưu 3-5 lượt đối đáp gần nhất để giải quyết đại từ nối tiếp.
Tự động dọn dẹp ngữ cảnh (Session Auto-Flush) khi camera phát hiện người đó rời đi.
"""
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class SessionState:
    """Định nghĩa các trạng thái của một phiên hội thoại."""
    NORMAL = "NORMAL"
    AWAITING_CLARIFICATION = "AWAITING_CLARIFICATION"


@dataclass
class SessionSlots:
    """Tầng 1: Các thực thể then chốt được ghim chặt trong suốt cuộc trò chuyện."""
    procedure_name: Optional[str] = None      # Ví dụ: "Thẻ căn cước", "Đăng ký tạm trú"
    target_citizen: Optional[str] = None      # Ví dụ: "Trẻ em dưới 14 tuổi", "Người lớn"
    action_type: Optional[str] = None         # Ví dụ: "Cấp mới lần đầu", "Cấp đổi", "Cấp lại"
    custom_attributes: Dict[str, Any] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not (self.procedure_name or self.target_citizen or self.action_type or self.custom_attributes)

    def update_from_query(self, query: str):
        """Tự động trích xuất thực thể thủ tục, đối tượng, hình thức từ câu hỏi."""
        if not query:
            return
        q = query.lower()
        procedures = {
            "thẻ căn cước": "thẻ căn cước",
            "căn cước": "căn cước",
            "đăng ký kết hôn": "đăng ký kết hôn",
            "kết hôn": "đăng ký kết hôn",
            "khai sinh": "đăng ký khai sinh",
            "khai tử": "đăng ký khai tử",
            "tạm trú": "đăng ký tạm trú",
            "thường trú": "đăng ký thường trú",
            "hộ chiếu": "cấp hộ chiếu",
            "visa": "thủ tục visa",
            "sổ đỏ": "sang tên sổ đỏ",
            "đất đai": "thủ tục đất đai",
            "chứng thực": "chứng thực bản sao",
            "sao y": "chứng thực bản sao",
            "công chứng": "chứng thực bản sao",
            "tình trạng hôn nhân": "xác nhận tình trạng hôn nhân",
            "độc thân": "xác nhận tình trạng hôn nhân",
            "giấy phép lái xe": "cấp đổi giấy phép lái xe",
            "bằng lái": "cấp đổi giấy phép lái xe",
            "gplx": "cấp đổi giấy phép lái xe",
            # Hỗ trợ tiếng Việt không dấu (Accentless input)
            "the can cuoc": "thẻ căn cước",
            "can cuoc": "căn cước",
            "dang ky ket hon": "đăng ký kết hôn",
            "ket hon": "đăng ký kết hôn",
            "khai sinh": "đăng ký khai sinh",
            "khai tu": "đăng ký khai tử",
            "tam tru": "đăng ký tạm trú",
            "thuong tru": "đăng ký thường trú",
            "ho chieu": "cấp hộ chiếu",
            "so do": "sang tên sổ đỏ",
            "dat dai": "thủ tục đất đai",
            "chung thuc": "chứng thực bản sao",
            "sao y": "chứng thực bản sao",
            "cong chung": "chứng thực bản sao",
            "tinh trang hon nhan": "xác nhận tình trạng hôn nhân",
            "doc than": "xác nhận tình trạng hôn nhân",
            "giay phep lai xe": "cấp đổi giấy phép lái xe",
            "bang lai": "cấp đổi giấy phép lái xe",
        }
        for kw, proc in procedures.items():
            if kw in q:
                if self.procedure_name and self.procedure_name.lower() != proc.lower():
                    # Đổi sang thủ tục mới -> reset các slot phụ thuộc của thủ tục cũ
                    self.target_citizen = None
                    self.action_type = None
                    self.custom_attributes.clear()
                self.procedure_name = proc
                break

        targets = {
            "dưới 14 tuổi": "trẻ em dưới 14 tuổi",
            "trẻ em": "trẻ em",
            "trẻ nhỏ": "trẻ em",
            "người lớn": "người từ 14 tuổi trở lên",
            "từ 14 tuổi": "người từ 14 tuổi trở lên",
        }
        for kw, tgt in targets.items():
            if kw in q:
                self.target_citizen = tgt
                break

        actions = {
            "cấp mới": "cấp mới",
            "làm mới": "cấp mới",
            "lần đầu": "cấp mới lần đầu",
            "cấp đổi": "cấp đổi",
            "đổi lại": "cấp đổi",
            "cấp lại": "cấp lại do bị mất",
            "bị mất": "cấp lại do bị mất",
            "mất thẻ": "cấp lại do bị mất",
        }
        for kw, act in actions.items():
            if kw in q:
                self.action_type = act
                break

    def format_pinned_context(self) -> str:
        """Xuất thông tin đã ghim thành đoạn tóm tắt súc tích cho LLM."""
        parts = []
        if self.procedure_name:
            parts.append(f"Thủ tục chính: {self.procedure_name}")
        if self.target_citizen:
            parts.append(f"Đối tượng áp dụng: {self.target_citizen}")
        if self.action_type:
            parts.append(f"Hình thức thực hiện: {self.action_type}")
        for k, v in self.custom_attributes.items():
            parts.append(f"{k}: {v}")
        if not parts:
            return ""
        return "THÔNG TIN CỐT LÕI ĐÃ XÁC ĐỊNH TRONG PHIÊN NÀY:\n" + "\n".join([f"  • {p}" for p in parts])


@dataclass
class DialogueTurn:
    """Lưu trữ một cặp tương tác (Hỏi - Đáp)."""
    turn_id: int
    user_query: str
    assistant_response: str
    timestamp: float = field(default_factory=time.time)
    source_type: str = "rag"  # "rag", "guardrail", "web", "clarification"


class DialogueSession:
    """Quản lý toàn bộ ngữ cảnh hội thoại của một người dùng cụ thể."""

    def __init__(self, track_id: Optional[int] = None, max_history_turns: int = 4):
        self.track_id = track_id
        self.max_history_turns = max_history_turns
        self.created_at = time.time()
        self.last_active_at = time.time()
        
        # Tầng 1: Hồ sơ phiên cốt lõi (Ghim vĩnh viễn)
        self.slots = SessionSlots()
        
        # Tầng 2: Cửa sổ trượt các lượt đối đáp gần nhất
        self.turns: List[DialogueTurn] = []
        
        # Trạng thái hội thoại: "NORMAL" hoặc "AWAITING_CLARIFICATION"
        self.state: str = SessionState.NORMAL
        self.pending_raw_query: Optional[str] = None
        self.pending_missing_slot: Optional[str] = None
        self.pending_clarification: Optional[Dict[str, Any]] = None

    def get_context_prompt(self) -> str:
        """Alias cho build_llm_context() để tương thích các module khác."""
        return self.build_llm_context()

    def add_turn(
        self,
        user_query: str = "",
        assistant_response: str = "",
        source_type: str = "rag",
        question: Optional[str] = None,
        answer: Optional[str] = None
    ):
        """Ghi nhận một lượt tương tác mới vào phiên."""
        if question is not None:
            user_query = question
        if answer is not None:
            assistant_response = answer

        self.last_active_at = time.time()
        turn_id = len(self.turns) + 1
        turn = DialogueTurn(
            turn_id=turn_id,
            user_query=user_query.strip(),
            assistant_response=assistant_response.strip(),
            source_type=source_type
        )
        self.turns.append(turn)
        
        # Cắt tỉa theo cửa sổ trượt (Sliding Window), chỉ giữ max_history_turns lượt gần nhất
        if len(self.turns) > self.max_history_turns:
            self.turns = self.turns[-self.max_history_turns:]

    def update_slots(self, procedure_name: Optional[str] = None, 
                     target_citizen: Optional[str] = None, 
                     action_type: Optional[str] = None, 
                     **kwargs):
        """Cập nhật các thực thể cốt lõi ở Tầng 1."""
        self.last_active_at = time.time()
        if procedure_name:
            self.slots.procedure_name = procedure_name.strip()
        if target_citizen:
            self.slots.target_citizen = target_citizen.strip()
        if action_type:
            self.slots.action_type = action_type.strip()
        if kwargs:
            self.slots.custom_attributes.update(kwargs)

    def set_awaiting_clarification(self, raw_query: str, missing_slot: str):
        """Đặt trạng thái đang chờ người dân trả lời làm rõ câu hỏi."""
        self.state = "AWAITING_CLARIFICATION"
        self.pending_raw_query = raw_query.strip()
        self.pending_missing_slot = missing_slot.strip()
        self.last_active_at = time.time()

    def resolve_clarification(self) -> Optional[str]:
        """Giải phóng trạng thái chờ làm rõ, trả về câu hỏi gốc đang chờ."""
        raw_q = self.pending_raw_query
        self.state = "NORMAL"
        self.pending_raw_query = None
        self.pending_missing_slot = None
        self.last_active_at = time.time()
        return raw_q

    def format_history_for_prompt(self) -> str:
        """Định dạng lịch sử hội thoại gần nhất thành văn bản sạch sẽ cho LLM."""
        if not self.turns:
            return ""
        lines = []
        for t in self.turns:
            lines.append(f"Công dân: {t.user_query}")
            # Rút gọn câu trả lời cũ nếu quá dài để tiết kiệm token
            resp_summary = t.assistant_response
            if len(resp_summary) > 220:
                resp_summary = resp_summary[:217] + "..."
            lines.append(f"Robot: {resp_summary}")
        return "\n".join(lines)

    def build_llm_context(self) -> str:
        """
        Ghép toàn bộ ngữ cảnh 2 tầng thành khối hướng dẫn chuẩn cho Não bộ RAG:
        - Tầng 1: Pinned Slots
        - Tầng 2: Recent Dialogues
        """
        sections = []
        pinned = self.slots.format_pinned_context()
        if pinned:
            sections.append(pinned)
            
        history = self.format_history_for_prompt()
        if history:
            sections.append("LỊCH SỬ CÁC LƯỢT ĐỐI ĐÁP GẦN NHẤT TRONG PHIÊN NÀY:\n" + history)
            
        if not sections:
            return ""
            
        full_context = (
            "\n" + "=" * 55 + "\n"
            "NGỮ CẢNH HỘI THOẠI ĐA LƯỢT (HÃY DÙNG ĐỂ GIẢI NGHĨA ĐẠI TỪ THAY THẾ 'thế thì', 'cái đó', 'ở đâu', 'mất bao lâu'):\n"
            + "\n\n".join(sections)
            + "\n" + "=" * 55 + "\n"
        )
        return full_context


class DialogueSessionManager:
    """
    Bộ điều phối toàn bộ các phiên làm việc của hệ thống:
    - Quản lý phiên theo Track ID của camera
    - Hỗ trợ phiên mặc định (Track ID = 0) cho chế độ gõ phím / không có camera
    - Tự động xóa phiên khi người dùng rời đi (Track ID biến mất)
    """

    def __init__(self, max_history_turns: int = 4, session_timeout_sec: float = 120.0, max_window_turns: Optional[int] = None):
        if max_window_turns is not None:
            max_history_turns = max_window_turns
        self.max_history_turns = max_history_turns
        self.session_timeout_sec = session_timeout_sec
        self.sessions: Dict[int, DialogueSession] = {}
        # Phiên mặc định cho Text Mode hoặc khi không bật Camera
        self.default_session = DialogueSession(track_id=0, max_history_turns=max_history_turns)
        self.sessions[0] = self.default_session

    def get_session(self, track_id: Optional[int] = None) -> DialogueSession:
        """Lấy phiên tương ứng với Track ID; nếu chưa có thì tạo mới."""
        if track_id is None or track_id <= 0:
            return self.default_session

        if track_id not in self.sessions:
            self.sessions[track_id] = DialogueSession(
                track_id=track_id, 
                max_history_turns=self.max_history_turns
            )
        session = self.sessions[track_id]
        session.last_active_at = time.time()
        return session

    def flush_inactive_sessions(self, active_track_ids: List[int]):
        """
        Dọn dẹp các phiên không còn hoạt động:
        - Xóa các phiên có Track ID không còn nằm trong active_track_ids từ camera.
        - Xóa các phiên bị bỏ rơi quá session_timeout_sec.
        """
        now = time.time()
        active_set = set(active_track_ids or [])
        tracks_to_delete = []

        for tid, sess in self.sessions.items():
            if tid == 0:
                # Phiên mặc định chỉ reset nếu bị bỏ rơi quá timeout
                if now - sess.last_active_at > self.session_timeout_sec:
                    sess.turns.clear()
                    sess.slots = SessionSlots()
                    sess.state = "NORMAL"
                continue

            # Nếu Track ID này đã hoàn toàn biến mất khỏi danh sách camera
            if tid not in active_set:
                tracks_to_delete.append(tid)
            # Hoặc phiên bị treo quá lâu
            elif now - sess.last_active_at > self.session_timeout_sec:
                tracks_to_delete.append(tid)

        for tid in tracks_to_delete:
            del self.sessions[tid]
        return tracks_to_delete

    def reset_all(self):
        """Khởi động lại toàn bộ các phiên hội thoại."""
        self.sessions.clear()
        self.default_session = DialogueSession(track_id=0, max_history_turns=self.max_history_turns)
        self.sessions[0] = self.default_session
