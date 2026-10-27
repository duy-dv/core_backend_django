# Cài đặt và chạy dự án

Các lệnh được chạy tại thư mục gốc, nơi có `requirements.txt`. Cần Python 3.12. Mặc định dùng SQLite, không cần Docker, Redis hoặc PostgreSQL.

## Windows CMD

```bat
cd /d D:\DEVs\django-base
py -3.12 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
copy .env.example .env
python src\manage.py migrate
python src\manage.py createsuperuser
python src\manage.py runserver
```

Ý nghĩa từng bước:

1. `cd /d`: chuyển ổ đĩa và thư mục trong CMD.
2. `venv`: tạo môi trường thư viện riêng cho dự án.
3. `activate.bat`: dùng Python và thư viện trong môi trường đó.
4. `pip install`: cài thư viện.
5. `copy`: tạo file cấu hình local; không ghi đè nếu đã có.
6. `migrate`: tạo/cập nhật các bảng database từ migrations đã có.
7. `createsuperuser`: tạo tài khoản quản trị để đăng nhập và gọi API bằng JWT.
8. `runserver`: chạy server phát triển; Ctrl+C để dừng.

Lần mở CMD tiếp theo, không cần làm lại tất cả:

```bat
cd /d D:\DEVs\django-base
call .venv\Scripts\activate.bat
python src\manage.py runserver
```

## Ubuntu

Với Ubuntu 24.04, cài Python một lần:

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

Tạo môi trường và chạy:

```bash
cd /duong-dan/den/django-base
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python src/manage.py migrate
python src/manage.py createsuperuser
python src/manage.py runserver
```

Lần sau chỉ cần vào thư mục, activate venv rồi runserver. Ubuntu khác phiên bản có thể cần cách cài Python 3.12 khác.

## File .env

Các giá trị cần hiểu khi mới bắt đầu:

| Biến | Ý nghĩa |
|---|---|
| DEBUG | True khi phát triển; server thật dùng cấu hình production |
| SECRET_KEY | Khóa bí mật của dự án; tạo khóa mới cho mỗi dự án |
| ALLOWED_HOSTS | Host được phép truy cập Django, ví dụ localhost |
| CORS_ALLOWED_ORIGINS | Địa chỉ frontend, ví dụ http://localhost:3000 |
| POSTGRES_DB | Để trống thì dùng SQLite |
| JWT_ACCESS_MINUTES | Thời hạn access token, mặc định 15 phút |
| JWT_REFRESH_DAYS | Thời hạn refresh token, mặc định 7 ngày |

Không đưa `.env` vào Git. Biến môi trường đã đặt trong terminal ưu tiên hơn giá trị trong file.

## Sau khi thay đổi code

- Thay view/serializer/service: runserver thường tự tải lại.
- Thay model: chạy hai lệnh:

```text
python src/manage.py makemigrations
python src/manage.py migrate
```

`makemigrations` tạo file mô tả thay đổi; `migrate` áp dụng thay đổi đó vào database. Đưa các file migration vào Git cùng code. Không xóa migration đã được dùng chỉ để sửa lỗi.

## PostgreSQL / Docker — tùy chọn

Khi muốn thử PostgreSQL, có thể dùng Docker Compose. Tạo `.env` trước bằng lệnh copy/cp ở trên:

```text
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose logs --tail=100 web
```

Compose chỉ có hai dịch vụ: web và PostgreSQL. Kiểm tra `http://127.0.0.1:8000/health/live/`; schema JSON ở `/schema/`. Compose này dành cho local, không phải cấu hình public server.

Dừng các container bằng `docker compose down`. Database vẫn được giữ trong volume. Sau khi thay code, chạy lại `docker compose up -d --build` vì source không được mount vào container.

Nếu chạy Python trực tiếp và chỉ chạy PostgreSQL bằng Docker:

```text
docker compose up -d postgres
python -m pip install -r requirements-production.txt
```

Sửa `.env`:

```dotenv
POSTGRES_DB=django_base
POSTGRES_USER=django
POSTGRES_PASSWORD=local-dev-only
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Sau đó chạy `python src/manage.py migrate`. Trong container host là `postgres`; trên máy cá nhân host là `localhost`.

## Kiểm tra và xử lý lỗi

```text
python -m pip install -r requirements-dev.txt
python src/manage.py check
python src/manage.py test apps --settings=core.test_settings
python -m ruff check src
python -m ruff format src
```

| Lỗi | Cách xử lý |
|---|---|
| CMD không nhận py/python | Cài Python 3.12 và mở lại CMD |
| No module named django | Activate đúng venv, chạy lại pip install |
| Không kết nối database | Để POSTGRES_DB trống nếu đang dùng SQLite |
| Port 8000 bị chiếm | Chạy `python src/manage.py runserver 8001` |
| DisallowedHost | Thêm hostname cụ thể vào ALLOWED_HOSTS, không thêm scheme/port |
| API trả 401 | Đăng nhập và gửi access token trong Authorization |
| API trả 404 khi dùng ID khác | Kiểm tra bản ghi có thuộc tài khoản đang đăng nhập không |
| API trả 429 | Đã gọi quá nhiều lần; chờ cửa sổ giới hạn kết thúc |
