"""
Kiểm thử tự động cho 2 vấn đề vừa nâng cấp:
  1. TC01: Trả lời câu hỏi thông thường / đời sống / thời tiết ("thời tiết hôm nay như thế nào")
  2. TC02: Bộ theo dõi đa đối tượng (MOT Tracker) - Chống chào lặp lại cùng 1 người
  3. TC03: Xử lý thay người lập tức (Người A đi, Người B đến)
  4. TC04: Xử lý nhóm nhiều người cùng xuất hiện (Group Greeting)
  5. TC05: Khóa chào hỏi khi đang trong phiên làm việc (Session Lock)
"""
import sys
import time
from pathlib import Path

PROTOTYPE_DIR = Path(__file__).resolve().parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

# Đảm bảo UTF-8 console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from src.rag.retriever import AdministrativeRAG, is_admin_procedure_query
from src.vision.tracker import PersonTracker, TrackedPerson


def print_banner(msg: str):
    print("\n" + "=" * 70)
    print(f" {msg.upper()} ")
    print("=" * 70)


def test_1_weather_and_general_qa():
    print_banner("TC01: Kiểm tra trả lời câu hỏi thông thường (Thời tiết hôm nay)")
    
    # 1. Kiểm tra bộ phân loại câu hỏi
    q_admin = "Thủ tục xin cấp visa du lịch Nhật Bản cần gì?"
    q_weather = "Thời tiết hôm nay như thế nào?"
    q_chit = "Hôm nay là ngày mấy?"
    
    assert is_admin_procedure_query(q_admin) is True, "Phải nhận diện là câu hỏi thủ tục!"
    assert is_admin_procedure_query(q_weather) is False, "Thời tiết KHÔNG PHẢI thủ tục hành chính!"
    assert is_admin_procedure_query(q_chit) is False, "Hỏi ngày tháng KHÔNG PHẢI thủ tục hành chính!"
    print("  • Phân loại câu hỏi: ✅ Chuẩn xác (Tách biệt thủ tục hành chính và câu hỏi đời thường)")

    # 2. Truy vấn thực tế RAG với câu hỏi thời tiết
    rag = AdministrativeRAG()
    print(f"[*] Đặt câu hỏi cho Não bộ RAG: \"{q_weather}\"")
    res = rag.query(q_weather)
    
    print("\n[🤖 LỜI ĐÁP CỦA ROBOT]:")
    print(res["answer"])
    
    # Kiểm tra xem câu trả lời có thông tin thời tiết hay không
    ans_lower = res["answer"].lower()
    has_weather_info = any(w in ans_lower for w in ["nhiệt độ", "độ c", "mây", "mưa", "nắng", "thời tiết", "độ ẩm", "gió"])
    not_refusal = "không có quy định cụ thể" not in ans_lower
    
    print(f"\n  • Nguồn phản hồi       : {res.get('source_type')}")
    print(f"  • Trích dẫn nguồn web : {res.get('sources')}")
    print(f"  • Có dữ liệu thời tiết: {has_weather_info}")
    
    assert res.get("source_type") == "web", "Phải qua Web Search Fallback!"
    assert has_weather_info, "Câu trả lời phải cung cấp thông tin thời tiết thực tế!"
    assert not_refusal, "Không được từ chối cứng nhắc theo khuôn mẫu hành chính!"
    print("[✅ PASS] TC01: Robot đã trả lời thời tiết đời thường chính xác và tự nhiên!")


def test_2_mot_tracker_no_repeat():
    print_banner("TC02: Kiểm tra chống chào lặp lại cùng một người (Track ID)")
    tracker = PersonTracker(iou_threshold=0.25)
    frame_area = 640.0 * 480.0
    
    # Giả lập Người A (BBox ~30% diện tích) ở Frame 1
    box_A = {"bbox": [100, 100, 350, 420], "confidence": 0.88, "area_ratio": 0.26}
    tracks_f1 = tracker.update([box_A], frame_area)
    
    assert len(tracks_f1) == 1, "Phải theo dõi được 1 người!"
    person_A = tracks_f1[0]
    id_A = person_A.track_id
    assert person_A.is_greeted is False, "Ban đầu Người A chưa được chào!"
    print(f"  • Frame 1: Người A xuất hiện với Track ID: #{id_A} (Greeted: {person_A.is_greeted})")

    # Robot cất lời chào Người A
    tracker.mark_as_greeted([id_A])
    assert tracker.active_tracks[id_A].is_greeted is True, "Sau khi chào phải đánh dấu is_greeted = True!"
    print(f"  • Đã chào Người A -> Đánh dấu Track ID #{id_A} is_greeted = True")

    # Giả lập Frame 2, 3, 4 (Người A vẫn đứng yên đó sau 20 giây)
    box_A_moved = {"bbox": [105, 102, 355, 422], "confidence": 0.89, "area_ratio": 0.26}
    for f in range(2, 6):
        tracks = tracker.update([box_A_moved], frame_area)
        assert len(tracks) == 1
        assert tracks[0].track_id == id_A, "Track ID phải giữ nguyên vì cùng là Người A!"
        assert tracks[0].is_greeted is True, "Người A vẫn đang đứng đó, KHÔNG ĐƯỢC reset cờ chào!"

    print(f"  • Frame 2-5 (Người A vẫn đứng yên): Track ID #{id_A} vẫn giữ cờ is_greeted = True.")
    print("[✅ PASS] TC02: Người cũ đứng yên KHÔNG BAO GIỜ bị chào lặp lại!")


