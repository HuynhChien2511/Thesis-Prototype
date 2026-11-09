# 📋 BÁO CÁO THỰC NGHIỆM ĐÁNH GIÁ NĂNG LỰC BÓC TÁCH CÂU TIẾNG VIỆT (TASK 3)

> **Thực hiện theo chỉ đạo của GVHD:** TS. Lê Thanh Lành (Tuần 4 - Sprint 4)
> **Mục tiêu:** Thẩm định độ chính xác của cơ chế tách câu phục vụ Sentence-Boundary Streaming TTS.
> **Tập dữ liệu kiểm chuẩn:** 20 câu hành chính công phức tạp chứa số tiền, ngày tháng, từ viết tắt, học vị và tên miền.

## 1. TỔNG HỢP HIỆU SUẤT ĐỐI ĐẦU

| Chỉ số đánh giá | Phương pháp Gốc (Naive `split('.')`) | Phương pháp Cải tiến (`split_sentences()`) | Cải thiện |
|---|:---:|:---:|:---:|
| **Số câu đạt chuẩn ngữ nghĩa** | **8 / 20** | **20 / 20** | **+12 câu** |
| **Tỷ lệ chính xác (Accuracy)** | **40.0%** | **100.0%** | **+60.0%** |
| **Số câu bị phân mảnh lỗi** | **12 / 20 (60.0%)** | **0 / 20 (0.0%)** | **Triệt tiêu 100% lỗi** |

---

## 2. BẢNG SO SÁNH CHI TIẾT 20 CA KIỂM THỬ THỰC TẾ

