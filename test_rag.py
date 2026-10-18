"""
Script kiểm thử tự động bộ não RAG cho Dịch vụ Hành chính công (Sprint 1 Benchmark).
"""
import sys
import json
from pathlib import Path

# Thêm thư mục prototype vào sys.path
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

from src.rag.retriever import AdministrativeRAG

TEST_CASES = [
    {
        "id": "TC01",
        "type": "In-domain (Căn cước)",
        "question": "Cho tôi hỏi trẻ em dưới 14 tuổi thì làm thẻ căn cước thế nào, có bắt buộc không?"
    },
    {
        "id": "TC02",
        "type": "In-domain (Tạm trú)",
        "question": "Đăng ký tạm trú mất bao nhiêu ngày làm việc và hồ sơ gồm những gì?"
    },
    {
        "id": "TC03",
        "type": "In-domain (Kết hôn)",
        "question": "Đăng ký kết hôn tại UBND cấp xã có mất tiền lệ phí không và cần bao nhiêu tuổi?"
    },
    {
        "id": "TC04",
        "type": "Natural Variation (VNeID)",
        "question": "Tôi có thể đăng ký tạm trú trực tiếp trên điện thoại qua VNeID được không?"
    },
    {
        "id": "TC05",
        "type": "Out-of-domain (Chống ảo giác)",
        "question": "Tôi muốn xin giấy phép xây dựng nhà ở 3 tầng thì cần chuẩn bị hồ sơ gì?"
    }
]

def run_benchmark():
    print("=" * 80)
    print(" BẮT ĐẦU KIỂM THỬ ĐÁNH GIÁ BỘ NÃO RAG - HÀNH CHÍNH CÔNG ")
    print("=" * 80)
    
    rag = AdministrativeRAG()
    results = []

    for case in TEST_CASES:
        print(f"\n▶ [{case['id']}] Loại: {case['type']}")
        print(f"  Câu hỏi: \"{case['question']}\"")
        print("  Đang xử lý truy vấn RAG...")
        
        res = rag.query(case["question"])
        
        print("\n  [CÂU TRẢ LỜI]:")
        for line in res["answer"].split("\n"):
            print(f"    {line}")
            
        print(f"\n  [NGUỒN TRÍCH DẪN]: {res['sources']}")
        print(f"  [TÌM THẤY TRONG TÀI LIỆU]: {'CÓ' if res['found_in_docs'] else 'KHÔNG (Đúng cơ chế bảo vệ)'}")
        print(f"  [ĐỘ TRỄ]: Tìm kiếm {res['latency']['retrieval_sec']}s | LLM {res['latency']['generation_sec']}s | Tổng {res['latency']['total_sec']}s")
        print("-" * 80)
        
        results.append({
            "id": case["id"],
            "type": case["type"],
            "question": case["question"],
            "found_in_docs": res["found_in_docs"],
            "latency": res["latency"]
        })

    # Tổng kết hiệu năng
    avg_total_latency = sum(r["latency"]["total_sec"] for r in results) / len(results)
    avg_gen_latency = sum(r["latency"]["generation_sec"] for r in results) / len(results)
    
    print("\n" + "=" * 80)
    print(" BẢNG TỔNG KẾT HIỆU NĂNG SPRINT 1 ")
    print("=" * 80)
    print(f"Tổng số test case thực thi: {len(results)}")
    print(f"Độ trễ trung bình toàn trình: {avg_total_latency:.2f} giây")
    print(f"Độ trễ trung bình sinh câu trả lời (LLM): {avg_gen_latency:.2f} giây")
    print("=" * 80)

if __name__ == "__main__":
    run_benchmark()
