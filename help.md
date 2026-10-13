# HƯỚNG DẪN SỬ DỤNG TASKFLOW PERSONAL

## 1. Giới thiệu

TaskFlow Personal là ứng dụng quản lý công việc cá nhân, gồm giao diện người dùng, API backend, cơ sở dữ liệu PostgreSQL trên Supabase và tính năng hỗ trợ lập kế hoạch bằng Gemini AI.

### Các thành phần

- **Frontend:** Streamlit — giao diện người dùng.
- **Backend:** FastAPI — xử lý dữ liệu và các API.
- **Database:** PostgreSQL — lưu trữ dữ liệu trên Supabase.
- **AI:** Google Gemini — hỗ trợ lập kế hoạch công việc.

---

## 2. Cách chạy ứng dụng trên Windows

### Bước 1: Mở dự án

1. Mở Visual Studio Code.
2. Chọn **File → Open Folder**.
3. Chọn thư mục dự án:

```text
D:\taskflow_personal
```

4. Mở Terminal bằng cách chọn **Terminal → New Terminal**.

### Bước 2: Chạy Backend

Mở Terminal thứ nhất và nhập lần lượt các lệnh sau:

```powershell
cd D:\taskflow_personal
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload
```

Nếu chạy thành công, Backend sẽ hoạt động tại:

- API: http://127.0.0.1:8000
- Tài liệu kiểm tra API: http://127.0.0.1:8000/docs

**Lưu ý:** Không đóng Terminal đang chạy Backend khi còn sử dụng ứng dụng.

### Bước 3: Chạy Frontend

Mở Terminal thứ hai bằng cách chọn **Terminal → New Terminal**.

Nhập lần lượt các lệnh:

```powershell
cd D:\taskflow_personal
.\.venv\Scripts\Activate.ps1
python -m streamlit run web_app.py
```

Khi chạy thành công, Streamlit sẽ hiển thị địa chỉ truy cập. Thông thường là:

http://localhost:8501

Mở địa chỉ này trên trình duyệt để sử dụng TaskFlow Personal.

**Lưu ý:** Phải giữ cả hai Terminal hoạt động đồng thời.

### Bước 4: Dừng ứng dụng

Để tắt ứng dụng:

1. Chuyển đến Terminal đang chạy Frontend.
2. Nhấn `Ctrl + C`.
3. Chuyển đến Terminal đang chạy Backend.
4. Nhấn `Ctrl + C`.

---

## 3. Các tính năng chính

### 3.1. Quản lý công việc

Người dùng có thể sử dụng giao diện để quản lý công việc theo các chức năng mà ứng dụng cung cấp, chẳng hạn như:

- Xem danh sách công việc.
- Tạo công việc mới.
- Cập nhật thông tin công việc.
- Theo dõi trạng thái công việc.
- Xóa công việc khi không còn cần thiết.

### 3.2. Lập kế hoạch với Gemini AI

Tính năng AI hỗ trợ người dùng xây dựng kế hoạch dựa trên thông tin đầu vào.

Cách sử dụng:

1. Mở ứng dụng TaskFlow Personal.
2. Truy cập khu vực lập kế hoạch AI.
3. Nhập yêu cầu hoặc thông tin công việc.
4. Gửi yêu cầu và chờ AI xử lý.
5. Xem kết quả được trả về.

Kết quả phụ thuộc vào nội dung yêu cầu, trạng thái dịch vụ Gemini và cấu hình API key.

---

## 4. Cấu hình môi trường

**Phần này dành cho người quản trị hoặc người phát triển ứng dụng. Người dùng thông thường không cần sửa các cấu hình này.**

### 4.1. File `.env`

File `.env` nằm trong thư mục gốc của dự án:

```text
D:\taskflow_personal\.env
```

File này có thể chứa các biến môi trường sau:

```dotenv
DATABASE_URL=CHUOI_KET_NOI_POSTGRESQL
GEMINI_API_KEY=API_KEY_GEMINI
GEMINI_MODEL=TEN_MODEL_GEMINI_DUOC_HO_TRO
```

Thay các giá trị mẫu bằng thông tin thực tế của dự án.

- `DATABASE_URL`: Chuỗi kết nối cơ sở dữ liệu.
- `GEMINI_API_KEY`: API key được cấp từ Google AI Studio.
- `GEMINI_MODEL`: Tên model Gemini được API key và tài khoản hỗ trợ.

Không sử dụng nguyên các giá trị mẫu ở trên.

### 4.2. Bảo mật cấu hình

- Không chia sẻ API key công khai.
- Không đăng tải file `.env` lên GitHub.
- Không đưa chuỗi kết nối cơ sở dữ liệu vào tài liệu hướng dẫn dành cho người dùng.
- Đảm bảo `.env` nằm trong `.gitignore`.
- Không để thông tin bí mật xuất hiện trong ảnh chụp màn hình hoặc log công khai.

---

## 5. Xử lý lỗi thường gặp

### 5.1. Không thể kết nối Backend

**Biểu hiện:** Trình duyệt không truy cập được API hoặc Frontend không lấy được dữ liệu.

**Cách xử lý:**

1. Kiểm tra Terminal Backend có đang chạy không.
2. Truy cập http://127.0.0.1:8000/docs.
3. Nếu không mở được, kiểm tra thông báo lỗi trong Terminal.
4. Đảm bảo đang chạy lệnh tại thư mục dự án.

### 5.2. Lỗi kết nối cơ sở dữ liệu

