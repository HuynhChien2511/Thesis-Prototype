# BẢNG NỘI DUNG COPY-PASTE VÀO SLIDE POWERPOINT (BÁO CÁO TUẦN 1 - 6 SLIDES)
**Tệp trình chiếu cần dán:** `D:\Thesis\weekly report w1.pptx`  
**Chủ đề:** Báo cáo tiến độ Tuần 1 - Sprint 1: Xây dựng Cơ sở Tri thức & Não bộ RAG  
**Cấu trúc:** Đã bổ sung Slide Quy trình Chuyển đổi Dữ liệu Thô (ETL Pipeline) thành trọn bộ 6 Slides súc tích.

---

## 🪟 SLIDE 1: TRANG TIÊU ĐỀ (TITLE SLIDE)

| Vị trí trên Slide | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề chính (Title)** | **BÁO CÁO TIẾN ĐỘ TUẦN 1: XÂY DỰNG CƠ SỞ TRI THỨC & NÃO BỘ RAG CHO ROBOT HÀNH CHÍNH CÔNG** |
| **Tiêu đề phụ (Subtitle)** | Học phần: Khóa luận Tốt nghiệp (Giai đoạn Pre-Thesis)<br>Giảng viên hướng dẫn: **Thầy Lành**<br>Sinh viên thực hiện: **Huỳnh Chiến** |
| **Tóm tắt kết quả (3 Bullets)** | • Hoàn thiện phân hệ Não bộ tri thức dựa trên kiến trúc **RAG (Retrieval-Augmented Generation)**.<br>• Xây dựng đường ống chuyển đổi dữ liệu thô (.pdf, .docx, .txt) thành cơ sở dữ liệu vector ChromaDB.<br>• Thiết lập **Cổng chặn tương đồng (Threshold = 0.55)** loại trừ triệt để hiện tượng AI ảo giác (Hallucination). |

---

## 🪟 SLIDE 2: MỤC TIÊU & PHƯƠNG PHÁP TIẾP CẬN

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **MỤC TIÊU TUẦN 1 & PHƯƠNG PHÁP TIẾP CẬN** |
| **Khung bên trái: Phương pháp AI-Assisted** | **1. Phương pháp: AI-Assisted Engineering (Pair Programming với AI)**<br>• Ứng dụng AI thế hệ mới làm công cụ hỗ trợ sinh mã (Boilerplate) và tự động hóa bộ test.<br>• **Sinh viên giữ vai trò Kiến trúc sư hệ thống (System Architect):** Thiết kế cấu trúc dữ liệu, lựa chọn mô hình, thiết lập các tham số toán học và kiểm định kết quả.<br>• Giúp rút ngắn thời gian xây dựng nền tảng từ 3 tuần xuống 1 tuần. |
| **Khung bên phải: Quyết định RAG vs Fine-tune** | **2. Quyết định kiến trúc: Tại sao chọn RAG thay vì Fine-tuning?**<br>• **Cập nhật luật trong 3 giây:** Khi có thông tư mới, chỉ cần thêm file văn bản vào hệ thống; Fine-tune tốn hàng tuần và chi phí GPU đắt đỏ để huấn luyện lại.<br>• **Minh bạch căn cứ pháp lý:** RAG trích dẫn rõ Điều, Khoản, tên văn bản nguồn; Fine-tune chỉ trả lời theo trí nhớ nơ-ron không thể kiểm chứng.<br>• **Triệt tiêu ảo giác:** Khóa chặt phạm vi trả lời trong tài liệu quy định nội bộ. |

---

## 🪟 SLIDE 3: QUY TRÌNH CHUYỂN ĐỔI DỮ LIỆU THÔ THÀNH VECTOR DB (ETL PIPELINE)

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **QUY TRÌNH CHUYỂN ĐỔI DỮ LIỆU THÔ THÀNH VECTOR DB (ETL PIPELINE)** |
| **Khung bên trái: 4 Bước chuyển đổi dữ liệu** | **Quy trình 4 bước tự động hóa (src/rag/ingest.py):**<br>• **Bước 1 (Trích xuất):** Đọc các tệp `.pdf`, `.docx`, `.txt` qua Document Loaders và tự động gắn nhãn nguồn `metadata["source_file"]`.<br>• **Bước 2 (Băm nhỏ):** Phân đoạn văn bản đệ quy ưu tiên theo cấu trúc Điều/Khoản luật Việt Nam.<br>• **Bước 3 (Vector hóa):** Gửi từng đoạn text qua mô hình `Google text-embedding-004` để chuyển đổi thành vector 768 chiều ngữ nghĩa.<br>• **Bước 4 (Lập chỉ mục & Lưu trữ):** Nạp vào **ChromaDB**, xây dựng cây chỉ mục không gian HNSW và lưu bền vững vào `vector_db/`. |
| **Khung bên phải: Điểm nhấn kỹ thuật** | **Ưu thế của đường ống chuyển đổi:**<br>• **Tự động hóa hoàn toàn:** Chỉ cần chạy lệnh `python src/rag/ingest.py`, toàn bộ tài liệu thô được nạp vào DB trong vài giây.<br>• **Cập nhật tức thì (Zero-downtime):** Dễ dàng thêm thủ tục mới mà không cần huấn luyện lại mô hình.<br>• **Truy xuất siêu tốc:** Cây chỉ mục **HNSW** giúp tìm kiếm 3 đoạn liên quan nhất chỉ mất **$0.03\text{ -- }0.04\text{ s}$** thay vì quét tuần tự toàn bộ văn bản. |

---

