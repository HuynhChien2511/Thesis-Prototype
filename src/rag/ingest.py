"""
Module nạp và vector hóa tài liệu hành chính công vào ChromaDB (Sprint 1 - Não bộ).
"""
import sys
import shutil
from pathlib import Path
from typing import List

# Thêm thư mục prototype vào sys.path
PROTOTYPE_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROTOTYPE_DIR) not in sys.path:
    sys.path.append(str(PROTOTYPE_DIR))

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader
)

from src.config import (
    DATA_DIR,
    VECTOR_DB_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    get_embedding_model,
)

def load_all_documents() -> List[Document]:
    """Quét và đọc tất cả các file .txt, .pdf, .docx trong thư mục data/."""
    docs: List[Document] = []
    
    if not DATA_DIR.exists():
        print(f"[!] Thư mục dữ liệu không tồn tại: {DATA_DIR}")
        return docs

    for file_path in DATA_DIR.glob("*.*"):
        ext = file_path.suffix.lower()
        try:
            if ext == ".txt":
                loader = TextLoader(str(file_path), encoding="utf-8")
                loaded = loader.load()
            elif ext == ".pdf":
                loader = PyPDFLoader(str(file_path))
                loaded = loader.load()
            elif ext == ".docx":
                loader = Docx2txtLoader(str(file_path))
                loaded = loader.load()
            else:
                continue
            
            # Gắn thêm metadata tên file ngắn gọn để trích dẫn
            for d in loaded:
                d.metadata["source_file"] = file_path.name
            docs.extend(loaded)
            print(f"[+] Đã đọc: {file_path.name} ({len(loaded)} trang/đoạn)")
        except Exception as e:
            print(f"[-] Lỗi khi đọc file {file_path.name}: {e}")

    return docs


def split_administrative_documents(docs: List[Document]) -> List[Document]:
    """
    Tách đoạn thông minh theo cấu trúc Điều/Khoản của văn bản hành chính Việt Nam.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\nĐiều ",      # Ưu tiên ngắt theo từng Điều luật
            "\nKhoản ",     # Ngắt theo Khoản
            "\n\n",         # Ngắt theo đoạn văn đôi
            "\n",           # Ngắt theo dòng
            " "             # Ngắt theo từ
        ],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False
    )
    chunks = text_splitter.split_documents(docs)
    print(f"[+] Tổng số chunks được tạo: {len(chunks)}")
    return chunks


def build_vector_store():
    """Quy trình chính: Nạp tài liệu -> Tách chunk -> Tạo Chroma Vector Store."""
    import shutil

    print("=" * 60)
    print("[1/3] Bắt đầu nạp tài liệu từ thư mục:", DATA_DIR)
    docs = load_all_documents()
    if not docs:
        print("[!] Không tìm thấy tài liệu nào trong thư mục data/!")
        return None

    print("[2/3] Băm nhỏ tài liệu theo cấu trúc pháp lý...")
    chunks = split_administrative_documents(docs)

    print("[3/3] Đang nhúng vector (Embedding) và lưu vào ChromaDB...")
    embedding_fn = get_embedding_model()
    
    # Xóa sạch vector store cũ nếu đã tồn tại để tránh nhân bản dữ liệu (duplicate chunks)
    if VECTOR_DB_DIR.exists() and any(VECTOR_DB_DIR.iterdir()):
        try:
            print(f"[*] Đang làm sạch cơ sở dữ liệu cũ tại: {VECTOR_DB_DIR}")
            shutil.rmtree(VECTOR_DB_DIR)
            VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[!] Cảnh báo không thể xóa thư mục cũ ({e}), tiến hành ghi đè...")

    # Tạo persistent vector store
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_fn,
        persist_directory=str(VECTOR_DB_DIR)
    )
    print(f"[SUCCESS] Đã lưu cơ sở dữ liệu Vector bền vững tại: {VECTOR_DB_DIR}")
    print("=" * 60)
    return vector_store


if __name__ == "__main__":
    build_vector_store()
