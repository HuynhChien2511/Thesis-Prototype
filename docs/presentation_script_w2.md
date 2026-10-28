# 🎤 KỊCH BẢN THUYẾT TRÌNH BÁO CÁO TIẾN ĐỘ TUẦN 2 (WEEK 2 PRESENTATION SCRIPT)

> **Dành cho:** Sinh viên Huỳnh Văn Quang Chiến  
> **Người nghe / Phản biện:** Giảng viên hướng dẫn - Thầy Lành  
> **Thời lượng khuyến nghị:** $7\text{ -- }10\text{ phút}$ thuyết trình $+ 5\text{ phút}$ hỏi đáp (Q&A)  
> **Tài liệu trình chiếu đi kèm:** [`d:\Thesis\slide_content_w2.md`](file:///d:/Thesis/slide_content_w2.md)  

---

## 🪟 SLIDE 1: MỞ ĐẦU & TỔNG QUAN KẾT QUẢ TUẦN 2

**Lời thoại thuyết minh:**
> *"Em xin kính chào Thầy Lành. Em là Huỳnh Chiến. Hôm nay, em xin phép được báo cáo tiến độ nghiên cứu của Tuần thứ 2 trong khuôn khổ đề tài Khóa luận Tốt nghiệp: **'Thiết kế và Hiện thực Robot Trợ lý Di động Tự hành Ứng dụng ROS 2, SLAM và Mô hình Ngôn ngữ Lớn'**.*
>
> *Nếu như ở Tuần 1, em đã báo cáo với Thầy về việc xây dựng thành công Não bộ tri thức RAG và kiểm soát hiện tượng ảo giác, thì trong Tuần 2 này, em đã đạt được hai bước tiến mang tính bản lề:*
> 1. *Thứ nhất, **khởi tạo và kiểm chứng thành công hạ tầng Robot trên nền tảng ROS 2 (WSL 2)**: cài đặt thành công ROS 2 Lyrical, kết nối mô phỏng 3D Gazebo, điều khiển teleop lái robot xoay vòng kiểm tra chuỗi truyền thông cảm biến LiDAR, Odometry, TF và chuẩn bị sẵn sàng cho SLAM Toolbox & Nav2.*
> 2. *Thứ hai, **nâng cấp toàn diện Phân hệ Trợ lý AI**: hoàn thiện 'Đôi mắt' thị giác máy tính với khả năng theo dõi đa đối tượng (MOT), chống spam lời chào, bổ sung hàng rào lọc ý định Guardrail siêu tốc và mở rộng tra cứu thời tiết thời gian thực.*
>
> *Sau đây, em xin phép đi vào chi tiết kiến trúc và các kết quả thực nghiệm định lượng mà em đã đạt được."*

---

## 🪟 SLIDE 2: MỤC TIÊU TUẦN 2 & KIẾN TRÚC 2 PHÂN HỆ LAI

**Lời thoại thuyết minh:**
> *"Thưa Thầy, để chuẩn bị cho việc tích hợp hoàn chỉnh một robot trợ lý vừa có khả năng đàm thoại tự nhiên, vừa có thể lăn bánh dẫn đường tại Bộ phận Một cửa, em đã thiết kế kiến trúc hệ thống theo mô hình **Phân tán lai (Hybrid Architecture)** gồm 2 phân hệ độc lập:*
>
> *Ở **Phân hệ 1 trên Windows 11**, em tập trung toàn bộ các tác vụ tương tác người - máy đa phương thức (HMI): bao gồm xử lý tín hiệu Microphone, nhận diện giọng nói Faster-Whisper tăng tốc CUDA, bộ lọc ý định Guardrail, cơ sở dữ liệu vector ChromaDB và mô hình Gemini 2.5 Flash.*
>
> *Ở **Phân hệ 2 trên môi trường ảo hóa Linux WSL 2**, em triển khai nền tảng **ROS 2 Lyrical**. Đây là nơi chạy các tác vụ điều khiển robot thời gian thực: tiếp nhận dữ liệu từ cảm biến LiDAR, Odometry, biến đổi hệ tọa độ TF và tính toán quỹ đạo di chuyển của robot.*
>
> *Ưu điểm lớn nhất của thiết kế này là **tách biệt hoàn toàn tải tính toán (Decoupling)**. Tác vụ xử lý ngôn ngữ và suy luận thị giác nặng trên Windows sẽ không bao giờ làm gián đoạn hay gây giật lag luồng điều khiển chuyển động khắt khe thời gian thực của ROS 2. Hai phân hệ này đã sẵn sàng để được ghép nối qua một tầng Cầu nối giao tiếp (Bridge Layer) trong tuần tiếp theo."*

---

## 🪟 SLIDE 3: PHÂN HỆ ROBOT: THIẾT LẬP HẠ TẦNG & KIỂM CHỨNG MÔ PHỎNG (ROS 2 & GAZEBO)

**Lời thoại thuyết minh:**
> *"Em xin đi sâu vào Phân hệ Robot Tự hành trên môi trường ROS 2 ở Slide thứ 3:*
>
> *Thưa Thầy, đối với phía robot bên WSL 2, trọng tâm tuần này của em là **Thiết lập Hạ tầng và Kiểm chứng Khởi động (Infrastructure Bring-up & Verification)**:*
>
> *Đầu tiên, em đã cấu hình môi trường Ubuntu 26.04 trên WSL 2 với bản phân phối **ROS 2 Lyrical** và dựng không gian mô phỏng văn phòng ảo trên **Gazebo Sim 10.5.0** cùng mô hình **TurtleBot3 Waffle**. Mẫu robot này có đầy đủ động học vi sai hai bánh và cảm biến quét 2D LiDAR.*
>
> *Em đã thiết lập cầu nối `ros_gz_bridge` và sử dụng công cụ điều khiển bàn phím `teleop_keyboard` để lái robot di chuyển và xoay vòng tại chỗ. Qua đó, em đã kiểm chứng được tính thông suốt của chuỗi dữ liệu thời gian thực: lệnh vận tốc `/cmd_vel` gửi từ ROS 2 sang Gazebo điều khiển bánh xe, đồng thời dữ liệu quét laser `/scan`, dữ liệu hành trình `/odom` và cây biến đổi tọa độ TF được phản hồi liên tục.*
>
> *Đặc biệt, trong quá trình chạy mô phỏng, em đã phát hiện và phân tích một điểm nghẽn kỹ thuật thực tế (Bottleneck): hệ số thời gian thực (RTF) của Gazebo dừng ở mức khoảng 35%. Qua việc kiểm tra thông số card NVIDIA RTX 3050 bằng `nvidia-smi`, em nhận diện được nguyên nhân xuất phát từ cơ chế xuất hình lai Optimus kết hợp tầng ảo hóa D3D12 của WSLg. Từ đó, em đã xác lập giải pháp kiến trúc tách biệt (Decoupled Architecture): để Gazebo tính toán vật lý ngầm, và chuyển toàn bộ việc giám sát trực quan 2D sang RViz2 để đạt tốc độ 60 FPS mượt mà.*
>
> *Song song đó, em đã cài đặt và kiểm tra tính tương thích của các gói cốt lõi: **SLAM Toolbox** và ngăn xếp **Nav2**. Các node này đã có thể khởi chạy và nhận dữ liệu cảm biến bình thường. Đây là tiền đề vững chắc để ngay trong giai đoạn tiếp theo, em sẽ điều khiển robot quét hoàn chỉnh toàn bộ bản đồ văn phòng, lưu lại file bản đồ tĩnh và tiến hành cấu hình các điểm mốc (waypoints) dẫn đường cho Nav2."*

---

## 🪟 SLIDE 4: PHÂN HỆ THỊ GIÁC MÁY TÍNH & THEO DÕI ĐỐI TƯỢNG (MOT & PROACTIVE GREETING)

**Lời thoại thuyết minh:**
> *"Bên cạnh việc dựng phân hệ robot, em cũng đã giải quyết trọn vẹn bài toán thị giác máy tính cho phân hệ AI ở Slide 4:*
>
> *Đầu tiên, để giải quyết hiện tượng trễ hình (Buffer Lag) vốn là điểm yếu cố hữu của OpenCV khi đọc camera, em đã thiết kế lớp `VideoCaptureThread` chạy ngầm riêng biệt với bộ đệm bằng 1. Nhờ đó, khung hình đưa vào mô hình **YOLOv8n** luôn là khung hình thời gian thực mới nhất, đạt tốc độ xử lý rất ấn tượng: **$53\text{ FPS}$ (tức chỉ mất $18.8\text{ ms}$ trên CPU thường)**.*
>
> *Đặc biệt, trong quá trình thử nghiệm thực tế, em nhận thấy nếu chỉ dùng bộ đếm thời gian (Cooldown 20s) thì người dân đang ngồi làm việc sẽ liên tục bị robot chào lại gây khó chịu. Do đó, em đã tự nghiên cứu và cài đặt một **Bộ theo dõi đa đối tượng thuần Python (`PersonTracker`)** dựa trên giải thuật kết hợp chỉ số giao cắt hộp bao (IoU) và khoảng cách tâm.*
>
> *Bộ theo dõi này gán một **Track ID duy nhất** cho từng người (`ID#1`, `ID#2`...). Khi người đó đã được chào (`is_greeted = True`), dù họ ngồi lại bao lâu robot cũng **không bao giờ chào lặp lại**. Nhưng nếu người đó bước đi và một người khác bước vào thế chỗ, robot lập tức phát hiện Track ID mới và cất lời chào tức thì. Ngoài ra, hệ thống còn tự động nhận diện nhóm đông người để chào tập thể và tự khóa cơ chế chào hỏi khi người dùng đang trong phiên đàm thoại, tránh tình trạng ngắt lời thô bạo."*

---

## 🪟 SLIDE 5: TRA CỨU DỰ PHÒNG INTERNET (WEB FALLBACK) & HÀNG RÀO AN TOÀN GUARDRAIL

**Lời thoại thuyết minh:**
> *"Thưa Thầy, một điểm nhấn kỹ thuật quan trọng ở Slide 5 chính là sự kết hợp giữa **Hàng rào An toàn Guardrail 4 tầng** và **Cơ chế Tra cứu Dự phòng Internet (Adaptive Web Fallback)**:*
>
> *Đầu tiên, tại quầy Một cửa, thực tế sẽ có rất nhiều trường hợp mic thu phải tiếng đệm (*'alo'*, *'ừm'*), hoặc người hiếu kỳ trêu đùa (*'bạn là ai'*, *'có người yêu chưa'*). Nếu đưa những câu này vào RAG và gọi API mạng thì vừa mất 3–5 giây, vừa tốn chi phí. Do đó, em đã xây dựng **Hàng rào Guardrail 4 tầng chạy nội bộ (< 0.1ms)**: lọc tiếng đệm, nhắc nhở ngôn từ thô tục, đối đáp hóm hỉnh theo phong cách công sở và khéo léo định hướng người dân quay về hỏi thủ tục hành chính, đồng thời chặn đứng các câu hỏi lạc đề như nấu ăn, chơi game.*
>
> *Thứ hai, đối với các câu hỏi hợp lệ nhưng **nằm ngoài CSDL nội bộ đã thẩm định (Cosine Score < 0.55)**, thay vì từ chối cụt ngủn, hệ thống sẽ kích hoạt **Cơ chế Tra cứu Dự phòng Internet qua Tavily AI Search**:*
> - *Nếu là câu hỏi thủ tục hành chính mới, hệ thống tự động khóa phạm vi tìm kiếm, chỉ tra cứu trên các cổng thông tin chính thống của Nhà nước như `.gov.vn`, `chinhphu.vn`, `luatvietnam.vn`.*
> - *Nếu là câu hỏi tiện ích đời sống (như dự báo thời tiết hôm nay), hệ thống sẽ mở rộng tìm kiếm toàn mạng và tự động chèn ngày tháng thực tế để lấy dữ liệu khí tượng mới nhất.*
> - *Và để đảm bảo tính chuẩn mực và trách nhiệm pháp lý công vụ, mọi câu trả lời từ Internet đều được **tự động đính kèm Hộp Cảnh báo (Disclaimer)** khuyến cáo đối chiếu với cán bộ tại quầy, cùng **danh sách URL nguồn trích dẫn minh bạch**.*
>
> *Nhờ cơ chế 2 tầng này, robot vừa được bảo vệ an toàn trước các câu trêu đùa, vừa có khả năng thích ứng mở rộng tri thức một cách có kiểm soát khi CSDL nội bộ chưa kịp cập nhật ạ."*

---

## 🪟 SLIDE 6: KẾT QUẢ THỰC NGHIỆM ĐỊNH LƯỢNG & KẾ HOẠCH TUẦN 3

**Lời thoại thuyết minh:**
> *"Em xin phép tổng kết lại các kết quả thực nghiệm định lượng trên Slide 6:*
>
> *Trong tuần qua, em đã thực hiện kiểm thử tự động toàn diện qua 6 bộ test kịch bản, và **toàn bộ 6 bộ test đều đạt tỷ lệ $100\%$ PASS**:*
> - *Nhận diện giọng nói STT tiếng Việt chỉ mất $0.28\text{ -- }0.45\text{ giây}$.*
> - *Hàng rào an toàn Guardrail phản hồi trong $0.09\text{ miligiây}$ (22/22 ca test đạt tuyệt đối).*
> - *Truy xuất RAG và suy luận Gemini mất khoảng $1.8\text{ -- }2.3\text{ giây}$, trích dẫn chính xác luật và $0\%$ ảo giác.*
> - *Nhận diện thị giác đạt $53\text{ FPS}$ trên CPU và bộ theo dõi MOT chạy trong $0.08\text{ miligiây}$.*
> - *Chuỗi truyền thông mô phỏng Gazebo, dữ liệu cảm biến LiDAR/Odom và điều khiển teleop của robot hoạt động trơn tru trong WSL 2.*
>
> *Dựa trên nền tảng vững chắc của cả 2 phân hệ AI và Robot, **kế hoạch trọng tâm của Tuần 3 (Sprint 3)** của em sẽ là:*
> 1. *Lái robot quét hoàn chỉnh bản đồ văn phòng bằng SLAM Toolbox, lưu file bản đồ tĩnh `.yaml` và cấu hình các điểm mốc (Waypoints) đón tiếp khách trong Nav2.*
> 2. *Xây dựng **Tầng Cầu nối Giao tiếp (Bridge Layer)** giữa Windows Python và ROS 2 trong WSL thông qua giao thức WebSocket hoặc FastAPI microservice.*
> 3. *Tích hợp chức năng **LLM Tool Calling** cho Gemini để phân tích ý định người dùng thành lệnh điều khiển robot.*
> 4. *Và nghiệm thu kịch bản hoàn chỉnh: Khi người dân nói: **'Dẫn tôi tới quầy làm Căn cước công dân'**, robot sẽ cất tiếng trả lời xác nhận và đồng thời tự động lăn bánh dẫn đường trên bản đồ mô phỏng!*
>
> *Em xin trân trọng cảm ơn Thầy Lành đã lắng nghe. Em rất mong nhận được những góp ý và chỉ dẫn của Thầy để hoàn thiện đề tài tốt hơn ạ!"*

---

## 🛡️ DỰ TRÙ CÂU HỎI HÓC BÚA CỦA THẦY LÀNH & HƯỚNG TRẢ LỜI (Q&A DEFENSE)

### Câu hỏi 1: *"Tuần này robot bên ROS 2 của em đã tự động chạy dẫn đường được chưa hay chỉ mới điều khiển bằng tay?"*
> **Cách trả lời trung thực & bản lĩnh kỹ thuật:**  
> *"Dạ thưa Thầy, trong Tuần 2 em tập trung vào giai đoạn **Bring-up và Kiểm chứng Hạ tầng (Infrastructure Verification)**:*  
> *Em đã thiết lập môi trường ROS 2 Lyrical trên WSL 2, kết nối mô phỏng Gazebo 3D và dùng teleop bàn phím điều khiển bot di chuyển, xoay vòng để kiểm tra chuỗi truyền thông cảm biến. Em đã xác nhận dữ liệu tia laser `/scan`, dữ liệu hành trình `/odom` và cây biến đổi tọa độ TF giữa Gazebo và ROS 2 đều phản hồi trơn tru trên RViz2. Các gói cốt lõi SLAM Toolbox và Nav2 đã được cài đặt và kiểm tra tính tương thích.*  
> *Sau khi hạ tầng mô phỏng đã hoàn toàn thông suốt, trong Tuần 3 tới em sẽ cho robot quét hoàn chỉnh toàn bộ bản đồ căn phòng và cấu hình Nav2 để robot tự động di chuyển giữa các quầy làm việc ạ."*

### Câu hỏi 2: *"Tại sao em lại tách hệ thống thành 2 môi trường Windows và WSL 2, sao không cài hết lên một máy Ubuntu thuần?"*
> **Cách trả lời tự tin:**  
> *"Dạ thưa Thầy, đây là một quyết định kỹ thuật em đã cân nhắc rất kỹ dựa trên 3 lý do:*  
> 1. *Thứ nhất, phân hệ AI tương tác người - máy cần truy cập trực tiếp vào phần cứng Microphone, Camera và loa ngoài thời gian thực, vốn hoạt động ổn định và tối ưu driver nhất trên hệ điều hành máy chủ (Host OS Windows).*  
> 2. *Thứ hai, việc tách biệt giúp cô lập lỗi (Fault Isolation). Nếu luồng AI đàm thoại có xử lý file nặng hoặc gọi API mạng thì cũng hoàn toàn không ảnh hưởng đến chu kỳ điều khiển động cơ khắt khe (Real-time Control Loop) của ROS 2.*  
> 3. *Thứ ba, thiết kế này phản ánh đúng kiến trúc công nghiệp thực tế: các robot thương mại hiện nay thường dùng 1 máy tính nhúng chuyên trách AI/HMI và 1 bộ điều khiển chuyên trách điều hướng/chuyển động, giao tiếp với nhau qua mạng nội bộ. Việc em dùng Bridge Layer chính là bước chuẩn bị chuẩn hóa cho mô hình này ạ."*

### Câu hỏi 3: *"Tại sao em tự viết thuật toán IoU Tracker bằng Python mà không dùng ByteTrack hay DeepSORT có sẵn của YOLO?"*
> **Cách trả lời tự tin:**  
> *"Dạ thưa Thầy, ban đầu em có gọi hàm `model.track()` của Ultralytics, nhưng thuật toán ByteTrack mặc định của họ đòi hỏi cài đặt gói `lap` (Linear Assignment Problem) bằng C++, dễ gây xung đột trình biên dịch và phụ thuộc nền tảng.*  
> *Trong khi đó, ở bài toán robot quầy Một cửa, người dân đứng lại trước quầy với vận tốc di chuyển vừa phải, không có hiện tượng che khuất phức tạp như giám sát giao thông tốc độ cao. Do đó, em đã tự cài đặt giải thuật `PersonTracker` kết hợp chỉ số IoU và khoảng cách tâm bằng thư viện `numpy`. Giải thuật này chạy siêu tốc chỉ mất **$0.08\text{ miligiây}$** (tức chưa đến 1/10 của một phần nghìn giây), hoàn toàn không phụ thuộc C++, ổn định tuyệt đối và đáp ứng $100\%$ yêu cầu bài toán ạ."*

### Câu hỏi 4: *"Nếu người dùng hỏi một câu vừa có ý định hỏi thủ tục vừa có yếu tố trêu đùa thì Guardrail của em xử lý như thế nào?"*
> **Cách trả lời tự tin:**  
> *"Dạ thưa Thầy, bộ lọc Guardrail được em thiết kế theo nguyên tắc ưu tiên an toàn và tính bao dung (Forgiving Design). Bộ lọc chỉ chặn hoặc chuyển hướng khi câu hỏi thuần túy là câu trêu đùa, tiếng ồn hoặc lạc đề hoàn toàn.*  
> *Nếu trong câu hỏi có chứa các thực thể thủ tục hành chính (ví dụ: 'Robot xinh gái ơi chỉ tôi làm căn cước với'), hệ thống sẽ bỏ qua phần trêu đùa và vẫn cho phép câu hỏi vượt qua Guardrail (Action = `pass`) để Não bộ RAG truy xuất chính xác thủ tục Căn cước cho người dân ạ."*