**Biểu hiện:** Backend báo lỗi kết nối PostgreSQL hoặc Supabase.

**Cách xử lý:**

1. Kiểm tra biến `DATABASE_URL` trong file `.env`.
2. Kiểm tra thông tin kết nối và quyền truy cập cơ sở dữ liệu.
3. Kiểm tra kết nối mạng.
4. Khởi động lại Backend sau khi sửa cấu hình.

Không gửi công khai chuỗi kết nối cơ sở dữ liệu khi nhờ hỗ trợ.

### 5.3. Lỗi Gemini API key

**Biểu hiện:** Tính năng AI báo thiếu API key hoặc lỗi xác thực.

**Cách xử lý:**

1. Kiểm tra biến `GEMINI_API_KEY`.
2. Kiểm tra API key có hợp lệ và còn quyền sử dụng không.
3. Khởi động lại Backend sau khi thay đổi file `.env`.

### 5.4. Gemini trả về lỗi `503 UNAVAILABLE`

**Nguyên nhân có thể:** Model đang quá tải hoặc dịch vụ tạm thời không khả dụng.

**Cách xử lý:**

1. Chờ một lúc rồi thử lại.
2. Kiểm tra trạng thái dịch vụ Gemini.
3. Kiểm tra model đang sử dụng có được hỗ trợ không.
4. Nếu lỗi kéo dài, kiểm tra log Backend.

### 5.5. Gemini trả về lỗi `429 RESOURCE_EXHAUSTED`

**Nguyên nhân có thể:** Đã chạm giới hạn yêu cầu hoặc hạn mức sử dụng.

**Cách xử lý:**

1. Chờ hạn mức được làm mới nếu phù hợp.
2. Kiểm tra giới hạn sử dụng của dự án Google AI.
3. Giảm tần suất gửi yêu cầu.
4. Kiểm tra điều kiện sử dụng và thanh toán nếu dịch vụ yêu cầu.

### 5.6. Gemini trả về lỗi `404 NOT_FOUND`

**Nguyên nhân có thể:** Tên model không tồn tại, không được hỗ trợ hoặc không khả dụng với API đang sử dụng.

**Cách xử lý:**

1. Kiểm tra biến `GEMINI_MODEL`.
2. Đối chiếu tên model với tài liệu Gemini hiện hành.
3. Chọn model được tài khoản và API hỗ trợ.
4. Khởi động lại Backend sau khi cập nhật cấu hình.

---

## 6. Triển khai ứng dụng lên Internet

Nếu muốn người khác sử dụng ứng dụng qua Internet mà không cần mở VS Code trên máy của bạn, cần triển khai các thành phần lên dịch vụ hosting phù hợp.

Một kiến trúc tham khảo:

| Thành phần | Dịch vụ tham khảo |
|---|---|
| Frontend Streamlit | Streamlit Community Cloud |
| Backend FastAPI | Render |
| Cơ sở dữ liệu PostgreSQL | Supabase |
| AI | Google Gemini API |

### Các bước tổng quát

1. Đưa mã nguồn lên GitHub, loại bỏ các thông tin bí mật.
2. Triển khai Backend FastAPI lên dịch vụ hosting.
3. Cấu hình biến môi trường cho Backend.
4. Cập nhật Frontend để gọi URL Backend công khai thay vì `127.0.0.1` hoặc `localhost`.
5. Triển khai Frontend Streamlit.
6. Kiểm tra đăng nhập, quản lý công việc, cơ sở dữ liệu và tính năng AI.
7. Chia sẻ URL ứng dụng cho người dùng.

**Lưu ý:** Đây là hướng dẫn tổng quát. Các lệnh khởi chạy, biến môi trường và cấu hình CORS cần khớp với mã nguồn thực tế của dự án.

---

## 7. Checklist trước khi sử dụng

- [ ] Đã cấu hình môi trường cần thiết.
- [ ] Backend khởi động thành công.
- [ ] Frontend khởi động thành công.
- [ ] Truy cập được giao diện ứng dụng.
- [ ] Các chức năng quản lý công việc hoạt động.
- [ ] Kết nối cơ sở dữ liệu thành công.
- [ ] Tính năng Gemini AI hoạt động.
- [ ] Không để lộ API key hoặc thông tin kết nối.

---

## 8. Lưu ý dành cho người dùng

- Khi chạy ứng dụng trên máy cá nhân, cần giữ các tiến trình Backend và Frontend hoạt động.
- Nếu ứng dụng đã được triển khai lên Internet, người dùng chỉ cần mở đường dẫn do quản trị viên cung cấp.
- Không tự ý chỉnh sửa file cấu hình hoặc xóa dữ liệu nếu chưa hiểu rõ tác động.
- Khi gặp lỗi, hãy ghi lại thông báo lỗi và gửi cho người quản trị để được hỗ trợ.

3. Chạy ứng dụng desktop
Bạn cần mở 2 terminal riêng biệt.

Terminal 1 — Khởi động backend
Mở terminal mới trong VS Code và chạy:
cd D:\taskflow_personal
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload


Giữ terminal này mở trong suốt quá trình sử dụng app.




Terminal 2 — Mở ứng dụng desktop
Nhấn nút + trong khu vực Terminal để tạo terminal mới, rồi chạy:
cd D:\taskflow_personal
.\.venv\Scripts\python.exe desktop_app.py


Cửa sổ ứng dụng Windows sẽ xuất hiện nếu code desktop đã được cập nhật và thư viện cần thiết đã cài.