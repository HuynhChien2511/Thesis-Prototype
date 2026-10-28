"""
Tập lệnh kiểm thử tự động tính năng Adaptive RAG (Web Search Fallback).
Xác thực 3 kịch bản:
  1. Câu hỏi In-Domain (Căn cước) -> Trả lời từ CSDL nội bộ (Không cảnh báo).
  2. Câu hỏi Out-of-Domain (Visa Nhật Bản) -> Kích hoạt Web Search (Có Cảnh báo thị giác & giọng nói).
  3. Kịch bản khi tắt Web Search hoặc chưa có Key -> Từ chối lịch sự trong 0.05s (Không sập ứng dụng).
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

from src.rag.retriever import AdministrativeRAG
from src.audio.text_normalizer import normalize_for_tts
from src.config import TAVILY_API_KEY, ENABLE_WEB_SEARCH_FALLBACK


def run_web_rag_tests():
    print("=" * 80)
    print(" BẮT ĐẦU KIỂM THỬ TÍNH NĂNG ADAPTIVE RAG (WEB SEARCH FALLBACK) ")
    print("=" * 80)
    
    rag = AdministrativeRAG()
    is_key_ready = rag.web_searcher.is_configured()
    print(f"[*] Cấu hình Web Search: {'BẬT' if rag.enable_web_search else 'TẮT'}")
    print(f"[*] Trạng thái Tavily API Key: {'ĐÃ CẤU HÌNH' if is_key_ready else 'CHƯA ĐIỀN (Vào .env)'}\n")

    test_results = []

    # ------------------------------------------------------------------
    # TEST CASE 1: CÂU HỎI TRONG PHẠM VI (IN-DOMAIN) -> LOCAL DB
    # ------------------------------------------------------------------
    print("-" * 80)
    print("▶ [TC01] KIỂM THỬ TRUY VẤN NỘI BỘ (IN-DOMAIN -> LOCAL CHROMADB)")
    print("-" * 80)
    q1 = "Làm thẻ căn cước cho trẻ dưới 14 tuổi thì cần những giấy tờ gì?"
    print(f"[*] Câu hỏi: \"{q1}\"")
    t0 = time.time()
    res1 = rag.query(q1)
    latency1 = round(time.time() - t0, 2)
    
    pass1 = (
        res1.get("source_type") == "local"
        and res1.get("found_in_docs") is True
        and res1.get("warning_issued") is False
        and "⚠️ CẢNH BÁO" not in res1["answer"]
    )
    print(f"[+] Nguồn phản hồi: {res1.get('source_type', '').upper()}")
    print(f"[+] Cảnh báo phát sinh: {res1.get('warning_issued')}")
    print(f"[+] Trích dẫn nguồn: {res1.get('sources')}")
    print(f"[+] Độ trễ xử lý: {latency1}s")
    print(f"[*] Kết quả: {'✅ PASS' if pass1 else '❌ FAIL'}")
    test_results.append(("TC01: Local In-domain (Không cảnh báo)", pass1, f"{latency1}s"))

    # ------------------------------------------------------------------
    # TEST CASE 2: CÂU HỎI NGOÀI MIỀN (OUT-OF-DOMAIN) -> WEB SEARCH FALLBACK
    # ------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("▶ [TC02] KIỂM THỬ TRA CỨU MẠNG DỰ PHÒNG (OUT-OF-DOMAIN -> WEB SEARCH)")
    print("-" * 80)
    q2 = "Thủ tục xin visa du lịch Nhật Bản tự túc cần những giấy tờ gì?"
    print(f"[*] Câu hỏi ngoài miền: \"{q2}\"")
    t0 = time.time()
    res2 = rag.query(q2)
    latency2 = round(time.time() - t0, 2)

    if is_key_ready:
        pass2 = (
            res2.get("source_type") == "web"
            and res2.get("warning_issued") is True
            and "⚠️ CẢNH BÁO TRA CỨU INTERNET" in res2["answer"]
        )
        print(f"[+] Nguồn phản hồi: {res2.get('source_type', '').upper()} (Tavily Search)")
        print(f"[+] Cảnh báo phát sinh: {res2.get('warning_issued')}")
        print(f"[+] URL trích dẫn: {res2.get('sources')[:2]}")
        
        # Kiểm tra kênh phát âm (TTS Normalizer) có biến cảnh báo thành giọng nói tự nhiên không
        spoken_text = normalize_for_tts(res2["answer"])
        has_voice_caveat = "lưu ý: thông tin sau được tôi tra cứu từ internet" in spoken_text.lower()
        print(f"[+] Kiểm tra giọng đọc loa: {'✅ ĐÃ CHÈN LỜI NHẮC CẢNH BÁO' if has_voice_caveat else '❌ CHƯA CHÈN'}")
        pass2 = pass2 and has_voice_caveat
    else:
        # Nếu chưa điền key, hệ thống phải fallback về từ chối an toàn
        pass2 = (
            res2.get("source_type") == "refusal"
            and "chưa có quy định cụ thể" in res2["answer"]
        )
        print(f"[!] Tavily Key chưa điền -> Tự động chuyển về từ chối lịch sự an toàn ({latency2}s)")

    print(f"[+] Độ trễ xử lý: {latency2}s")
    print(f"[*] Kết quả: {'✅ PASS' if pass2 else '❌ FAIL'}")
    test_results.append(("TC02: Out-of-domain Fallback (Có cảnh báo)", pass2, f"{latency2}s"))

    # ------------------------------------------------------------------
    # TEST CASE 3: TẮT WEB SEARCH -> FAST REFUSAL (0.05S)
    # ------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("▶ [TC03] KIỂM THỬ KHI TẮT CỜ TÌM KIẾM MẠNG (ENABLE_WEB_SEARCH = FALSE)")
    print("-" * 80)
    rag.enable_web_search = False  # Giả lập tắt tìm kiếm
    q3 = "Cách làm món phở bò Hà Nội truyền thống?"
    print(f"[*] Câu hỏi ngoài miền khi tắt Web Search: \"{q3}\"")
    t0 = time.time()
    res3 = rag.query(q3)
    latency3 = round(time.time() - t0, 2)
    
    pass3 = (
        res3.get("source_type") == "refusal"
        and res3.get("warning_issued") is False
        and res3["latency"]["generation_sec"] == 0.0
    )
    print(f"[+] Nguồn phản hồi: {res3.get('source_type', '').upper()} (Từ chối nhanh)")
    print(f"[+] Độ trễ: {latency3}s (Cắt luồng siêu tốc không tốn token)")
    print(f"[*] Kết quả: {'✅ PASS' if pass3 else '❌ FAIL'}")
    test_results.append(("TC03: Tắt Web Search -> Fast Refusal", pass3, f"{latency3}s"))

    # ------------------------------------------------------------------
    # BẢNG TỔNG KẾT
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" BẢNG TỔNG KẾT KIỂM THỬ ADAPTIVE RAG (WEB SEARCH FALLBACK) ")
    print("=" * 80)
    print(f"{'Kịch bản kiểm thử':<45} | {'Thời gian':<10} | {'Trạng thái'}")
    print("-" * 80)
    for name, p, lat in test_results:
        status = "✅ PASS" if p else "❌ FAIL"
        print(f"{name:<45} | {lat:<10} | {status}")
    print("=" * 80)


if __name__ == "__main__":
    run_web_rag_tests()
