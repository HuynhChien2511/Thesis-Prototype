import os
import sys
import warnings
from pathlib import Path

# Bỏ qua cảnh báo lấy mẫu cố định vô hại từ thư viện langchain_google_genai
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_google_genai")

# Đảm bảo in tiếng Việt UTF-8 chuẩn trên Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

try:
    from dotenv import load_dotenv
    PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
    ENV_FILE = PROTOTYPE_DIR / ".env"
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=True)
    else:
        load_dotenv(PROTOTYPE_DIR / ".env.example")
except ImportError:
    PROTOTYPE_DIR = Path(__file__).resolve().parent.parent

# Đường dẫn thư mục dữ liệu và vector db
DATA_DIR = PROTOTYPE_DIR / "data"
VECTOR_DB_DIR = PROTOTYPE_DIR / "vector_db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# Cấu hình LLM Provider: "gemini", "openai", "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")

# RAG parameters
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.55"))

# Audio & STT Settings
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "1"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", os.getenv("STT_MODEL", "small"))
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", os.getenv("STT_DEVICE", "cuda"))
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
TTS_VOICE = os.getenv("TTS_VOICE", "vi-VN-HoaiMyNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")

# Web Search Fallback Settings (Tavily Search API)
ENABLE_WEB_SEARCH_FALLBACK = os.getenv("ENABLE_WEB_SEARCH_FALLBACK", "true").lower() in ("true", "1", "yes")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Vision Settings (Computer Vision & YOLOv8)
VISION_ENABLED = os.getenv("VISION_ENABLED", "true").lower() in ("true", "1", "yes")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480"))
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", str(Path(__file__).resolve().parent.parent.parent / "yolov8n.pt"))
YOLO_DEVICE = os.getenv("YOLO_DEVICE", "0")  # "0" for CUDA GPU, "cpu" for CPU
YOLO_IMGSZ = int(os.getenv("YOLO_IMGSZ", "320"))
PERSON_CONFIDENCE_THRESHOLD = float(os.getenv("PERSON_CONFIDENCE_THRESHOLD", "0.5"))
PROACTIVE_GREETING_ENABLED = os.getenv("PROACTIVE_GREETING_ENABLED", "true").lower() in ("true", "1", "yes")
PROACTIVE_GREETING_RATIO = float(os.getenv("PROACTIVE_GREETING_RATIO", "0.20"))  # bbox area / frame area
PROACTIVE_COOLDOWN_SEC = float(os.getenv("PROACTIVE_COOLDOWN_SEC", "20.0"))


def get_embedding_model():
    """Khởi tạo Embedding model dựa trên cấu hình LLM_PROVIDER."""
    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        api_key = GOOGLE_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("Chưa tìm thấy GOOGLE_API_KEY trong file .env!")
        return GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBEDDING_MODEL,
            google_api_key=api_key
        )
    elif LLM_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        if not OPENAI_API_KEY:
            raise ValueError("Chưa tìm thấy OPENAI_API_KEY trong file .env!")
        return OpenAIEmbeddings(
            model=OPENAI_EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY
        )
    elif LLM_PROVIDER == "ollama":
        from langchain_community.embeddings import OllamaEmbeddings
        return OllamaEmbeddings(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_EMBEDDING_MODEL
        )
    else:
        raise ValueError(f"Không hỗ trợ LLM_PROVIDER: {LLM_PROVIDER}")


def get_llm_model(temperature: float = 0.1):
    """Khởi tạo LLM Chat model dựa trên cấu hình LLM_PROVIDER."""
    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = GOOGLE_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("Chưa tìm thấy GOOGLE_API_KEY trong file .env!")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=api_key,
            temperature=temperature
        )
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        if not OPENAI_API_KEY:
            raise ValueError("Chưa tìm thấy OPENAI_API_KEY trong file .env!")
        return ChatOpenAI(
            model=OPENAI_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=temperature
        )
    elif LLM_PROVIDER == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=temperature
        )
    else:
        raise ValueError(f"Không hỗ trợ LLM_PROVIDER: {LLM_PROVIDER}")
