"""
Module tìm kiếm Internet dự phòng (Web Search Fallback) sử dụng Tavily AI Search API.
Dành riêng cho kiến trúc Adaptive RAG khi CSDL nội bộ không có dữ liệu (Out-of-Domain).
"""
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from src.config import TAVILY_API_KEY, ENABLE_WEB_SEARCH_FALLBACK

# Danh sách tên miền chính thống ưu tiên cho dịch vụ công Việt Nam
TRUSTED_GOV_DOMAINS = [
    "dichvucong.gov.vn",
    "chinhphu.vn",
    "thuvienphapluat.vn",
    "luatvietnam.vn",
    "bocongan.gov.vn",
    "moj.gov.vn"
]


class TavilyWebSearch:
    """Công cụ tìm kiếm web tối ưu cho AI RAG qua Tavily Search REST API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or TAVILY_API_KEY).strip()
        self.endpoint = "https://api.tavily.com/search"

    def is_configured(self) -> bool:
        """Kiểm tra xem API Key của Tavily đã được cấu hình hợp lệ chưa."""
        if not self.api_key:
            return False
        if self.api_key.lower() in ("your_tavily_api_key_here", "none", ""):
            return False
        return True

    def search(
        self,
        query: str,
        max_results: int = 3,
        prioritize_gov: bool = True,
        timeout: float = 6.0
    ) -> Dict[str, Any]:
        """
        Thực hiện tìm kiếm trên mạng:
        1. Ưu tiên lọc qua các domain chính thống (gov.vn, thuvienphapluat.vn,...)
        2. Nếu không có kết quả lọc, tự động mở rộng tìm kiếm toàn mạng.
        """
        if not self.is_configured():
            return {
                "success": False,
                "query": query,
                "results": [],
                "sources": [],
                "error": "TAVILY_API_KEY chưa được cấu hình trong file .env!"
            }

        start_time = time.time()
        
        # Thử lần 1: Lọc theo các domain chính phủ nếu prioritize_gov=True
        results = self._call_tavily_api(
            query=query,
            max_results=max_results,
            include_domains=TRUSTED_GOV_DOMAINS if prioritize_gov else None,
            timeout=timeout
        )

        # Nếu lọc domain mà không ra kết quả nào, tìm kiếm mở rộng không lọc domain
        if prioritize_gov and (not results or not results.get("results")):
            print("[*] Không tìm thấy kết quả từ domain chính phủ, đang mở rộng tìm kiếm toàn mạng...")
            results = self._call_tavily_api(
                query=query,
                max_results=max_results,
                include_domains=None,
                timeout=timeout
            )

        latency = round(time.time() - start_time, 2)
        if results.get("success"):
            results["latency_sec"] = latency

        return results

    def _call_tavily_api(
        self,
        query: str,
        max_results: int,
        include_domains: Optional[List[str]],
        timeout: float
    ) -> Dict[str, Any]:
        """Hàm nội bộ gọi REST API của Tavily."""
        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "max_results": max_results
        }
        if include_domains:
            payload["include_domains"] = include_domains

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            if response.status_code == 200:
                data = response.json()
                raw_results = data.get("results", [])
                
                clean_results = []
                sources = []
                for item in raw_results:
                    title = item.get("title", "").strip()
                    url = item.get("url", "").strip()
                    content = item.get("content", "").strip()
                    if content:
                        clean_results.append({
                            "title": title,
                            "url": url,
                            "content": content
                        })
                        if url:
                            sources.append(url)

                return {
                    "success": True,
                    "query": query,
                    "results": clean_results,
                    "sources": sources,
                    "error": None
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "query": query,
                    "results": [],
                    "sources": [],
                    "error": "TAVILY_API_KEY không hợp lệ hoặc đã hết hạn (HTTP 401)!"
                }
            elif response.status_code == 429:
                return {
                    "success": False,
                    "query": query,
                    "results": [],
                    "sources": [],
                    "error": "Đã vượt quá hạn mức miễn phí của Tavily (HTTP 429)!"
                }
            else:
                return {
                    "success": False,
                    "query": query,
                    "results": [],
                    "sources": [],
                    "error": f"Lỗi gọi Tavily API: HTTP {response.status_code}"
                }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "query": query,
                "results": [],
                "sources": [],
                "error": f"Quá thời gian chờ phản hồi tìm kiếm mạng ({timeout}s)!"
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "results": [],
                "sources": [],
                "error": f"Lỗi kết nối mạng: {e}"
            }


if __name__ == "__main__":
    searcher = TavilyWebSearch()
    print("=" * 60)
    print("KIỂM TRA CÔNG CỤ TÌM KIẾM TAVILY WEB SEARCH")
    print("=" * 60)
    print("Trạng thái cấu hình API Key:", "ĐÃ SẴN SÀNG" if searcher.is_configured() else "CHƯA CÓ KEY")
    if searcher.is_configured():
        test_q = "Thủ tục xin visa du lịch Nhật Bản mới nhất 2024"
        print(f"[*] Thử nghiệm tìm kiếm: \"{test_q}\"")
        res = searcher.search(test_q)
        print("Kết quả:", res)
    else:
        print("[!] Vui lòng điền TAVILY_API_KEY vào tệp .env để bắt đầu thử nghiệm.")
