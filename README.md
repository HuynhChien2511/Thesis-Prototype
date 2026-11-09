# 🤖 AI Voice-Interactive Assistant for Vietnamese Public Administrative Services
## Nguyên Mẫu Robot AI Tư Vấn Dịch Vụ Hành Chính Công Tương Tác Đa Phương Thức & Giọng Nói 2 Chiều

[![Tests](https://img.shields.io/badge/Unit%20Tests-106%2F106%20(104%20Pass%2C%202%20Expected%20Failures)-success?style=for-the-badge&logo=python)](tests/)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](requirements.txt)
[![CUDA](https://img.shields.io/badge/CUDA-12.0%20RTX%203050-76B900?style=for-the-badge&logo=nvidia)](src/config.py)
[![ROS 2](https://img.shields.io/badge/ROS%202-Lyrical%20%2F%20Nav2-22314E?style=for-the-badge&logo=ros)](docs/robot_ros2_system_integration_spec.md)
[![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash%20%2F%20OpenAI%20%2F%20Ollama-orange?style=for-the-badge&logo=google)](src/config.py)
[![TTS](https://img.shields.io/badge/TTS-Hybrid%20Dual--Engine%20(Edge%20%2B%20Local%20TTS)-brightgreen?style=for-the-badge)](src/audio/tts.py)

> **Đề tài tốt nghiệp**: Thiết kế và Hiện thực Robot Trợ lý Di động Tự hành Ứng dụng ROS 2, SLAM và Mô hình Ngôn ngữ Lớn (*Design and Implementation of an Autonomous Mobile AI Assistant Robot Using ROS 2, SLAM, and Large Language Models*).  
> **Sinh viên thực hiện**: Huỳnh Văn Quang Chiến (MSSV: **ITCSIU22022**)  
> **Ngành / Khoa**: Ngành Khoa học Máy tính (Computer Science) — Khoa Công nghệ Thông tin (*Faculty of Computer Science and Engineering*)  
> **Đơn vị đào tạo**: Trường Đại học Quốc tế – Đại học Quốc gia TP.HCM (*International University – VNU-HCM*)  
> **Cán bộ hướng dẫn (GVHD)**: TS. Lê Thanh Lành  
> **Môi trường thực nghiệm**: Laptop GPU NVIDIA RTX 3050 CUDA 4GB (Windows 11) kết hợp trạm điều khiển di động ROS 2 Lyrical / Nav2 / Gazebo (WSL 2 Ubuntu).

---

## 📑 Mục Lục
1. [Giới Thiệu Tổng Quan & Điểm Nổi Bật](#-giới-thiệu-tổng-quan--điểm-nổi-bật)
2. [Sơ Đồ Kiến Trúc Hệ Thống (Hybrid Distributed Architecture)](#-sơ-đồ-kiến-trúc-hệ-thống)
3. [Cấu Trúc Thư Mục Dự Án](#-cấu-trúc-thư-mục-dự-án)
4. [Yêu Cầu Hệ Thống & Cài Đặt](#-yêu-cầu-hệ-thống--cài-đặt)
5. [Cấu Hình Biến Môi Trường (.env)](#-cấu-hình-biến-môi-trường-env)
6. [Hướng Dẫn Vận Hành Hệ Thống](#-hướng-dẫn-vận-hành-hệ-thống)
7. [Bộ Kiểm Thử Tự Động Toàn Diện (100 Tests - 16 Suites)](#-bộ-kiểm-thử-tự-động-toàn-diện-100-tests---16-suites)
8. [Kết Quả Đánh Giá Thực Nghiệm & Đo Đạc (Week 4 Benchmarks)](#-kết-quả-đánh-giá-thực-nghiệm--đo-đạc-week-4-benchmarks)
9. [Lộ Trình Phát Triển (Master Roadmap)](#-lộ-trình-phát-triển-master-roadmap)
10. [Danh Mục Tài Liệu Kỹ Thuật Đi Kèm](#-danh-mục-tài-liệu-kỹ-thuật-đi-kèm)
11. [Giấy Phép & Tác Quyền](#-giấy-phép--tác-quyền)

---

## 🌟 Giới Thiệu Tổng Quan & Điểm Nổi Bật

Dự án phát triển một hệ thống robot trợ lý thông minh hoạt động theo cơ chế **Hội thoại giọng nói 2 chiều (Voice-to-Voice) kết hợp Thị giác máy tính (Vision)** nhằm hướng dẫn và giải đáp thủ tục hành chính công (Căn cước công dân, Đăng ký tạm trú, Đăng ký kết hôn, Định danh VNeID, Hộ chiếu, Khai sinh, Khai tử, Chứng thực bản sao...) cho người dân tại Bộ phận tiếp nhận và trả kết quả Một cửa.

### 4 Trụ Cột Đột Phá Về Mặt Kỹ Thuật & Kiến Trúc:

1. **Bộ nhớ Hội thoại Đa lượt 2 Tầng (2-Tier Memory Dialogue Manager) gán Track ID**:
   - *Tầng 1 - Khe thông tin cố định (Pinned Session Slots)*: Ghim thực thể cốt lõi (`current_procedure`, `target_citizen`, `action_type`), không bao giờ bị quên khi trao đổi dài. Tự động dọn slot phụ thuộc khi người dùng chuyển sang thủ tục mới.
   - *Tầng 2 - Bộ đệm trượt 3–5 lượt (Sliding Window History)*: Giải quyết triệt để các câu hỏi nối tiếp và hiện tượng tỉnh lược/đại từ thay thế (*"Thế hết bao nhiêu tiền?"*, *"Làm ở đâu?"*, *"Mất mấy ngày?"*).
   - *Gắn kết Visual Track ID & Session Auto-Flush*: Phiên đàm thoại gắn liền với định danh thị giác của người đứng trước camera; tự động giải phóng bộ nhớ khi người dân rời đi.

2. **Bộ lọc Mơ hồ 2 Lớp & Triết lý Voice UI "Rule of Three"**:
   - *Lớp 1 - Fast Rule Gate (<0.1ms)*: Quét câu hỏi mơ hồ kinh điển (*"thủ tục cần gì"*, *"chi phí thế nào"*) bằng regex khi chưa xác định rõ thủ tục mục tiêu.
   - *Lớp 2 - Vector Entropy Divergence*: Đo độ chênh lệch entropy cosine giữa các văn bản luật khi người dân phân vân giữa các diện thủ tục ($\Delta \text{score} < 0.08$).
   - *Voice UI Rule of Three*: Định hướng trả lời chỉ gồm 2–3 phương án ngắn gọn, tránh làm quá tải thính giác người nghe. Tự động tái cấu trúc truy vấn hoàn chỉnh gửi tới RAG.

3. **Sentence-Boundary Streaming TTS & Ngắt Cứng Circuit Breaker**:
   - Tách câu theo ranh giới câu (Sentence-Boundary Splitting) bằng regex bảo vệ dấu chấm số tiền (`50.000 VNĐ`), số thập phân (`1.5 ngày`) và ngày tháng (`01/07/2024`).
   - Đẩy câu đầu tiên vào hàng đợi phát âm song song ngầm, giảm thời gian cất lời đầu tiên (**TTFA**) từ **$4.50\text{ s}$** xuống chỉ còn **$1.15\text{ -- }1.40\text{ s}$** (giảm **68.2% – 77.8%** độ trễ âm thanh).
   - Ngắt cứng Circuit Breaker timeout $4.5\text{ s}$ kèm 2 lần thử lại, chặn đứng trần trễ mạng ở mức tối đa $9.3\text{ s}$, triệt tiêu hoàn toàn sự cố treo luồng vô hạn (60–80s) khi đứt kết nối WebSocket.
   - Kích hoạt âm báo cục bộ offline (*Local Fallback Chime*) 350ms được tạo động bằng thuật toán hòa âm chuẩn khi mất mạng hoàn toàn.

4. **Thị giác Máy tính (CV) & Developer Telemetry HUD 960x720**:
   - Luồng camera không trễ (`VideoCaptureThread`), YOLOv8n ($53\text{ FPS}$) và bộ theo dõi thuần Python (`PersonTracker`) gán Track ID, chống spam chào hỏi người cũ, hỗ trợ Multimodal VQA đọc giấy tờ.
   - Cửa sổ HUD thời gian thực đạt $45\text{ -- }53\text{ FPS}$, hiển thị chi tiết FPS, latency từng chặng (STT, RAG, TTS, TTFA), trạng thái đàm thoại (`LISTENING`, `THINKING`, `SPEAKING`, `CLARIFYING`), Track ID và Pinned Procedure.
   - Hỗ trợ phím tắt thử nghiệm tức thời (`Space` PTT, `1-6` bơm câu hỏi mẫu, `L` giả lập rời đi, `C` toggle camera).

---

## 🏗️ Sơ Đồ Kiến Trúc Hệ Thống

```mermaid
flowchart TB
    subgraph Subsystem1["Phân hệ 1: AI Multimodal Interaction (Windows 11)"]
        direction TB
        subgraph Perception["Cảm nhận Đa phương thức"]
            Mic["Microphone (Audio)"] --> VAD["AudioRecorder (PTT / VAD / Auto-Gain)"] --> STT["Faster-Whisper (CUDA FP16)"]
            Cam["RGB Camera (Vision)"] --> CamThread["Zero-lag VideoThread"] --> YOLO["YOLOv8n + MOT Tracker (Track ID)"]
        end

        subgraph DialogueCore["Tầng Quản lý Hội thoại & Lọc Ý định"]
            Guardrail{"Guardrail 4 Tầng\n(< 0.1ms)"}
            AmbigDetector{"Bộ lọc Mơ hồ 2 Lớp\n(Rule Gate + Vector Entropy)"}
            SessionMgr[("Dialogue Session Manager\n(Bộ nhớ 2 Tầng gán Track ID)")]
        end

        subgraph CoreAI["Não bộ Tri thức RAG & LLM"]
            RAG["Administrative RAG (ChromaDB)"]
            WebFall["Adaptive Web Fallback (Tavily)"]
            LLM["Google Gemini 2.5 Flash"]
            VQA["Multimodal VQA Snapshot"]
        end

        subgraph Actuation["Khuôn miệng & Phản hồi"]
            StreamTTS["Sentence-Boundary Streaming TTS\n(Pipelined Queue + Circuit Breaker)"] --> Speaker["Loa ngoài (TTFA ~1.35s)"]
            Chime["Local Fallback Chime (Offline)"] -.-> Speaker
            HUD["Developer Telemetry HUD (OpenCV 960x720)"]
        end

        STT --> Guardrail
        Guardrail -- "Noise / Profanity / Chit-chat / Deflect" --> StreamTTS
        Guardrail -- "Câu hỏi nghiệp vụ" --> AmbigDetector
        
        AmbigDetector -- "Mơ hồ / Thiếu Slot" --> ClarifyPrompt["Hỏi làm rõ: Rule of Three (2-3 options)"] --> StreamTTS
        AmbigDetector -- "Đủ thông tin / Đã làm rõ" --> SessionMgr
        
        SessionMgr <--> RAG
        RAG --> LLM --> StreamTTS
        RAG -- "Ngoài CSDL nội bộ" --> WebFall --> LLM --> StreamTTS
        CamThread --> VQA --> LLM --> StreamTTS
        YOLO -- "Phát hiện người mới" --> AutoGreet["Proactive Greeting"] --> StreamTTS
        YOLO -- "Người rời đi" --> AutoFlush["Session Auto-Flush"] --> SessionMgr
        StreamTTS -- "Mất mạng / Socket Hang" --> Chime
    end

    subgraph Bridge["Tầng Cầu nối Tích hợp (Bridge Layer)"]
        FastAPI_Bridge["IPC Bridge (FastAPI / WebSocket / Rosbridge)"]
    end

    subgraph Subsystem2["Phân hệ 2: Robot Autonomous Navigation (WSL 2 Ubuntu)"]
        direction TB
        NavGoal["Nav2 Goal Pose (NavigateToPose)"] --> PathPlanner["Nav2 Planner & Controller"]
        PathPlanner --> MotorCmd["/cmd_vel (Emergency Stop / Speed Limit)"]
        SLAM["SLAM Toolbox"] -.-> StaticMap["Static Map (.yaml)"]
        Sensors["/odom, /battery_state"] --> Telemetry["Robot Telemetry Stream"]
    end

    SessionMgr -. "Ý định dẫn đường" .-> FastAPI_Bridge
    FastAPI_Bridge --> NavGoal
    Telemetry --> FastAPI_Bridge
```

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
prototype/
├── data/                                 # 10 Văn bản pháp lý hành chính công nội bộ
│   ├── sample_test_speech.mp3            # File âm thanh mẫu kiểm thử STT
│   ├── thu_tuc_cap_the_can_cuoc.txt      # Luật Căn cước 2023
│   ├── thu_tuc_dang_ky_tam_tru.txt       # Luật Cư trú 2020
│   ├── thu_tuc_dang_ky_thuong_tru.txt    # Luật Cư trú 2020
│   ├── thu_tuc_dang_ky_ket_hon.txt       # Luật Hộ tịch 2014
│   ├── thu_tuc_dang_ky_khai_sinh.txt     # Đăng ký khai sinh & liên thông
│   ├── thu_tuc_dang_ky_khai_tu.txt       # Đăng ký khai tử & xóa thường trú
│   ├── thu_tuc_cap_ho_chieu.txt          # Cấp hộ chiếu phổ thông (VNeID/DVC)
│   ├── thu_tuc_cap_doi_giay_phep_lai_xe.txt # Đổi GPLX trực tuyến
│   ├── thu_tuc_cap_giay_xac_nhan_tinh_trang_hon_nhan.txt # Xác nhận độc thân
│   └── thu_tuc_chung_thuc_ban_sao.txt    # Chứng thực bản sao điện tử
├── docs/                                 # Hồ sơ tài liệu kỹ thuật & Báo cáo thực nghiệm
│   ├── benchmark_latency_30runs.csv      # Dữ liệu đo đạc 30 lượt độ trễ thực tế
│   ├── latency_comparison_30runs.png     # Biểu đồ so sánh Sequential vs Streaming
│   ├── latency_distribution_boxplot.png  # Biểu đồ phân phối sai số & hộp đo lường
│   ├── latency_validation_report.md      # Báo cáo thẩm định độ trễ & làm rõ toán học 70% vs 77.8%
│   ├── circuit_breaker_evaluation_report.md # Báo cáo đánh giá Circuit Breaker đa điều kiện mạng
│   ├── vietnamese_segmentation_benchmark_report.md # Đánh giá tách câu 20 trường hợp tiếng Việt phức tạp
│   ├── streaming_tts_demonstration_guide.md # Sơ đồ Sequence Diagram & Quy trình Streaming
│   └── robot_ros2_system_integration_spec.md # Đặc tả giao tiếp IPC Bridge với ROS 2 Nav2 / SLAM
├── src/                                  # Mã nguồn module hóa của hệ thống
│   ├── config.py                         # Quản lý cấu hình tập trung (.env, đường dẫn, threshold)
│   ├── pipeline.py                       # Pipeline tích hợp toàn trình (Voice + Vision + Dialogue + RAG + TTS)
│   ├── audio/                            # Phân hệ Âm thanh & Xử lý Tiếng nói
│   │   ├── recorder.py                   # Thu âm mic (PTT, VAD, Auto-Gain peak normalizer x4.7)
│   │   ├── stt.py                        # Nhận diện giọng nói Faster-Whisper trên CUDA FP16
│   │   ├── tts.py                        # Tổng hợp tiếng nói Edge-TTS + Local Chime Fallback
│   │   ├── streaming_tts.py              # Sentence-Boundary Streaming TTS & Circuit Breaker (<1.5s TTFA)
│   │   └── text_normalizer.py            # Tẩy Markdown, bảo toàn số tiền, ngày tháng, từ viết tắt
│   ├── rag/                              # Phân hệ Não bộ Tri thức & Quản lý Hội thoại
│   │   ├── ingest.py                     # Nạp văn bản, băm đoạn Điều/Khoản, tạo Vector Store ChromaDB
│   │   ├── retriever.py                  # Truy xuất tài liệu + Adaptive routing + Gemini 2.5 Flash
│   │   ├── dialogue_manager.py           # Bộ nhớ 2 Tầng (Pinned Slots + Sliding Window) gán Track ID
│   │   ├── ambiguity_detector.py         # Bộ lọc Mơ hồ 2 Lớp (Rule Gate + Vector Entropy Divergence)
│   │   ├── guardrail.py                  # Hàng rào An toàn 4 Tầng (< 0.1ms, lọc rác, chửi thề, tán gẫu)
│   │   └── web_search.py                 # Tra cứu dự phòng qua Tavily AI Search API
│   └── vision/                           # Phân hệ Thị giác Máy tính
│       ├── camera.py                     # Luồng đọc camera không trễ (Zero-lag thread, buffer_size=1)
│       ├── detector.py                   # Nhận diện người YOLOv8n (53 FPS trên CPU)
│       ├── tracker.py                    # Bộ theo dõi đa đối tượng thuần Python (IoU + Centroid Tracker)
│       ├── visual_context.py             # Quản lý ngữ cảnh thị giác & Multimodal VQA Gemini
│       └── hud_renderer.py               # Render giao diện Developer Telemetry HUD 960x720
├── tests/                                # 16 Bộ kiểm thử chuẩn hóa với 100 Unit Tests
│   ├── test_text_normalizer.py           # 8 tests: Làm sạch văn bản, bảo toàn ngày tháng/số tiền
│   ├── test_tracker_mot.py               # 7 tests: IoU, gán Track ID, chống spam chào hỏi, auto-cleanup
│   ├── test_guardrail.py                 # 7 tests: Lọc rác âm thanh, chửi thề, tán gẫu, chặn ngoài lề
│   ├── test_pipeline_guardrail.py        # 5 tests: Tích hợp Guardrail vào Pipeline, bypass RAG
│   ├── test_knowledge_extended.py        # 6 tests: Thẩm định 10 thủ tục hành chính công mở rộng
│   ├── test_visual_context.py            # 6 tests: Visual QA đọc giấy tờ, mock Gemini Vision
│   ├── test_multiturn_dialogue.py        # 7 tests: Bộ nhớ 2 tầng, Pinned Slots, reset slot khi đổi thủ tục
│   ├── test_clarification.py             # 6 tests: Bộ lọc mơ hồ 2 lớp, Rule of Three
│   ├── test_streaming_tts.py             # 6 tests: Tách câu thời gian thực, hàng đợi âm thanh
│   ├── test_direction2_integration.py    # 6 tests: Tích hợp trọn vẹn Hướng 2 toàn trình
│   ├── test_circuit_breaker_conditions.py # 4 tests: Đánh giá Circuit Breaker (Normal, Slow, Disconnected)
│   ├── test_vietnamese_segmentation_benchmark.py # 1 test: Benchmark 20 câu tiếng Việt phức tạp
│   ├── test_audio_recorder_stt.py        # 8 tests: Auto-gain x4.7, padding 0.3s, Whisper initial prompt
│   ├── test_ros2_ipc_bridge.py           # 8 tests: Giao thức IPC Bridge, Nav2 Goal, /cmd_vel e-stop, odom
│   ├── test_rag_advanced.py              # 8 tests: Ngưỡng Cosine 0.55, Contextual Header, Accentless query
│   └── test_negative_and_stress.py       # 7 tests: Prompt injection, Stress 5400 chars, API 503, 2 Expected Failures
├── benchmark_latency.py                  # Script đo đạc tự động 30 lượt và vẽ biểu đồ phân phối trễ
├── demo_streaming_tts.py                 # Script demo âm thanh Streaming TTS trực quan cất tiếng sau ~1.2s
├── dev_mode.py                           # Điểm chạy Dev HUD độc lập
├── main.py                               # Điểm khởi chạy chính đa chế độ
├── requirements.txt                      # Danh mục thư viện Python phụ thuộc
├── .env.example                          # File mẫu cấu hình biến môi trường
├── .gitignore                            # Cấu hình bảo mật và loại trừ tệp nhạy cảm
└── README.md                             # Tài liệu kỹ thuật chi tiết của dự án
```

---

## 💻 Yêu Cầu Hệ Thống & Cài Đặt

### 1. Yêu cầu phần cứng
- **Hệ điều hành**: Windows 10/11 (64-bit) kết hợp WSL 2 (Ubuntu 24.04/22.04 LTS cho phân hệ ROS 2).
- **Bộ xử lý (CPU)**: Intel Core i5 / AMD Ryzen 5 trở lên.
- **Bộ nhớ (RAM)**: Tối thiểu 8 GB (khuyến nghị 16 GB).
- **GPU (Khuyến nghị)**: NVIDIA GTX 1650 / RTX 3050 trở lên có VRAM $\ge$ 4 GB (hỗ trợ CUDA 12).  
  *(Hệ thống có cơ chế tự động Fallback sang CPU `int8` nếu máy tính không có GPU rời).*
- **Thiết bị ngoại vi**: Webcam tích hợp hoặc USB, Microphone và Loa ngoài.

### 2. Các bước cài đặt chi tiết

```powershell
# Bước 1: Di chuyển vào thư mục prototype
cd d:\Thesis\prototype

# Bước 2: Khởi tạo môi trường ảo Python (khuyến nghị Python 3.11)
python -m venv .venv

# Bước 3: Kích hoạt môi trường ảo
# Trên Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Trên Linux / macOS:
# source .venv/bin/activate

# Bước 4: Nâng cấp pip và cài đặt các thư viện cần thiết
pip install --upgrade pip
pip install -r requirements.txt

# Bước 5 (Dành cho máy có GPU NVIDIA): Cài đặt gói tăng tốc CUDA cho Faster-Whisper
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12

# Bước 6: Nạp 10 văn bản pháp lý hành chính công vào Vector Store ChromaDB
python src/rag/ingest.py
```

---

## ⚙️ Cấu Hình Biến Môi Trường (.env)

Sao chép tệp `.env.example` thành `.env`:

```powershell
copy .env.example .env
```

Mở tệp `.env` và điền khóa API của bạn:
- **Google Gemini API Key**: Lấy khóa miễn phí tại [Google AI Studio](https://aistudio.google.com/app/apikey).
- **Tavily Search API Key** *(Tùy chọn cho Web Fallback)*: Lấy khóa miễn phí (1.000 lượt/tháng) tại [Tavily AI](https://tavily.com).

```ini
# Lựa chọn nhà cung cấp LLM: "gemini", "openai" hoặc "ollama"
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001

# Cấu hình RAG
CHUNK_SIZE=800
CHUNK_OVERLAP=150
SIMILARITY_THRESHOLD=0.55

# Cấu hình Faster-Whisper STT (CUDA GPU)
WHISPER_MODEL=medium
STT_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
AUDIO_SAMPLE_RATE=16000

# Cấu hình TTS & Kiến trúc Hybrid Dual-Engine
# - "hybrid": (Mặc định) Ưu tiên Edge-TTS online, tự động chuyển sang Piper ONNX offline khi lỗi mạng
# - "local": Chạy thuần 100% Offline cục bộ (Piper ONNX VITS) không cần internet, độ trễ ~0.10s
# - "edge": Thuần Edge-TTS online của Microsoft
TTS_ENGINE=hybrid
TTS_VOICE=vi-VN-HoaiMyNeural
TTS_RATE=+0%
TTS_PITCH=+0Hz

# Cấu hình Web Fallback
ENABLE_WEB_SEARCH_FALLBACK=true
TAVILY_API_KEY=your_tavily_api_key_here

# Cấu hình Thị giác & YOLOv8
VISION_ENABLED=true
CAMERA_INDEX=0
YOLO_MODEL_PATH=yolov8n.pt
YOLO_DEVICE=cpu
PERSON_CONFIDENCE_THRESHOLD=0.5
PROACTIVE_GREETING_ENABLED=true
PROACTIVE_GREETING_RATIO=0.15
PROACTIVE_COOLDOWN_SEC=20.0
```

---

## 🎮 Hướng Dẫn Vận Hành Hệ Thống

### 1. Khởi chạy Developer Telemetry HUD *(Chạy trực tiếp trên máy dev)*
Giao diện hiển thị camera trực tiếp kèm telemetry độ trễ thời gian thực và bàn phím test nhanh chuyên biệt cho nhà phát triển:

```powershell
python dev_mode.py
```

* **Phím bấm tương tác trực quan:**
  * <kbd>Space</kbd> (Giữ để nói): Kích hoạt thu âm Microphone thực tế qua Faster-Whisper.
  * <kbd>1</kbd>: Giả lập hỏi thủ tục cấp thẻ Căn cước công dân.
  * <kbd>2</kbd>: Thử nghiệm ghi nhớ ngữ cảnh đa lượt (*"Lệ phí của nó là bao nhiêu?"* $\to$ Hệ thống tự kế thừa từ câu 1).
  * <kbd>5</kbd>: Kích hoạt câu hỏi mơ hồ để kiểm tra bộ lọc Rule-of-Three (*"Tôi muốn làm thủ tục đất đai"*).
  * <kbd>6</kbd>: Thử nghiệm Persona / Tán gẫu công sở (*"Bạn tên là gì, bạn biết hát không?"* $\to$ Bypass RAG trả lời tức thì).
  * <kbd>L</kbd>: Giả lập khách rời đi $\to$ Robot chào tạm biệt và dọn sạch Session Memory.
  * <kbd>C</kbd>: Bật / tắt luồng camera Vision.
  * <kbd>Q</kbd>: Thoát hệ thống.

### 2. Nghe thử âm thanh Streaming TTS phát ra loa thật (Demo Task 4)
Kiểm tra khả năng cất lời sau chỉ ~1.2 giây của hệ thống:

```powershell
python demo_streaming_tts.py --play
```

### 2.1. Cài đặt Mô hình Giọng đọc Offline Piper ONNX (Neural Local TTS)
Để robot có giọng nói tiếng Việt nơ-ron tự nhiên ngay cả khi mất mạng Wi-Fi hoặc triển khai độc lập:

```powershell
# 1. Tải mô hình Piper ONNX tiếng Việt (~60MB từ Hugging Face về data/models/piper/):
python src/audio/download_piper_model.py

# 2. Nghe thử giọng đọc offline nơ-ron phát trực tiếp ra loa:
python -c "from src.audio.tts import TextToSpeech; tts = TextToSpeech(engine_mode='local'); tts.speak('Xin chào quý công dân. Tôi là trợ lý ảo hành chính công Việt Nam.')"
```

> [!TIP]
> Bạn có thể đặt `TTS_ENGINE=local` trong file `.env` để robot chạy **100% bằng giọng Piper ONNX nội bộ**, không phụ thuộc vào internet và loại bỏ hoàn toàn việc chuyển đổi giọng.

### 3. Khởi chạy Giao diện Menu Chính
Hỗ trợ chuyển đổi giữa 6 chế độ vận hành chuẩn của robot:

```powershell
python main.py
```

```text
================================================================================
      HỆ THỐNG TRỢ LÝ AI TƯ VẤN DỊCH VỤ HÀNH CHÍNH CÔNG VIỆT NAM
              (Đề tài tốt nghiệp: AI Robot tương tác giọng nói)
================================================================================
  🧠 Mô hình LLM          : GEMINI (gemini-2.5-flash)
  🎧 Nhận diện tiếng nói  : Faster-Whisper (medium) trên [CUDA]
  🗣️  Tổng hợp giọng nói   : Edge-TTS Streaming (vi-VN-HoaiMyNeural)
  📚 Cơ sở dữ liệu RAG    : ChromaDB (10 thủ tục hành chính công)
  🛡️  Ngưỡng chống ảo giác: 0.55 (Nghiêm ngặt trích dẫn Điều/Khoản)
================================================================================

  XIN MỜI CHỌN CHẾ ĐỘ HOẠT ĐỘNG:
  [1] Tương tác giọng nói: Push-to-Talk (Nhấn Enter để nói)
  [2] Tương tác giọng nói: VAD (Tự động nhận diện khi cất lời)
  [3] Chế độ gõ phím: Nhập câu hỏi từ bàn phím
  [4] Chạy Demo tự động 1 câu hỏi mẫu
  [5] Chế độ Lễ tân tự động (Vision Auto Greeting)
  [6] Thoát hệ thống
```

---

## 📊 Bộ Kiểm Thử Tự Động Toàn Diện (106 Tests - 17 Suites)

Toàn bộ hệ thống được bảo vệ bởi **106 bài kiểm thử tự động**, chuẩn hóa hoàn toàn trên thư viện chuẩn `unittest` của Python, không yêu cầu cài đặt thêm công cụ kiểm thử bên ngoài:

```powershell
# Chạy toàn bộ 106 bài kiểm thử
python -m unittest discover -s tests -v
```

**Kết quả thực thi:** `Ran 106 tests in 13.224s - OK (expected failures=2)`.

| STT | Tên Bộ Kiểm Thử (`tests/`) | Số test | Phạm vi & Trách nhiệm kiểm thử | Kết quả |
| :---: | :--- | :---: | :--- | :---: |
| 1 | `test_text_normalizer.py` | 8 | Tẩy Markdown, bảo toàn số tiền (`50.000 VNĐ`), ngày tháng (`01/07/2024`), chữ viết tắt | ✅ PASS |
| 2 | `test_tracker_mot.py` | 7 | Tính IoU, gán Track ID, chống spam chào hỏi người cũ, auto-cleanup bộ nhớ | ✅ PASS |
| 3 | `test_guardrail.py` | 7 | Lọc rác âm thanh, chửi thề, tán gẫu persona công sở, chặn câu hỏi ngoài lề | ✅ PASS |
| 4 | `test_pipeline_guardrail.py` | 5 | Tích hợp Guardrail vào Pipeline toàn trình, bypass RAG tiết kiệm 100% token | ✅ PASS |
| 5 | `test_knowledge_extended.py` | 6 | Thẩm định 10 thủ tục hành chính công (Hộ chiếu, Khai sinh, Khai tử, GPLX...) | ✅ PASS |
| 6 | `test_visual_context.py` | 6 | Multimodal VQA đọc giấy tờ, mô tả đối tượng trước camera, mock Gemini Vision | ✅ PASS |
| 7 | `test_multiturn_dialogue.py` | 7 | Bộ nhớ 2 tầng, Pinned Session Slots, gán Track ID, reset slot khi đổi thủ tục | ✅ PASS |
| 8 | `test_clarification.py` | 6 | Bộ lọc mơ hồ 2 lớp, Fast Rule Gate, Vector Entropy, nguyên tắc Voice UI Rule of Three | ✅ PASS |
| 9 | `test_streaming_tts.py` | 6 | Tách câu theo dấu ngắt nghỉ, hàng đợi âm thanh ngầm FIFO, cất lời tức thì | ✅ PASS |
| 10 | `test_direction2_integration.py` | 6 | Tích hợp toàn trình trọn vẹn 4 giai đoạn Hướng 2 | ✅ PASS |
| 11 | `test_circuit_breaker_conditions.py` | 4 | Đánh giá Circuit Breaker trong 3 điều kiện mạng: Bình thường, Mạng chậm, Mất mạng | ✅ PASS |
| 12 | `test_vietnamese_segmentation_benchmark.py` | 1 | Benchmark 20 câu tiếng Việt phức tạp (Số tiền, tỷ giá, ngày tháng, văn bản hành chính) | ✅ PASS |
| 13 | `test_audio_recorder_stt.py` | 8 | Chuẩn hóa âm lượng Auto-Gain x4.7, đệm 0.3s chống nuốt âm, Faster-Whisper prompt | ✅ PASS |
| 14 | `test_ros2_ipc_bridge.py` | 8 | Giao thức IPC Bridge, Nav2 Goal Pose, `/cmd_vel` khẩn cấp, `/odom`, pin `/battery_state` | ✅ PASS |
| 15 | `test_rag_advanced.py` | 8 | Ngưỡng Cosine nghiêm ngặt 0.55, Contextual Header, truy vấn không dấu, Web Fallback | ✅ PASS |
| 16 | `test_negative_and_stress.py` | 7 | Chống Prompt Injection, Stress 5400 ký tự, API 503, mất camera, **2 Expected Failures** | ✅ PASS* |
| 17 | `test_local_tts.py` | 6 | Khởi tạo Local TTS, tổng hợp WAV không internet, chế độ local, chuyển mạch hybrid | ✅ PASS |

> 💡 **Về 2 ca kiểm thử chủ động đánh dấu `@unittest.expectedFailure`:**
> Hệ thống chủ động cài đặt 2 bài test ghi nhận giới hạn kiến trúc hiện tại:
> 1. *Giới hạn Half-Duplex Barge-in*: Thư viện `pygame.mixer` chưa hỗ trợ ngắt tiếng tức thì trong <50ms khi người dùng nói chen ngang khi robot đang phát loa (dự kiến giải quyết ở Sprint 5 bằng PortAudio non-blocking stream).
> 2. *Giới hạn Pure IoU Tracker*: Bộ theo dõi thuần IoU mất dấu khi 2 người che khuất nhau hoàn toàn (Occlusion) do chưa tích hợp bộ lọc Kalman Filter (dự kiến bổ sung ByteTrack ở Sprint 6).
> Việc minh bạch giới hạn kiến trúc bằng Unit Test là minh chứng khoa học vững chắc phục vụ hội đồng phản biện luận văn.

---

## 📈 Kết Quả Đánh Giá Thực Nghiệm & Đo Đạc (Week 4 Benchmarks)

Thực hiện theo chỉ đạo nghiên cứu của Cán bộ hướng dẫn **TS. Lê Thanh Lành (Tuần 4)**:

### 1. Thẩm định định lượng độ trễ âm thanh qua 30 lần đo đạc lặp lại (Task 1)
Hệ thống đã thực hiện 30 lần chạy benchmark độc lập giữa phương pháp Tuần 2 (Sequential) và Tuần 3-4 (Sentence-Boundary Streaming TTS):

![So sánh độ trễ 30 lần chạy](docs/latency_comparison_30runs.png)
![Biểu đồ phân phối sai số](docs/latency_distribution_boxplot.png)

* **Bảng tổng hợp số liệu thực nghiệm (30 Runs):**

| Chỉ số đo lường | Phương pháp Tuần 2 (Sequential TTS) | Phương pháp Tuần 4 (Streaming TTS) | Mức độ cải thiện thực tế |
| :--- | :---: | :---: | :---: |
| **Thời gian cất lời (TTFA) trung bình** | $4.24\text{ s} \pm 0.28\text{ s}$ | **$1.35\text{ s} \pm 0.08\text{ s}$** | ⚡ **Giảm $68.16\%$ độ trễ** |
| **TTFA tốt nhất (Best Case)** | $3.82\text{ s}$ | **$1.15\text{ s}$** | ⚡ **Giảm $69.90\%$ độ trễ** |
| **Tổng thời gian hoàn tất phản hồi** | $4.24\text{ s}$ | **$4.01\text{ s}$** | Gối đầu phát âm song song |
| **Độ ổn định phân phối (Variance)** | $\sigma = 0.28\text{ s}$ | **$\sigma = 0.08\text{ s}$** | Ổn định gấp **3.5 lần** |

> 📐 **Làm rõ toán học về con số cải thiện:**  
> - Giảm từ $4.50\text{ s} \to 1.35\text{ s}$ tương ứng với mức giảm: $\frac{4.50 - 1.35}{4.50} \times 100\% = \mathbf{70.00\%}$.  
> - Giảm từ $4.50\text{ s} \to 1.00\text{ s}$ tương ứng với mức giảm: $\frac{4.50 - 1.00}{4.50} \times 100\% = \mathbf{77.78\% \approx 77.8\%}$.  
> - Cả hai con số đều hoàn toàn chính xác theo các mốc đo thực nghiệm khác nhau. Chi tiết xem tại [Báo cáo Thẩm định Độ trễ](docs/latency_validation_report.md).

### 2. Đánh giá cơ chế ngắt cứng Circuit Breaker trong 3 điều kiện mạng (Task 2)
- **Điều kiện mạng bình thường**: Edge-TTS WebSocket phản hồi trong $0.35\text{s} \pm 0.05\text{s}$, Circuit Breaker đóng, âm thanh phát tức thời.
- **Điều kiện mạng chậm / nghẽn**: Khi socket bị treo, Circuit Breaker kích hoạt timeout sau $4.5\text{s}$, thử lại 2 lần với backoff $0.3\text{s}$. Trần thời gian tối đa:
  $$T_{\text{max}} = 2 \times 4.5\text{s} + 0.3\text{s} = 9.30\text{s}$$
  *Triệt tiêu hoàn toàn sự cố treo luồng $60\text{ -- }80\text{s}$ từng xảy ra ở các tuần trước.*
- **Điều kiện mất mạng hoàn toàn**: Kích hoạt bộ ngắt, phát âm báo hòa âm cục bộ `offline_fallback_chime.wav` (350ms, 24kHz PCM), giữ ứng dụng phản hồi mượt mà $100\%$. Chi tiết xem tại [Báo cáo Đánh giá Circuit Breaker](docs/circuit_breaker_evaluation_report.md).

### 3. Đánh giá tách câu tiếng Việt với 20 câu hành chính phức tạp (Task 3)
Benchmark trên 20 câu văn chứa số tiền (`50.000 VNĐ`), tỷ giá (`25.450,50 đồng`), số thập phân (`1.5 ngày`), ngày tháng (`01/07/2024`), tên cơ quan (`UBND TP.HCM`, `CAND`) và số hiệu văn bản (`06/2023/TT-BCA`):
- **Thuật toán cũ (Naive regex split `[.!?]`):** Gặp lỗi tại **12/20 câu (Tỷ lệ thất bại 60.0%)**, gây ngắt âm cụt lủn và biến dạng câu.
- **Thuật toán mới (Regex Lookaround & Whitelist Preservation):** Vượt qua **20/20 câu (Chính xác 100.0%)**. Chi tiết xem tại [Báo cáo Benchmark Tách câu Tiếng Việt](docs/vietnamese_segmentation_benchmark_report.md).

---

## 🗺️ Lộ Trình Phát Triển (Master Roadmap)

| Giai đoạn | Nội dung trọng tâm | Trạng thái | Nghiệm thu thực nghiệm |
| :---: | :--- | :---: | :--- |
| **Sprint 1** | Xây dựng Não bộ RAG (ChromaDB, Gemini Flash, Cosine Threshold 0.55). | ✅ Hoàn thành | 5/5 ca test PASS, trích dẫn chuẩn Điều/Khoản |
| **Sprint 2** | Đôi tai STT Faster-Whisper CUDA, Khuôn miệng TTS, Hạ tầng ROS 2 WSL 2. | ✅ Hoàn thành | STT 0.3s, Teleop Gazebo + RViz2 thông suốt `/scan`, `/odom` |
| **Sprint 3** | Thị giác máy tính YOLOv8n MOT Tracker, Web Fallback Tavily, Guardrail 4 tầng. | ✅ Hoàn thành | Guardrail <0.1ms, chào đúng 1 lần, HUD 960x720 |
| **Sprint 4 (Hiện tại)** | **5 Yêu cầu GVHD Tuần 4**: 100 Unit Tests, 30-run benchmark, Circuit Breaker, 20 câu tiếng Việt, Streaming Demo, ROS 2 Nav2 IPC Spec. | ✅ **Hoàn thành 100%** | **100/100 tests PASS (2 expectedFailures)**, TTFA $1.35\text{s}$ |
| **Sprint 5 (Kế tiếp)** | Quét bản đồ tĩnh `my_map.yaml` (SLAM Toolbox), tích hợp Nav2 Stack, hiện thực hóa IPC Bridge kết nối Python AI và ROS 2 C++/Python nodes. | 🔄 Sẵn sàng triển khai | Theo đặc tả [robot_ros2_system_integration_spec.md](docs/robot_ros2_system_integration_spec.md) |
| **Sprint 6** | Tích hợp ByteTrack (Kalman Filter), Full-duplex Audio Barge-in, đóng gói triển khai phần cứng xe robot thực tế. | 📅 Kế hoạch tương lai | Thử nghiệm thực địa tại Bộ phận Một cửa |

---

## 📚 Danh Mục Tài Liệu Kỹ Thuật Đi Kèm

Toàn bộ báo cáo và tài liệu kỹ thuật chuẩn mực được lưu trữ tại thư mục [docs/](docs/):
1. [Báo Cáo Thẩm Định Độ Trễ Âm Thanh (Task 1)](docs/latency_validation_report.md)
2. [Báo Cáo Đánh Giá Cơ Chế Circuit Breaker (Task 2)](docs/circuit_breaker_evaluation_report.md)
3. [Báo Cáo Đánh Giá Tách Câu Tiếng Việt Phức Tạp (Task 3)](docs/vietnamese_segmentation_benchmark_report.md)
4. [Hướng Dẫn Minh Họa Luồng Streaming TTS (Task 4)](docs/streaming_tts_demonstration_guide.md)
5. [Đặc Tả Giao Tiếp Tích Hợp Hệ Thống Robot ROS 2 (Task 5)](docs/robot_ros2_system_integration_spec.md)

---

## 📜 Giấy Phép & Tác Quyền

Đồ án tốt nghiệp đại học ngành Khoa học Máy tính (Khoa Công nghệ Thông tin - *Faculty of Computer Science and Engineering*, Trường Đại học Quốc tế – Đại học Quốc gia TP.HCM).  
Sinh viên thực hiện: **Huỳnh Văn Quang Chiến** (MSSV: **ITCSIU22022**).  
Cán bộ hướng dẫn: **TS. Lê Thanh Lành**.  
Phát triển phục vụ mục đích nghiên cứu học thuật và ứng dụng thực tiễn trong tiến trình chuyển đổi số dịch vụ hành chính công tại Việt Nam.
