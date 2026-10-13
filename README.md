# TaskFlow Personal

Ứng dụng quản lý công việc cá nhân chạy trên web và Windows desktop:
- Backend Python/FastAPI, REST API dùng chung.
- Web app bằng Streamlit.
- Windows desktop bằng Tkinter.
- Cơ sở dữ liệu SQLite mặc định để chạy thử; PostgreSQL (ví dụ Supabase) khi triển khai cloud.
- Đăng ký/đăng nhập, task CRUD, trạng thái, ưu tiên, hạn chót, lọc theo ngày.
- AI lập kế hoạch qua OpenAI API nếu cấu hình `OPENAI_API_KEY`.

> Đây là bộ khung ứng dụng chạy được, có xác thực và API. Trước khi dùng công khai, hãy cấu hình HTTPS, CORS phù hợp, sao lưu database, rate limit, và kiểm thử bảo mật.

## 1. Cài đặt trên Windows

Cài Python 3.11+ từ https://www.python.org/downloads/ và đánh dấu **Add Python to PATH**.

Mở PowerShell, chạy:

```powershell
mkdir $HOME\Projects -Force
cd $HOME\Projects
# Giải nén taskflow_personal.zip vào thư mục này, rồi:
cd .\taskflow_personal
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Nếu PowerShell chặn kích hoạt môi trường:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Chạy local

Mở terminal thứ nhất (backend):
```powershell
uvicorn backend.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

Mở terminal thứ hai (web):
```powershell
.\.venv\Scripts\Activate.ps1
streamlit run web_app.py
```
Web: http://localhost:8501

Mở terminal thứ ba (desktop):
```powershell
.\.venv\Scripts\Activate.ps1
python desktop_app.py
```

Đăng ký tài khoản trong web app trước, sau đó đăng nhập trên desktop bằng cùng tài khoản.
Local mặc định dùng `taskflow.db` trong thư mục dự án.

## 3. Cấu hình AI

Mở `.env`, đặt:
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```
Khởi động lại backend. Không đưa API key vào frontend, GitHub hoặc file được chia sẻ. Nếu không cấu hình key, tính năng AI trả về thông báo rõ ràng và các chức năng quản lý task vẫn hoạt động.

## 4. Bật database cloud (PostgreSQL/Supabase)

1. Tạo project tại https://supabase.com/
2. Vào Project Settings → Database, lấy connection string PostgreSQL phù hợp (ưu tiên connection pooler khi nền tảng yêu cầu).
3. Đặt `DATABASE_URL` trong `.env` cho local hoặc biến môi trường trên host triển khai backend. Ví dụ:
```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:6543/postgres
```
Nếu URL do nhà cung cấp đưa ra bắt đầu bằng `postgres://` hoặc `postgresql://`, ứng dụng tự chuyển sang driver `psycopg`.
4. Giữ `SECRET_KEY` bí mật và dài ngẫu nhiên. Không commit `.env`.
5. Khi backend và web được deploy lên host, cấu hình `API_BASE_URL` của web/desktop trỏ về URL HTTPS của backend.

Lưu ý: dùng PostgreSQL qua backend API, không kết nối trực tiếp database từ trình duyệt. Chỉ backend được giữ thông tin kết nối database. Nếu deploy công khai, bật SSL theo yêu cầu nhà cung cấp và đặt firewall/network restrictions phù hợp.

## 5. Deploy web/cloud

Deploy backend lên một Python host hỗ trợ ASGI (ví dụ Render, Railway hoặc VPS), lệnh start:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```
Đặt biến môi trường `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY` (nếu dùng AI), `CORS_ORIGINS`.
Deploy `web_app.py` lên host hỗ trợ Streamlit và đặt `API_BASE_URL=https://your-backend-domain`.
Với Streamlit Community Cloud, thêm `API_BASE_URL` trong phần Secrets hoặc biến môi trường của host. Desktop app dùng cùng `API_BASE_URL` trong `.env`.

## 6. Build desktop thành EXE (tuỳ chọn)

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name TaskFlow desktop_app.py
```
File tạo ở `dist\TaskFlow.exe`. Đặt `API_BASE_URL` trong `.env` cạnh file chạy hoặc sửa cấu hình desktop trước khi build. Không đóng gói secrets vào EXE.

## Cấu trúc

```text
taskflow_personal/
├── backend/
│   ├── __init__.py
│   ├── auth.py
│   ├── database.py
│   ├── main.py
│   └── models.py
├── web_app.py
├── desktop_app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
