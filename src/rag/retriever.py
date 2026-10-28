"""
Module truy vấn RAG và kiểm soát câu trả lời (Sprint 1 - Não bộ).
"""
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Thêm thư mục prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import (
    VECTOR_DB_DIR,
    SIMILARITY_THRESHOLD,
    ENABLE_WEB_SEARCH_FALLBACK,
    get_embedding_model,
    get_llm_model,
)
from src.rag.web_search import TavilyWebSearch

# System Prompt nghiêm ngặt cho dịch vụ hành chính công (tối ưu cho Robot phát âm thanh)
ADMIN_RAG_SYSTEM_PROMPT = """Bạn là Trợ lý AI thông minh hỗ trợ tư vấn dịch vụ hành chính công tại Việt Nam.
Nhiệm vụ của bạn là giải đáp thắc mắc của người dân một cách chính xác, lịch sự, rõ ràng và chuẩn mực.

QUY TẮC CỐT LÕI (BẮT BUỘC TUÂN THỦ):
1. CHỈ ĐƯỢC PHÉP TRẢ LỜI DỰA TRÊN [NGỮ CẢNH TÀI LIỆU] ĐƯỢC CUNG CẤP DƯỚI ĐÂY. Tuyệt đối không tự bịa đặt hoặc suy đoán thông tin ngoài tài liệu.
2. NẾU TÀI LIỆU KHÔNG CHỨA ĐỦ THÔNG TIN: Hãy trả lời chính xác:
   "Hiện tại trong cơ sở dữ liệu nội bộ chưa có quy định cụ thể về vấn đề này. Quý công dân vui lòng tra cứu thêm tại Cổng Dịch vụ công Quốc gia (dichvucong.gov.vn) hoặc liên hệ trực tiếp Bộ phận một cửa của cơ quan có thẩm quyền để được hướng dẫn chi tiết."
3. NẾU TÀI LIỆU CÓ THÔNG TIN: Trình bày câu trả lời súc tích, ngắn gọn và gãy gọn (vì câu trả lời sẽ được đọc ra loa ngoài cho người dân nghe):
   - Nêu trực diện các điều kiện, giấy tờ cần thiết, nơi nộp, thời hạn và lệ phí.
   - Mỗi mục chỉ tóm tắt 1-2 câu ngắn, đi thẳng vào trọng tâm, tránh viết thành bài văn quá dài.
4. TRÍCH DẪN NGUỒN: Cuối câu trả lời, luôn ghi rõ trích dẫn căn cứ pháp lý (Tên văn bản, Điều, Khoản) tìm thấy trong tài liệu.

[NGỮ CẢNH TÀI LIỆU]:
{context}
"""

# System Prompt cho tầng tìm kiếm mạng (Web Search Fallback)
WEB_SEARCH_SYSTEM_PROMPT = """Bạn là Trợ lý AI thông minh tư vấn dịch vụ hành chính công và hỗ trợ công dân tại Việt Nam.
Thời gian thực của hệ thống: {current_date}.
Cơ sở dữ liệu nội bộ chưa có thông tin này nên hệ thống đã tra cứu từ Internet.

NHIỆM VỤ CỦA BẠN:
1. Dựa trên [KẾT QUẢ TÌM KIẾM INTERNET] dưới đây, hãy tổng hợp câu trả lời ngắn gọn, lịch sự, đúng trọng tâm (tối đa 2-3 câu vì câu trả lời sẽ được đọc ra loa ngoài).
2. Đối với câu hỏi thủ tục hành chính / pháp lý: Nêu trực diện các điều kiện, giấy tờ cần thiết, nơi nộp hoặc thời hạn nếu thông tin có đề cập.
3. Đối với câu hỏi đời sống, thời tiết, tin tức hoặc kiến thức chung: Trả lời trực diện, tự nhiên thông tin tìm thấy (ví dụ: nhiệt độ, tình trạng mưa nắng, sự kiện chính trong ngày).
4. Không tự bịa đặt thông tin. Nếu kết quả tìm kiếm không có thông tin rõ ràng, hãy thông báo ngắn gọn.

[KẾT QUẢ TÌM KIẾM INTERNET]:
{context}
"""