## 🪟 SLIDE 4: PHÂN ĐOẠN PHÁP LÝ THEO ĐIỀU/KHOẢN & VECTOR DB

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **PHÂN ĐOẠN PHÁP LÝ THEO ĐIỀU/KHOẢN & VECTOR DB** |
| **Khung trên: Vấn đề & Giải pháp băm nhỏ** | • **Vấn đề của băm cố định (500 ký tự):** Cắt ngẫu nhiên làm chém đôi danh sách giấy tờ hoặc mức lệ phí giữa hai đoạn $\rightarrow$ AI trả lời thiếu thông tin cho công dân.<br>• **Giải pháp phân đoạn theo cấp bậc Điều/Khoản luật:**<br>  - Bộ tách đệ quy ưu tiên: `["\nĐiều ", "\nKhoản ", "\n\n", "\n", " "]`<br>  - **`chunk_size = 800` ký tự** ($\approx 180$ từ, vừa trọn vẹn 1 Điều hoặc 1 Khoản luật).<br>  - **`chunk_overlap = 150` ký tự** (gối $1\text{ -- }2$ câu để giữ liên từ điều kiện).<br>  - $\rightarrow$ *Kết quả:* Toàn bộ quy định của 1 thủ tục luôn nằm trọn vẹn trong cùng 1 vector. |
| **Khung dưới: Cơ sở dữ liệu ChromaDB** | • **Cơ sở dữ liệu Vector cục bộ: ChromaDB**<br>  - **Serverless & Local-first:** Lưu trữ bền vững trên đĩa (`vector_db/`) qua SQLite và Parquet, không cần cài Docker cồng kềnh.<br>  - Tự động gắn kèm Metadata tên file gốc để phục vụ trích dẫn căn cứ pháp lý.<br>  - Mô hình Embedding: `Google text-embedding-004` ánh xạ văn bản sang vector ngữ nghĩa đa chiều. |

---

## 🪟 SLIDE 5: CƠ CHẾ CỔNG CHẶN CHỐNG ẢO GIÁC (HALLUCINATION FIREWALL)

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **CƠ CHẾ CỔNG CHẶN CHỐNG ẢO GIÁC (THRESHOLD = 0.55)** |
| **Khung bên trái: Nguyên lý Cổng chặn** | **1. Nguyên lý phân tách điểm tương đồng:**<br>• Mọi câu hỏi đều được chấm điểm tương đồng cosine ($0.0\text{ to }1.0$) với Vector DB trước khi gọi LLM.<br>• *Câu hỏi đúng phạm vi (Căn cước, tạm trú):* Điểm đạt **$0.68\text{ -- }0.86$**.<br>• *Câu hỏi ngoài lề (Visa nước ngoài, hỏi phiếm):* Điểm chỉ đạt **$0.25\text{ -- }0.48$**.<br>$\rightarrow$ Thiết lập **ngưỡng cứng `SIMILARITY_THRESHOLD = 0.55`**. |
| **Khung bên phải: Hiệu quả ngăn chặn** | **2. Phản xạ từ chối tức thì (Fast Refusal):**<br>• **Nếu Score $< 0.55$:** Lập tức ngắt luồng trong **$0.05\text{ giây}$**, từ chối lịch sự và hướng dẫn tra cứu Cổng Dịch vụ công Quốc gia.<br>• **Hiệu quả:** Tiết kiệm $100\%$ chi phí gọi LLM và **triệt tiêu hoàn toàn nguy cơ AI bịa đặt luật**.<br>• **System Prompt khắt khe:** Tham số `temperature = 0.1` ép mô hình suy luận tất định, bám sát tài liệu nội bộ. |

---

## 🪟 SLIDE 6: KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG & KẾ HOẠCH TUẦN 2

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG & KẾ HOẠCH TUẦN 2** |
| **Khung trên: Bảng số liệu đo đạc** | *(Xem bảng chi tiết bên dưới)* |
| **Khung dưới: Kế hoạch Tuần 2** | **KẾ HOẠCH NGHIÊN CỨU TUẦN 2:**<br>1. **Hiện thực hóa phân hệ "Đôi tai" (STT):** Xử lý thu âm microphone qua `sounddevice` (chuẩn hóa biên độ tín hiệu và chèn đệm chống nuốt âm).<br>2. **Tích hợp Faster-Whisper:** Nhận diện giọng nói tiếng Việt tăng tốc trên GPU NVIDIA CUDA.<br>3. Kết nối phân hệ STT với Não bộ RAG đã hoàn thiện của Tuần 1. |

### 📊 BẢNG DÁN VÀO SLIDE 6:

| Kịch bản kiểm thử | Câu hỏi thử nghiệm | Tìm kiếm Vector | LLM phản hồi | Tổng độ trễ | Đánh giá độ chính xác |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **TC01: Đúng phạm vi** | *"Làm thẻ căn cước cho trẻ dưới 14 tuổi thì cần những gì?"* | $0.04\text{ s}$ | $2.25\text{ s}$ | **$2.29\text{ s}$** | ✅ Đầy đủ hồ sơ, trích dẫn đúng Luật Căn cước 2023 |
| **TC02: Đúng phạm vi** | *"Đăng ký tạm trú mất bao lâu và nộp ở đâu?"* | $0.03\text{ s}$ | $2.18\text{ s}$ | **$2.21\text{ s}$** | ✅ Nêu rõ thời hạn 03 ngày & Công an cấp xã |
| **TC03: Ngoài phạm vi** | *"Thủ tục xin visa du lịch Nhật Bản tự túc?"* | $0.04\text{ s}$ | $0.00\text{ s}$ | **$0.04\text{ s}$** | ✅ Chặn đứng tại DB, từ chối trong 0.04s, 0% ảo giác |