| STT | Nhóm nội dung thử nghiệm | Số mảnh (Gốc) | Trạng thái Gốc | Số câu (Cải tiến) | Trạng thái Cải tiến | Kết quả phân đoạn Cải tiến |
|:---:|---|:---:|:---:|:---:|:---:|---|
| 1 | Viết tắt địa danh & Chức danh (TP. HCM, TS.) | 3 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Hồ sơ xin cấp Phiếu lý lịch tư pháp được tiếp nhận tại Sở Tư pháp TP. HCM.`<br>• `Quý công dân có thể nhận kết quả qua bưu điện sau 10 ngày.` |
| 2 | Số tiền hàng triệu & Đơn vị đồng | 4 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Lệ phí đăng ký kết hôn có yếu tố nước ngoài là 1.500.000 đồng theo quy định hiện hành.`<br>• `Công dân được miễn hoàn toàn lệ phí khi đăng ký trong nước.` |
| 3 | Nhiều số tiền & Số thập phân (1.5 ngày) | 5 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Mức phí cấp đổi thẻ căn cước gắn chip là 50.000 đồng đối với cấp lại và 30.000 đồng khi đổi mới.`<br>• `Thời hạn xử lý hồ sơ là 1.5 ngày làm việc.` |
| 4 | Ngày tháng & Số hiệu Thông tư (TT-BTC) | 2 | ĐẠT | 2 | **ĐẠT (Hoàn hảo)** | • `Căn cứ Thông tư 73/2024/TT-BTC có hiệu lực từ ngày 01/07/2024 của Bộ Tài chính.`<br>• `Người dân có thể nộp hồ sơ trực tuyến qua cổng VNeID.` |
| 5 | Học vị & Danh xưng (TS., ThS.) | 3 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Đề tài nghiên cứu do TS. Lê Thanh Lành hướng dẫn tại Khoa Công nghệ Thông tin.`<br>• `Nhóm sinh viên tiến hành thực nghiệm trên mô hình robot tự hành.` |
| 6 | Nghị định pháp luật (NĐ-CP) | 2 | ĐẠT | 2 | **ĐẠT (Hoàn hảo)** | • `Theo quy định tại Nghị định số 104/2022/NĐ-CP của Chính phủ.`<br>• `Sổ hộ khẩu giấy chính thức hết giá trị sử dụng từ ngày 01/01/2023.` |
| 7 | Cơ quan hành chính (UBND, HĐND) | 2 | ĐẠT | 2 | **ĐẠT (Hoàn hảo)** | • `UBND cấp huyện chịu trách nhiệm thẩm định và phê duyệt phương án bồi thường tái định cư.`<br>• `HĐND cùng cấp thực hiện giám sát theo thẩm quyền.` |
| 8 | Tên miền cổng dịch vụ công (.gov.vn) | 4 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Công dân vui lòng truy cập địa chỉ dichvucong.gov.vn để nộp hồ sơ trực tuyến.`<br>• `Hệ thống sẽ tự động gửi mã hồ sơ qua tin nhắn SMS.` |
| 9 | Số phần trăm & Mốc thời gian | 2 | ĐẠT | 2 | **ĐẠT (Hoàn hảo)** | • `Mức thu lệ phí trước bạ đối với ô tô điện chạy pin là 0% trong 3 năm đầu.`<br>• `Từ năm thứ tư trở đi áp dụng mức thu bằng 50% so với xe chạy xăng.` |
| 10 | Ứng dụng số (VNeID, BHYT, BHXH) | 2 | ĐẠT | 2 | **ĐẠT (Hoàn hảo)** | • `Thẻ BHYT và sổ BHXH đã được tích hợp trực tiếp trên ứng dụng VNeID mức độ 2.`<br>• `Người bệnh chỉ cần xuất trình căn cước công dân khi khám chữa bệnh.` |
| 11 | Giấy phép lái xe (GPLX) & Mức phí nhiều bậc | 4 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Thủ tục cấp đổi GPLX hạng B2 được thực hiện khi còn thời hạn sử dụng.`<br>• `Chi phí sát hạch lý thuyết là 100.000 đồng và thực hành là 350.000 đồng.` |
| 12 | Câu đệm quá ngắn cần gom ('Dạ.', 'Vâng ạ.') | 4 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Dạ. Vâng ạ. Thủ tục cấp Giấy xác nhận tình trạng hôn nhân được giải quyết trong ngày làm việc.`<br>• `Quý khách vui lòng xuất trình CCCD để kiểm tra.` |
| 13 | Dấu chấm lửng (...) & Tờ khai CT01 | 2 | ĐẠT | 1 | **ĐẠT (Hoàn hảo)** | • `Hồ sơ bao gồm: Tờ khai theo mẫu CT01, bản sao giấy khai sinh, giấy xác nhận cư trú... Người nộp mang theo bản chính để đối chiếu khi có yêu cầu.` |
| 14 | Cơ quan tư pháp (VKSND, TAND) & Số thập phân | 3 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `VKSND và TAND các cấp đang đẩy mạnh chuyển đổi số trong quản lý hồ sơ vụ án.`<br>• `Thời gian giải quyết khiếu nại được rút ngắn xuống còn 2.5 ngày.` |
| 15 | Số tiền tỷ đồng (1.000.000.000 đồng) & Tỷ lệ 0.1% | 9 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Phí công chứng hợp đồng mua bán nhà đất có giá trị 1.000.000.000 đồng đến 3.000.000.000 đồng là 0.1% giá trị tài sản.`<br>• `Thời hạn trả kết quả là 3 ngày.` |
| 16 | Luật Quốc hội (QH15) & Mốc thời hạn | 2 | ĐẠT | 2 | **ĐẠT (Hoàn hảo)** | • `Luật Căn cước số 26/2023/QH15 chính thức có hiệu lực từ ngày 01/07/2024.`<br>• `Trẻ em dưới 14 tuổi được cấp thẻ căn cước theo nhu cầu của cha mẹ.` |
| 17 | Cảnh sát giao thông (CSGT) & Thành phố | 3 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Đội CSGT thuộc Công an TP. Thủ Đức tiến hành xử lý vi phạm nồng độ cồn qua camera giám sát.`<br>• `Biên lai phạt tiền được gửi về nơi cư trú của người vi phạm.` |
| 18 | Thời hạn khai sinh & Nghị định | 2 | ĐẠT | 2 | **ĐẠT (Hoàn hảo)** | • `Trong thời hạn 60 ngày kể từ ngày sinh con, cha hoặc mẹ có trách nhiệm đăng ký khai sinh cho con.`<br>• `Quá thời hạn trên sẽ bị xử lý theo quy định của NĐ-CP.` |
| 19 | Phí chứng thực bản sao (2.000 đồng / 200.000 đồng) | 4 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `Mức thu phí chứng thực bản sao từ bản chính là 2.000 đồng một trang và tối đa không quá 200.000 đồng một bản.`<br>• `Bản sao chứng thực có giá trị như bản chính.` |
| 20 | Học vị liên tiếp (PGS. TS.) & Bộ GD&ĐT | 5 | LỖI (Bị băm nát) | 2 | **ĐẠT (Hoàn hảo)** | • `PGS. TS. Trần Trung Tính và ThS. Nguyễn Văn A đã chủ trì hội thảo khoa học cấp quốc gia.`<br>• `Các định hướng mới của Bộ GD&ĐT được phổ biến tới đại biểu.` |

---

## 3. PHÂN TÍCH NGUYÊN NHÂN LỖI CỦA PHƯƠNG PHÁP GỐC & GIẢI PHÁP KHẮC PHỤC

### 3.1. Các dạng sai hỏng nghiêm trọng của phương pháp ngây thơ (`split('.')`)
1. **Băm nát số tiền hàng triệu:** Ví dụ `1.500.000 đồng` bị cắt vụn thành `1`, `500`, `000 đồng`. Khi TTS phát âm, máy sẽ đọc rời rạc thành *'một'* nghỉ *'năm trăm'* nghỉ *'không không không đồng'*, gây khó hiểu cho người dân.
2. **Cắt cụt số thập phân thời hạn:** `1.5 ngày làm việc` bị cắt thành `1` và `5 ngày làm việc`. Người dân có thể nghe nhầm hạn trả hồ sơ từ **1.5 ngày** thành **5 ngày** (sai lệch thông tin pháp lý nghiêm trọng).
3. **Phân rã địa danh hành chính:** `TP. HCM` bị cắt thành `TP` và `HCM`. Giọng đọc máy ngắt quãng giữa câu gây mất tự nhiên.
4. **Cắt gãy học hàm, danh xưng:** `TS. Lê Thanh Lành` bị cắt thành `TS` và `Lê Thanh Lành`.
5. **Phân mảnh tên miền quốc gia:** `dichvucong.gov.vn` bị cắt thành `dichvucong`, `gov`, `vn`.
6. **Vụn vỡ câu đệm ngắn:** Các từ lịch sự như `Dạ.`, `Vâng ạ.` bị tách thành luồng TTS riêng với thời lượng vài trăm mili-giây, làm tăng tải số lần bắt tay WebSocket và giọng đọc giật cục.

### 3.2. Cơ chế khắc phục chuẩn mực trong `split_sentences()`
- **Sentinel Protection Pattern:** Sử dụng mã placeholder bảo vệ các dấu chấm nội hàm (`@@DOT@@`) cho cụm số hàng nghìn (`\d+\.\d+`), số thập phân, học vị (`TS.`, `ThS.`, `PGS.`, `GS.`), địa danh (`TP.`) và tên miền (`.gov.vn`).
- **Ellipsis Shielding:** Bảo vệ chuỗi chấm lửng (`...`) bằng mã `@@ELLIPSIS@@` tránh băm rác.
- **Buffer Merging (`min_chars=25`):** Tự động gom các câu đệm ngắn hoặc câu cảm thán vào câu kế tiếp để đảm bảo nhịp điệu phát âm mượt mà, liên tục.
- **Khôi phục hoàn nguyên:** Sau khi phân tách ranh giới câu thực sự (`[.!?\n]+\s+`), hệ thống hoàn nguyên chính xác 100% các dấu chấm nội hàm vào văn bản phát âm.