# Danh sách từ khóa nhận diện câu hỏi thủ tục hành chính công
ADMIN_PROCEDURE_KEYWORDS = [
    "thủ tục", "hồ sơ", "giấy tờ", "lệ phí", "đăng ký",
    "căn cước", "hộ chiếu", "visa", "thị thực", "tạm trú",
    "thường trú", "kết hôn", "khai sinh", "khai tử", "đất đai",
    "sổ đỏ", "bảo hiểm", "thuế", "nghị định", "thông tư",
    "luật", "công an", "bộ phận một cửa", "dịch vụ công",
    "xử phạt", "mức phạt", "khiếu nại", "tố cáo"
]


def is_admin_procedure_query(query: str) -> bool:
    """Kiểm tra xem câu hỏi có thuộc nhóm thủ tục hành chính / pháp lý hay không."""
    q = query.lower()
    return any(kw in q for kw in ADMIN_PROCEDURE_KEYWORDS)


class AdministrativeRAG:
    def __init__(self, similarity_threshold: float = SIMILARITY_THRESHOLD):
        """Khởi tạo kết nối Vector Store, mô hình LLM và công cụ Web Search."""
        print("[*] Đang khởi tạo kết nối Vector Store (ChromaDB)...")
        self.similarity_threshold = similarity_threshold
        self.enable_web_search = ENABLE_WEB_SEARCH_FALLBACK
        self.web_searcher = TavilyWebSearch()
        self.embedding_fn = get_embedding_model()
        self.vector_store = Chroma(
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=self.embedding_fn
        )
        self.llm = get_llm_model(temperature=0.1)
        
        # Thiết lập Prompt Chain cho CSDL nội bộ
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", ADMIN_RAG_SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

        # Thiết lập Prompt Chain cho Web Search Fallback
        self.web_prompt = ChatPromptTemplate.from_messages([
            ("system", WEB_SEARCH_SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        self.web_chain = self.web_prompt | self.llm | StrOutputParser()

    def query_web_search(
        self,
        question: str,
        start_total: float,
        retrieval_latency: float
    ) -> Dict[str, Any]:
        """
        Tìm kiếm dự phòng trên Internet khi câu hỏi nằm ngoài CSDL nội bộ.
        Tự động phân loại:
          - Câu hỏi hành chính/pháp lý: Ưu tiên domain chính thống (.gov.vn, luatvietnam...).
          - Câu hỏi thời tiết/đời sống: Tìm kiếm mở rộng toàn mạng để lấy dữ liệu thời gian thực.
        """
        import datetime
        is_admin = is_admin_procedure_query(question)
        prioritize_gov = is_admin

        # Tối ưu hóa truy vấn nếu là câu hỏi thời tiết chung chung
        clean_q = question.strip(" ?.,!")
        search_query = clean_q
        q_lower = clean_q.lower()
        if "thời tiết" in q_lower:
            if not any(loc in q_lower for loc in ["hà nội", "tp.hcm", "hồ chí minh", "đà nẵng", "tại", "ở"]):
                search_query = f"Dự báo {q_lower} tại Việt Nam"
            else:
                search_query = f"Dự báo {q_lower}"

        search_mode = "Chính thống (Gov/Luật)" if prioritize_gov else "Mở rộng (Thời tiết/Đời sống)"
        print(f"[*] Đang kích hoạt Web Search Fallback qua Tavily AI Search [{search_mode}]...")
        search_res = self.web_searcher.search(search_query, max_results=3, prioritize_gov=prioritize_gov)
        
        if not search_res.get("success") or not search_res.get("results"):
            # Nếu tìm kiếm thất bại hoặc không có kết quả, trả về câu từ chối chuẩn
            print(f"[!] Tìm kiếm mạng không có kết quả hoặc gặp sự cố: {search_res.get('error')}")
            total_latency = time.time() - start_total
            return {
                "question": question,
                "answer": (
                    "Hiện tại trong cơ sở dữ liệu nội bộ chưa có quy định cụ thể về vấn đề này. "
                    "Quý công dân vui lòng tra cứu thêm tại Cổng Dịch vụ công Quốc gia (dichvucong.gov.vn) "
                    "hoặc liên hệ trực tiếp Bộ phận một cửa của cơ quan có thẩm quyền để được hướng dẫn chi tiết."
                ),
                "sources": [],
                "found_in_docs": False,
                "source_type": "refusal",
                "warning_issued": False,
                "latency": {
                    "retrieval_sec": round(retrieval_latency, 2),
                    "web_search_sec": search_res.get("latency_sec", 0.0),
                    "generation_sec": 0.0,
                    "total_sec": round(total_latency, 2)
                }
            }

        # Ghép ngữ cảnh từ kết quả tìm kiếm internet
        web_context_parts = []
        for i, item in enumerate(search_res["results"], 1):
            web_context_parts.append(
                f"--- [Nguồn web {i}: {item.get('title', 'Tài liệu')} - {item.get('url', '')}] ---\n"
                f"{item.get('content', '')}"
            )
        web_context_str = "\n\n".join(web_context_parts)

        # Gọi LLM tổng hợp lời giải đáp
        t1 = time.time()
        current_date_str = datetime.datetime.now().strftime("ngày %d/%m/%Y")
        try:
            raw_web_answer = self.web_chain.invoke({
                "context": web_context_str,
                "question": question,
                "current_date": current_date_str
            })
        except Exception as e:
            print(f"[!] Lỗi khi gọi LLM cho Web Search: {e}")
            raw_web_answer = "Hệ thống đã tìm thấy thông tin trên mạng nhưng gặp sự cố khi xử lý lời đáp."

        generation_latency = time.time() - t1
        total_latency = time.time() - start_total

        # Đính kèm Hộp Cảnh báo (Disclaimer Box) & Nguồn trích dẫn cho Màn hình hiển thị
        warning_header = (
            "⚠️ CẢNH BÁO TRA CỨU INTERNET:\n"
            "Thông tin dưới đây được tra cứu từ Internet (chưa có trong CSDL nội bộ đã thẩm định của cơ quan). "
            "Quý công dân vui lòng đối chiếu lại với cán bộ tại quầy hoặc Cổng Dịch vụ công Quốc gia (dichvucong.gov.vn).\n\n"
        )
        sources_footer = "\n\n📚 NGUỒN TRA CỨU INTERNET:\n" + "\n".join([f"- {url}" for url in search_res.get("sources", [])])
        formatted_answer = warning_header + raw_web_answer.strip() + sources_footer

        return {
            "question": question,
            "answer": formatted_answer,
            "sources": search_res.get("sources", []),
            "found_in_docs": False,
            "source_type": "web",
            "warning_issued": True,
            "latency": {
                "retrieval_sec": round(retrieval_latency, 2),
                "web_search_sec": search_res.get("latency_sec", 0.0),
                "generation_sec": round(generation_latency, 2),
                "total_sec": round(total_latency, 2)
            }
        }

    def query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """
        Thực hiện truy vấn câu hỏi người dân:
        1. Tìm kiếm k đoạn văn bản tương đồng nhất kèm relevance score
        2. Lọc theo similarity_threshold
        3. Nếu Out-of-Domain: Fallback sang Web Search (kèm Cảnh báo)
        4. Đo lường độ trễ (latency)
        """
        start_total = time.time()
        
        # 1. Truy xuất Vector DB kèm điểm tương đồng (Relevance Scores)
        t0 = time.time()
        try:
            docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(question, k=k)
        except Exception as e:
            print(f"[!] Lỗi truy vấn Vector Store: {e}")
            docs_with_scores = []
        retrieval_latency = time.time() - t0

        # Lọc các đoạn văn bản đạt ngưỡng tương đồng (P1 #7)
        relevant_docs = [doc for doc, score in docs_with_scores if score >= self.similarity_threshold]

        # Nếu không có tài liệu nào đạt ngưỡng tương đồng (câu hỏi ngoài phạm vi dữ liệu)
        if not relevant_docs:
            if self.enable_web_search and self.web_searcher.is_configured():
                return self.query_web_search(question, start_total, retrieval_latency)
            else:
                total_latency = time.time() - start_total
                return {
                    "question": question,
                    "answer": (
                        "Hiện tại trong cơ sở dữ liệu nội bộ chưa có quy định cụ thể về vấn đề này. "
                        "Quý công dân vui lòng tra cứu thêm tại Cổng Dịch vụ công Quốc gia (dichvucong.gov.vn) "
                        "hoặc liên hệ trực tiếp Bộ phận một cửa của cơ quan có thẩm quyền để được hướng dẫn chi tiết."
                    ),
                    "sources": [],
                    "found_in_docs": False,
                    "source_type": "refusal",
                    "warning_issued": False,
                    "latency": {
                        "retrieval_sec": round(retrieval_latency, 2),
                        "web_search_sec": 0.0,
                        "generation_sec": 0.0,
                        "total_sec": round(total_latency, 2)
                    }
                }

        # Ghép ngữ cảnh từ các tài liệu đạt chuẩn
        context_parts = []
        sources = []
        for i, doc in enumerate(relevant_docs, 1):
            source_file = doc.metadata.get("source_file", "Tài liệu nội bộ")
            sources.append(source_file)
            context_parts.append(f"--- [Trích đoạn {i} - Nguồn: {source_file}] ---\n{doc.page_content}")
            
        context_str = "\n\n".join(context_parts)

        # 2. Sinh câu trả lời qua LLM (bọc try-except chống sập do API / mạng - P1 #8)
        t1 = time.time()
        api_error = False
        try:
            answer = self.chain.invoke({
                "context": context_str,
                "question": question
            })
        except Exception as e:
            print(f"[!] Lỗi khi gọi mô hình ngôn ngữ (LLM): {e}")
            api_error = True
            answer = (
                "Rất tiếc, hệ thống đang gặp gián đoạn kết nối với máy chủ AI. "
                "Quý công dân vui lòng thử lại sau giây lát hoặc liên hệ cán bộ hướng dẫn tại quầy."
            )
        generation_latency = time.time() - t1
        total_latency = time.time() - start_total

        # Nhận diện xem câu trả lời có tìm thấy trong tài liệu không (loại trừ trường hợp lỗi API)
        found_in_docs = (
            not api_error
            and len(sources) > 0
            and not answer.strip().lower().startswith("hiện tại trong cơ sở dữ liệu nội bộ chưa có quy định cụ thể")
        )

        return {
            "question": question,
            "answer": answer,
            "sources": list(set(sources)),
            "found_in_docs": found_in_docs,
            "source_type": "local",
            "warning_issued": False,
            "latency": {
                "retrieval_sec": round(retrieval_latency, 2),
                "web_search_sec": 0.0,
                "generation_sec": round(generation_latency, 2),
                "total_sec": round(total_latency, 2)
            }
        }


def main():
    rag = AdministrativeRAG()
    test_question = "Làm thẻ căn cước cho trẻ dưới 14 tuổi thì cần làm những gì?"
    print("\n" + "=" * 60)
    print(f"[*] Câu hỏi thử nghiệm: {test_question}")
    print("=" * 60)
    res = rag.query(test_question)
    print("\n[+] Câu trả lời:")
    print(res["answer"])
    print("\n[*] Nguồn tài liệu:", res["sources"])
    print(f"[*] Độ trễ: Tìm kiếm {res['latency']['retrieval_sec']}s | LLM {res['latency']['generation_sec']}s | Tổng {res['latency']['total_sec']}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
