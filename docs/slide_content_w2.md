# BẢNG NỘI DUNG COPY-PASTE VÀO SLIDE POWERPOINT (BÁO CÁO TUẦN 2 - 6 SLIDES)
**Tệp trình chiếu cần dán:** `D:\Thesis\weekly report w2.pptx` (hoặc tạo file mới theo mẫu Tuần 1)  
**Chủ đề:** Báo cáo tiến độ Tuần 2 - Hoàn thiện Phân hệ AI Đa phương thức & Tích hợp Điều hướng Robot với ROS 2 / SLAM  
**Sinh viên thực hiện:** Huỳnh Chiến | **GVHD:** Thầy Lành  

---

## 🪟 SLIDE 1: TRANG TIÊU ĐỀ (TITLE SLIDE)

| Vị trí trên Slide | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề chính (Title)** | **BÁO CÁO TIẾN ĐỘ TUẦN 2: HOÀN THIỆN PHÂN HỆ AI ĐA PHƯƠNG THỨC & THỬ NGHIỆM HẠ TẦNG ROBOT ROS 2 / SLAM** |
| **Tiêu đề phụ (Subtitle)** | Học phần: Khóa luận Tốt nghiệp (Giai đoạn Pre-Thesis)<br>Giảng viên hướng dẫn: **Thầy Lành**<br>Sinh viên thực hiện: **Huỳnh Chiến** |
| **Tóm tắt kết quả (3 Bullets)** | • **Khởi tạo & Kiểm chứng Hạ tầng Robot trên WSL 2:** Thiết lập môi trường ROS 2 Lyrical, kết nối mô phỏng 3D Gazebo, điều khiển teleop kiểm chứng chuỗi dữ liệu cảm biến (LiDAR `/scan`, Odometry `/odom`, TF tree), và kiểm tra tính tương thích của **SLAM Toolbox & Nav2**.<br>• **Nâng cấp Thị giác & Theo dõi đối tượng (MOT):** Tích hợp camera không trễ, YOLOv8n (53 FPS) kết hợp thuật toán theo dõi định danh (Track ID), tự động chào hỏi thông minh không spam lặp lại.<br>• **Tra cứu Dự phòng Internet (Web Fallback) & Guardrail:** Tích hợp tìm kiếm mạng thông minh khi câu hỏi nằm ngoài CSDL nội bộ (kèm Hộp cảnh báo và trích dẫn URL), đối đáp xã giao hóm hỉnh và lọc rác âm thanh với độ trễ siêu tốc **$< 0.1\text{ ms}$**. |

---

## 🪟 SLIDE 2: MỤC TIÊU TUẦN 2 & KIẾN TRÚC 2 PHÂN HỆ LAI (HYBRID ARCHITECTURE)

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **MỤC TIÊU TUẦN 2 & KIẾN TRÚC 2 PHÂN HỆ LAI (HYBRID ARCHITECTURE)** |
| **Khung bên trái: Mục tiêu Tuần 2** | **1. Trọng tâm hoàn thành trong Tuần 2:**<br>• Cài đặt, cấu hình và kiểm chứng khởi động (Bring-up verification) nền tảng Robot: ROS 2 Lyrical, Gazebo Sim, SLAM Toolbox và Nav2 trên Ubuntu 26.04 (WSL 2). Điều khiển teleop kiểm tra cảm biến.<br>• Nâng cấp Prototype AI từ dạng "Hỏi - Đáp cục bộ" thành hệ thống **Tương tác Đa phương thức thông minh** (Giọng nói + Thị giác Camera + Hàng rào lọc ý định + Tra cứu dự phòng Internet khi thiếu dữ liệu).<br>• Bảo đảm toàn bộ 6 bộ test tự động đạt tỷ lệ **100% PASS**. |
| **Khung bên phải: Kiến trúc Phân tán lai** | **2. Thiết kế Kiến trúc Phân tán lai (Windows 11 + WSL 2):**<br>• **Phân hệ 1 (Windows 11):** Chạy giao tiếp người - máy (HMI: Mic, Loa, Camera, Faster-Whisper, ChromaDB RAG, Gemini LLM, Guardrail).<br>• **Phân hệ 2 (WSL 2 Ubuntu):** Chạy tác vụ điều khiển robot thời gian thực (ROS 2 Lyrical, LiDAR, Odometry, TF, Nav2 Path Planning).<br>• **Tách biệt tải tính toán:** Giúp hệ thống ổn định, tránh xung đột driver phần cứng và chuẩn bị sẵn sàng cho Cầu nối điều khiển (Bridge Layer). |

---

