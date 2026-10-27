# Triển khai lên server — đọc khi cần

Bộ khung mặc định phục vụ phát triển local. Chỉ thực hiện phần này khi đã chọn server, domain, PostgreSQL và cấu hình HTTPS.

## Chuẩn bị

Cài thêm thư viện dùng trên server:

```text
python -m pip install -r requirements-production.txt
```

Cấu hình môi trường:

```dotenv
DJANGO_SETTINGS_MODULE=core.production
DEBUG=False
SECRET_KEY=THAY_BANG_KHOA_NGAU_NHIEN_DAI_IT_NHAT_50_KY_TU
ALLOWED_HOSTS=api.example.com
POSTGRES_DB=my_project
POSTGRES_USER=my_project
POSTGRES_PASSWORD=THAY_BANG_MAT_KHAU_DATABASE
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
CORS_ALLOWED_ORIGINS=https://app.example.com
TRUST_PROXY_SSL_HEADER=False
```

Sinh SECRET_KEY bằng `python -c "import secrets; print(secrets.token_urlsafe(64))"`. Không dùng nguyên chuỗi ví dụ và không đưa secrets vào Git.

## Chạy trên Ubuntu

Trong terminal đã activate venv và cấu hình đủ biến môi trường:

```bash
export DJANGO_SETTINGS_MODULE=core.production
python src/manage.py check --deploy --fail-level WARNING
python src/manage.py migrate --noinput
python -m uvicorn core.asgi:application --app-dir src --host 127.0.0.1 --port 8000
```

Lưu ý: `manage.py` nạp file .env qua settings, còn Uvicorn cần biết profile trước khi import ứng dụng. Vì vậy phải export DJANGO_SETTINGS_MODULE như trên, không chỉ ghi biến này trong file .env.

Dùng supervisor của hệ thống hoặc nền tảng triển khai để giữ ứng dụng chạy. Không dùng `runserver` hoặc `--reload` cho server thật.

## Các việc cần hoàn tất trước khi public

- Đặt Nginx hoặc reverse proxy trước ứng dụng và cấu hình HTTPS.
- Chỉ bật TRUST_PROXY_SSL_HEADER nếu proxy xóa header client rồi tự gán X-Forwarded-Proto.
- Profile bật HSTS cho toàn bộ subdomain; điều chỉnh nếu chưa phải mọi subdomain đều dùng HTTPS.
- Backup PostgreSQL và kiểm tra khôi phục dữ liệu.
- Chạy migrations một lần trong bước release, không chạy đồng thời trên nhiều web instance.
- Backend không phục vụ static/frontend. Nếu sau này có API upload, thiết kế lưu trữ và phân quyền file riêng.
- Giới hạn request tại proxy. Throttle mặc định trong bộ nhớ chỉ áp dụng riêng từng process; khi chạy nhiều process cần bổ sung cache dùng chung hoặc giới hạn tại gateway.
- Dọn token hết hạn định kỳ bằng `python src/manage.py flushexpiredtokens`.

`/health/live/` kiểm tra ứng dụng có phản hồi; `/health/ready/` kiểm tra kết nối database. Hai URL không thay thế hệ thống giám sát đầy đủ.

Schema JSON `/schema/` trên production yêu cầu Bearer JWT của tài khoản role admin hoặc superuser. Có thể xuất schema bằng management command để xem trên công cụ bên ngoài; không cần session hay trang đăng nhập HTML. Docker Compose trong repository chỉ để chạy thử local; khi deploy image, truyền profile và secrets từ hệ thống vận hành.

requirements pin phiên bản các thư viện trực tiếp, chưa khóa toàn bộ thư viện phụ thuộc. Với dự án triển khai thật, tạo lock của môi trường release và kiểm tra lại trước khi cập nhật.
