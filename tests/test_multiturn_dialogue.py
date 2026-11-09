"""
Bộ kiểm thử Tự động cho Giai đoạn 1: Bộ nhớ Hội thoại Đa lượt 2 Tầng (DialogueSessionManager).
Kiểm tra:
  1. Cửa sổ trượt (Sliding Window) 3-5 lượt đối đáp gần nhất.
  2. Hồ sơ cốt lõi (Pinned Slots) được ghim chặt vĩnh viễn qua nhiều lượt thoại.
  3. Định dạng ngữ cảnh cho LLM giải quyết đại từ thay thế (Anaphora).
  4. Phân lập phiên độc lập giữa các Track ID của Camera.
  5. Tự động dọn dẹp (Session Auto-Flush) khi người dân rời đi.
"""
import sys
import unittest
from pathlib import Path

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.rag.dialogue_manager import (
    SessionSlots,
    DialogueTurn,
    DialogueSession,
    DialogueSessionManager
)


class TestMultiTurnDialogue(unittest.TestCase):

    def setUp(self):
        self.mgr = DialogueSessionManager(max_history_turns=3, session_timeout_sec=60.0)

    def test_1_sliding_window_turns(self):
        """Kiểm tra cửa sổ trượt chỉ lưu đúng max_history_turns lượt gần nhất."""
        sess = self.mgr.get_session(track_id=1)
        self.assertEqual(len(sess.turns), 0)

        # Giả lập 5 lượt hỏi đáp liên tiếp
        for i in range(1, 6):
            sess.add_turn(f"Câu hỏi số {i}", f"Câu trả lời số {i}")

        # Chỉ được lưu 3 lượt gần nhất (Lượt 3, 4, 5)
        self.assertEqual(len(sess.turns), 3)
        self.assertEqual(sess.turns[0].user_query, "Câu hỏi số 3")
        self.assertEqual(sess.turns[1].user_query, "Câu hỏi số 4")
        self.assertEqual(sess.turns[2].user_query, "Câu hỏi số 5")

    def test_2_pinned_slots_preserved_indefinitely(self):
        """Kiểm tra Tầng 1: Thông tin cốt lõi đã ghim không bao giờ bị xóa dù hỏi tới 10 câu."""
        sess = self.mgr.get_session(track_id=1)
        sess.update_slots(
            procedure_name="Cấp thẻ Căn cước",
            target_citizen="Trẻ em 10 tuổi (dưới 14 tuổi)",
            action_type="Làm lần đầu"
        )

        # Hỏi liên tiếp 10 câu khác nhau
        for i in range(1, 11):
            sess.add_turn(f"Hỏi thêm câu {i}", f"Trả lời câu {i}")

        # Kiểm tra Tầng 1 vẫn nguyên vẹn 100%
        self.assertEqual(sess.slots.procedure_name, "Cấp thẻ Căn cước")
        self.assertEqual(sess.slots.target_citizen, "Trẻ em 10 tuổi (dưới 14 tuổi)")
        self.assertEqual(sess.slots.action_type, "Làm lần đầu")

    def test_3_build_llm_context(self):
        """Kiểm tra khối ngữ cảnh tạo ra cho LLM chứa cả thông tin ghim và các lượt thoại gần nhất."""
        sess = self.mgr.get_session(track_id=1)
        sess.update_slots(procedure_name="Đăng ký Tạm trú", target_citizen="Người ngoại tỉnh thuê nhà")
        sess.add_turn("Hồ sơ tạm trú cần gì?", "Cần tờ khai CT01 và hợp đồng thuê nhà.")
        sess.add_turn("Nộp ở đâu?", "Nộp tại Công an xã/phường nơi tạm trú.")

        ctx = sess.build_llm_context()
        self.assertIn("THÔNG TIN CỐT LÕI ĐÃ XÁC ĐỊNH", ctx)
        self.assertIn("Thủ tục chính: Đăng ký Tạm trú", ctx)
        self.assertIn("Người ngoại tỉnh thuê nhà", ctx)
        self.assertIn("LỊCH SỬ CÁC LƯỢT ĐỐI ĐÁP GẦN NHẤT", ctx)
        self.assertIn("Công dân: Nộp ở đâu?", ctx)
        self.assertIn("Robot: Nộp tại Công an xã/phường", ctx)

    def test_4_track_id_session_isolation(self):
        """Kiểm tra phiên của Người #1 và Người #2 hoàn toàn độc lập, không bị lẫn lộn thông tin."""
        sess_1 = self.mgr.get_session(track_id=1)
        sess_1.update_slots(procedure_name="Làm thẻ Căn cước")
        sess_1.add_turn("Hỏi về căn cước", "Trả lời căn cước")

        sess_2 = self.mgr.get_session(track_id=2)
        sess_2.update_slots(procedure_name="Đăng ký Kết hôn")
        sess_2.add_turn("Hỏi về kết hôn", "Trả lời kết hôn")

        # Xác minh phiên 1 không bị nhiễm thông tin của phiên 2
        self.assertEqual(sess_1.slots.procedure_name, "Làm thẻ Căn cước")
        self.assertEqual(len(sess_1.turns), 1)
        self.assertEqual(sess_1.turns[0].user_query, "Hỏi về căn cước")

        # Xác minh phiên 2 có dữ liệu riêng
        self.assertEqual(sess_2.slots.procedure_name, "Đăng ký Kết hôn")
        self.assertEqual(len(sess_2.turns), 1)
        self.assertEqual(sess_2.turns[0].user_query, "Hỏi về kết hôn")

    def test_5_session_auto_flush(self):
        """Kiểm tra khi Người #1 rời đi (camera không còn track ID 1), phiên 1 tự động bị xóa."""
        sess_1 = self.mgr.get_session(track_id=1)
        sess_2 = self.mgr.get_session(track_id=2)
        self.assertIn(1, self.mgr.sessions)
        self.assertIn(2, self.mgr.sessions)

        # Camera báo hiện tại chỉ còn Người #2 trong khung hình
        self.mgr.flush_inactive_sessions(active_track_ids=[2])

        # Phiên 1 phải biến mất khỏi bộ nhớ
        self.assertNotIn(1, self.mgr.sessions)
        # Phiên 2 vẫn được bảo tồn
        self.assertIn(2, self.mgr.sessions)

    def test_6_clarification_state_management(self):
        """Kiểm tra quản lý trạng thái chờ làm rõ (AWAITING_CLARIFICATION)."""
        sess = self.mgr.get_session(track_id=1)
        self.assertEqual(sess.state, "NORMAL")

        # Kích hoạt trạng thái hỏi lại
        sess.set_awaiting_clarification(
            raw_query="Làm cái này bao nhiêu tiền?",
            missing_slot="procedure_name"
        )
        self.assertEqual(sess.state, "AWAITING_CLARIFICATION")
        self.assertEqual(sess.pending_raw_query, "Làm cái này bao nhiêu tiền?")
        self.assertEqual(sess.pending_missing_slot, "procedure_name")

        # Khi người dân trả lời, giải phóng trạng thái chờ
        resolved_q = sess.resolve_clarification()
        self.assertEqual(resolved_q, "Làm cái này bao nhiêu tiền?")
        self.assertEqual(sess.state, "NORMAL")
        self.assertIsNone(sess.pending_raw_query)

    def test_7_slot_reset_on_procedure_change(self):
        """Kiểm tra khi chuyển sang thủ tục mới thì các slot phụ thuộc của thủ tục cũ được reset."""
        sess = self.mgr.get_session(track_id=1)
        sess.slots.update_from_query("Làm thẻ căn cước cho trẻ dưới 14 tuổi")
        self.assertEqual(sess.slots.procedure_name, "thẻ căn cước")
        self.assertEqual(sess.slots.target_citizen, "trẻ em dưới 14 tuổi")

        # Đổi sang thủ tục đăng ký tạm trú
        sess.slots.update_from_query("Tôi muốn đăng ký tạm trú")
        self.assertEqual(sess.slots.procedure_name, "đăng ký tạm trú")
        self.assertIsNone(sess.slots.target_citizen)


if __name__ == "__main__":
    unittest.main()