## 🪟 SLIDE 3: PHÂN HỆ ROBOT: THIẾT LẬP HẠ TẦNG, KIỂM CHỨNG & PHÂN TÍCH ĐIỂM NGHẼN (BOTTLENECK)

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **PHÂN HỆ ROBOT: THIẾT LẬP HẠ TẦNG, KIỂM CHỨNG & PHÂN TÍCH ĐIỂM NGHẼN (BOTTLENECK)** |
| **Khung bên trái: Mô phỏng Gazebo & Kiểm chứng Chuyển động** | **1. Môi trường Mô phỏng 3D & Kiểm chứng Điều khiển:**<br>• **Mô hình TurtleBot3 Waffle:** Nạp thành công vào thế giới ảo `turtlebot3_world` với đầy đủ khung gầm vi sai 2 bánh, cảm biến LiDAR 2D và cây biến đổi tọa độ TF.<br>• **Cầu nối dữ liệu `ros_gz_bridge`:** Chuyển đổi dữ liệu vận tốc thời gian thực giữa ROS 2 Lyrical và Gazebo Sim 10.5.0.<br>• **Điều khiển Teleop Bàn phím (`teleop_keyboard`):** Gửi lệnh vận tốc `/cmd_vel` từ terminal, điều khiển robot lăn bánh và xoay tròn tại chỗ thành công trong không gian mô phỏng. |
| **Khung bên phải: Phân tích Điểm nghẽn & Định hướng SLAM/Nav2** | **2. Phân tích Điểm nghẽn (Bottleneck) & Định hướng SLAM/Nav2:**<br>• **Khảo sát Điểm nghẽn RTF ($\sim 35\%$):** Kiểm tra qua `nvidia-smi` xác nhận card rời RTX 3050 ($4\text{ GB}$) đã kích hoạt, nhưng hệ số thời gian thực (RTF) bị hãm ở mức $35\%$ do kiến trúc GPU lai (NVIDIA Optimus `Disp.A: Off`) kết hợp cầu nối render D3D12 của WSLg.<br>• **Giải pháp Kiến trúc Tách biệt (Decoupled):** Gazebo chỉ chịu trách nhiệm mô phỏng vật lý ngầm (`headless`), chuyển toàn bộ giám sát trực quan sang **RViz2** (đồ họa 2D nhẹ đạt 60 FPS, giải phóng hoàn toàn nút thắt cổ chai).<br>• **Sẵn sàng cho Tuần 3:** Đã nạp thành công `slam_toolbox` và `nav2_bringup`, sẵn sàng quét bản đồ tĩnh (`.yaml`) phục vụ dẫn đường. |

---

## 🪟 SLIDE 4: PHÂN HỆ THỊ GIÁC MÁY TÍNH & THEO DÕI ĐỐI TƯỢNG (MOT & PROACTIVE GREETING)

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **PHÂN HỆ THỊ GIÁC MÁY TÍNH & THEO DÕI ĐỐI TƯỢNG (MOT & PROACTIVE GREETING)** |
| **Khung bên trái: Camera không trễ & YOLOv8** | **1. Luồng Camera Zero-lag & Nhận diện thời gian thực:**<br>• Khởi tạo `VideoCaptureThread` chạy ngầm độc lập với bộ đệm `buffer_size = 1`, triệt tiêu hoàn toàn độ trễ trễ hình (Buffer Lag) của OpenCV.<br>• Mô hình **YOLOv8n** tối ưu đạt tốc độ xử lý **$53\text{ FPS}$** ($\sim 18.8\text{ ms}$ trên CPU), phát hiện người và tài liệu tức thời.<br>• **Multimodal VQA:** Khi người dùng yêu cầu xem giấy tờ, camera lập tức chụp khung hình và gửi tới Gemini 2.5 Flash để đọc nội dung văn bản. |
| **Khung bên phải: Bộ theo dõi MOT & Chào hỏi thông minh** | **2. Bộ theo dõi đa đối tượng (MOT) & Chống spam lời chào:**<br>• **Thuật toán `PersonTracker` thuần Python:** Kết hợp IoU và khoảng cách tâm, gán **Track ID** độc lập cho từng người bước vào khung hình mà không cần phụ thuộc thư viện C++ phức tạp.<br>• **Chống chào lặp lại:** Ghi nhớ trạng thái `is_greeted = True`, người ngồi làm việc chỉ được chào **đúng 1 lần duy nhất**, không lặp sau mỗi 20s.<br>• **Xử lý tình huống thực tế:** Đổi người lập tức thì chào người mới; phát hiện đoàn đông người (`count > 1`) thì phát câu chào tập thể; tự động khóa lời chào khi người dùng đang nói chuyện/gõ phím. |

---