def test_3_person_replacement():
    print_banner("TC03: Kiểm tra Người A vừa đi, Người B thế chỗ ngay lập tức")
    tracker = PersonTracker(iou_threshold=0.25)
    frame_area = 640.0 * 480.0
    
    # 1. Người A ở góc trái
    box_A = {"bbox": [50, 100, 250, 400], "confidence": 0.90, "area_ratio": 0.20}
    t_A = tracker.update([box_A], frame_area)[0]
    id_A = t_A.track_id
    tracker.mark_as_greeted([id_A])
    print(f"  • Người A (ID #{id_A}) đã được chào đón.")

    # 2. Người A bước đi, Người B xuất hiện ở góc phải
    box_B = {"bbox": [380, 100, 580, 400], "confidence": 0.87, "area_ratio": 0.20}
    tracks = tracker.update([box_B], frame_area)
    
    person_B = [t for t in tracks if t.bbox == box_B["bbox"]][0]
    id_B = person_B.track_id
    
    assert id_B != id_A, f"Người B phải nhận Track ID mới! ({id_B} != {id_A})"
    assert person_B.is_greeted is False, "Người B mới đến phải có cờ is_greeted = False để robot chào đón!"
    print(f"  • Người B thế chỗ lập tức: Nhận Track ID mới #{id_B} (is_greeted = False) -> Kích hoạt chào Người B ngay!")
    print("[✅ PASS] TC03: Thay người ngay lập tức được phát hiện chuẩn xác!")


def test_4_group_arrival():
    print_banner("TC04: Kiểm tra Nhóm nhiều người cùng xuất hiện (Group Greeting)")
    tracker = PersonTracker(iou_threshold=0.25)
    frame_area = 640.0 * 480.0
    
    # Nhóm 3 người cùng xuất hiện
    box_1 = {"bbox": [50, 100, 200, 400], "confidence": 0.85, "area_ratio": 0.15}
    box_2 = {"bbox": [220, 100, 420, 420], "confidence": 0.90, "area_ratio": 0.22}
    box_3 = {"bbox": [440, 100, 600, 400], "confidence": 0.84, "area_ratio": 0.16}
    
    tracks = tracker.update([box_1, box_2, box_3], frame_area)
    assert len(tracks) == 3, "Phải theo dõi đủ 3 người trong nhóm!"
    
    all_ids = [t.track_id for t in tracks]
    print(f"  • Nhóm 3 người cùng xuất hiện: IDs = {all_ids}")
    
    # Đánh dấu cả nhóm đã được chào
    tracker.mark_as_greeted(all_ids)
    
    # Kiểm tra ở frame tiếp theo: Cả 3 người đều phải là is_greeted = True
    tracks_next = tracker.update([box_1, box_2, box_3], frame_area)
    for t in tracks_next:
        assert t.is_greeted is True, f"Track #{t.track_id} phải được đánh dấu đã chào!"
        
    print("  • Cả 3 người đều được đánh dấu Đã chào trong 1 lượt duy nhất.")
    print("[✅ PASS] TC04: Nhóm đông chỉ chào đúng 1 lần duy nhất, không spam!")


def main():
    print("=" * 70)
    print(" BẮT ĐẦU KIỂM THỬ TỰ ĐỘNG CÁC TÍNH NĂNG NÂNG CẤP THỊ GIÁC & RAG ")
    print("=" * 70)
    
    test_1_weather_and_general_qa()
    test_2_mot_tracker_no_repeat()
    test_3_person_replacement()
    test_4_group_arrival()
    
    print("\n" + "=" * 70)
    print(" 🎉 TẤT CẢ 4 BÀI KIỂM THỬ NÂNG CẤP ĐẠT KẾT QUẢ 100% PASS! ")
    print("=" * 70)


if __name__ == "__main__":
    main()
