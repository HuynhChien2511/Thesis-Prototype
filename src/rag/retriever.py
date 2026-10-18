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
    get_embedding_model,
    get_llm_model,
)

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

class AdministrativeRAG:
    def __init__(self, similarity_threshold: float = SIMILARITY_THRESHOLD):
        """Khởi tạo kết nối Vector Store và mô hình LLM."""
        print("[*] Đang khởi tạo kết nối Vector Store (ChromaDB)...")
        self.similarity_threshold = similarity_threshold
        self.embedding_fn = get_embedding_model()
        self.vector_store = Chroma(
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=self.embedding_fn
        )
        self.llm = get_llm_model(temperature=0.1)
        
        # Thiết lập Prompt Chain
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", ADMIN_RAG_SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """
        Thực hiện truy vấn câu hỏi người dân:
        1. Tìm kiếm k đoạn văn bản tương đồng nhất kèm relevance score
        2. Lọc theo similarity_threshold
        3. Gửi cho LLM sinh câu trả lời (có try-except bắt lỗi kết nối/quota)
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
                "latency": {
                    "retrieval_sec": round(retrieval_latency, 2),
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
            "latency": {
                "retrieval_sec": round(retrieval_latency, 2),
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