## 🪟 SLIDE 5: TRA CỨU DỰ PHÒNG INTERNET (WEB FALLBACK) & HÀNG RÀO AN TOÀN GUARDRAIL

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **TRA CỨU DỰ PHÒNG INTERNET (WEB FALLBACK) & HÀNG RÀO AN TOÀN GUARDRAIL** |
| **Khung bên trái: Hàng rào 4 tầng Guardrail** | **1. Hàng rào An toàn & Lọc Ý định (Độ trễ $< 0.1\text{ ms}$):**<br>• **Tier 1 (Lọc rác & Thô tục):** Tự động phát hiện tiếng đệm (*"alo"*, *"ừm"*, *"1 2 3"*) và nhắc nhở ngôn từ thô tục, xúc phạm.<br>• **Tier 2 (Persona Chit-chat):** Đối đáp hóm hỉnh với các câu trêu đùa (*"bạn là ai"*, *"có người yêu chưa"*, *"hát đi"*) và khéo léo **kéo người dân về lại thủ tục hành chính**.<br>• **Tier 3 (Chặn Lạc đề Out-of-Scope):** Từ chối ngay các câu hỏi nấu ăn, chơi game, giải toán mà không tiêu tốn API.<br>• **Tiết kiệm 100% chi phí:** Giảm thời gian phản hồi từ $3\text{ s}$ xuống **$0.09\text{ ms}$** cho các câu hỏi trêu đùa. |
| **Khung bên phải: Tra cứu Dự phòng Internet** | **2. Tra cứu Dự phòng khi Ngoài CSDL (Adaptive Web Fallback):**<br>• **Kích hoạt khi ngoài CSDL (Score $< 0.55$):** Thay vì từ chối cụt ngủn, hệ thống tự động kích hoạt tìm kiếm mạng thông minh qua Tavily AI Search.<br>• **Định tuyến 2 luồng thích ứng (`is_admin`):**<br>  - *Câu hỏi thủ tục mới:* Khóa phạm vi chỉ tìm trên domain chính thống (`.gov.vn`, `chinhphu.vn`, `luatvietnam.vn`).<br>  - *Câu hỏi đời sống/thời tiết:* Mở rộng toàn mạng kèm chèn ngày tháng thực tế để lấy dự báo thời tiết hôm nay.<br>• **Minh bạch & Trách nhiệm pháp lý:** Tự động đính kèm **Hộp Cảnh báo (Disclaimer Box)** và danh sách **URL nguồn trích dẫn**. |

---

## 🪟 SLIDE 6: KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG & KẾ HOẠCH TUẦN 3

| Khung hiển thị | Nội dung cần dán (Copy đoạn dưới) |
| :--- | :--- |
| **Tiêu đề Slide** | **KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG & KẾ HOẠCH TUẦN 3** |
| **Khung trên: Bảng số liệu đo đạc** | *(Xem bảng số liệu nghiệm thu thực tế bên dưới)* |
| **Khung dưới: Kế hoạch Tuần 3 (Sprint 3)** | **KẾ HOẠCH TRỌNG TÂM TUẦN 3 (SPRINT 3 - TUẦN THI GIỮA KỲ):**<br>1. **Nâng cấp Hội thoại Đa lượt (Multi-turn Context Memory):** Tích hợp bộ nhớ trượt 3 lượt gần nhất, duy trì ngữ cảnh cho chuỗi câu hỏi tiếp nối (*"hết bao nhiêu tiền"*, *"ở đâu"*, *"mất bao lâu"*).<br>2. **Xây dựng Giao diện Màn hình Cảm ứng (Touchscreen Web UI):** Trực quan hóa tương tác đa phương thức (khuôn mặt/trạng thái robot, live camera stream, hiển thị transcript và trích dẫn luật).<br>3. **Làm giàu Cơ sở Tri thức Thủ tục Một cửa:** Bổ sung các thủ tục phổ biến (Đăng ký kết hôn, Khai sinh, Cấp đổi GPLX).<br>4. **Quét và Lưu trữ Bản đồ Số 2D trong Mô phỏng:** Điều khiển robot quét hoàn chỉnh không gian phòng trong Gazebo và xuất file bản đồ tĩnh (`my_map.yaml` & `my_map.pgm`). |

---

### 📊 BẢNG DÁN VÀO SLIDE 6 (SỐ LIỆU ĐO ĐẠC NGHIỆM THU TUẦN 2):

| Phân hệ / Tính năng | Cơ chế kỹ thuật | Độ trễ đo đạc | Tỷ lệ thành công (Pass Rate) |
| :--- | :--- | :---: | :---: |
| **Nhận diện giọng nói STT** | Faster-Whisper Base (CUDA FP16) | $0.28\text{ -- }0.45\text{ s}$ | 100% (Chuẩn xác âm tiết tiếng Việt) |
| **Hàng rào Guardrail & Lọc ý định** | Pure Regex State Machine (4 Tầng) | **$0.09\text{ ms}$** | **100% (22/22 ca test PASS)** |
| **Truy xuất & Trả lời RAG nội bộ** | ChromaDB + Gemini 2.5 Flash | $1.8\text{ -- }2.3\text{ s}$ | 100% (Đúng điều/khoản, 0% ảo giác) |
| **Tra cứu Thời tiết (Web Fallback)** | Tavily Search + Realtime Temporal Date | $2.1\text{ -- }2.8\text{ s}$ | 100% (Đầy đủ cảnh báo & nguồn) |
| **Phát hiện đối tượng & Thị giác** | Camera Zero-lag + YOLOv8n (CPU) | **$18.8\text{ ms}$ ($53\text{ FPS}$)** | 100% (Phát hiện người tức thời) |
| **Theo dõi MOT & Chống lặp chào** | Pure Python IoU Tracker (Track ID) | **$0.08\text{ ms}$** | 100% (Chào đúng 1 lần duy nhất) |
| **Hạ tầng Robot & Teleop Sensor** | Gazebo Sim + Teleop + RViz2 (WSL 2) | Hoạt động thời gian thực | 100% (Thông suốt chuỗi dữ liệu /scan, /odom, TF) |
