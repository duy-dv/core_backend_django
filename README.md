# Django + DRF — Base source backend API

Dự án này chỉ chứa **source backend API**, dùng làm điểm bắt đầu cho backend của các dự án mới. Frontend được phát triển riêng và giao tiếp với backend bằng HTTP/JSON. Không triển khai giao diện theo MVC/MVT, không có template hoặc trang Django Admin. Mục tiêu là dễ đọc, dễ chạy và dễ thêm chức năng. Comment giải thích và tài liệu đều bằng tiếng Việt; tên biến, hàm và class giữ tiếng Anh theo quy ước Python.

## Base có những gì?

- Django + Django REST Framework, mặc định chạy bằng SQLite.
- Đăng ký, đăng nhập email/mật khẩu, refresh token và đăng xuất bằng JWT.
- User có vai trò và quyền quản trị qua API; tạo superuser bằng CLI.
- Một module `samples` minh họa thêm, xem, sửa, xóa dữ liệu (CRUD).
- API `minimal` lấy dữ liệu rút gọn và `delete-many` xóa nhiều bản ghi cho users/samples.
- Phân quyền: người dùng chỉ truy cập dữ liệu của mình; admin quản lý toàn bộ.
- Phân trang, lọc, tìm kiếm, lỗi JSON và OpenAPI schema để nhập vào Postman/Swagger.
- Test cho các hành vi cơ bản và các trường hợp sai quyền.

Base không yêu cầu Google OAuth, Redis hay Celery. PostgreSQL và Docker là **tùy chọn**, đọc sau khi đã chạy được local.

## Chạy trên Windows CMD

Cài Python 3.12 trước. Mở **Command Prompt** rồi chạy:

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

Nếu đã có `.venv` thì chỉ cần activate; nếu đã có `.env` thì giữ file đó, không ghi đè.

## Chạy trên Ubuntu

Ví dụ Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv
cd /duong-dan/den/django-base
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python src/manage.py migrate
python src/manage.py createsuperuser
python src/manage.py runserver
```

Giữ `POSTGRES_DB=` trống trong `.env` để dùng SQLite. Không cần cài database riêng.

Mở:

- [OpenAPI schema JSON](http://127.0.0.1:8000/schema/)
- [Kiểm tra backend đang chạy](http://127.0.0.1:8000/health/live/)

Dùng curl hoặc Postman để thử API theo hướng dẫn bên dưới; backend không phục vụ trang HTML.

## Nên đọc theo thứ tự nào?

1. [Cài đặt và chạy lại dự án](docs/SETUP.md).
2. [Thử đăng nhập và CRUD](docs/API.md).
3. [Hiểu từng file và luồng xử lý](docs/ARCHITECTURE.md).
4. [Dùng base để tạo dự án mới](docs/NEW_PROJECT.md).

[Triển khai lên server](docs/DEPLOYMENT.md) là phần tùy chọn, không cần đọc ngay.

[Cấu hình nâng cao: Redis, Celery và WebSocket](docs/ADVANCED_CONFIGURATION.md) hướng dẫn bổ sung cache, tác vụ nền và kết nối thời gian thực khi dự án cần.

## Cấu trúc chính

```text
src/
  manage.py                 Chạy các lệnh Django
  core/
    settings.py             Cấu hình chạy local
    urls.py                 Các đường dẫn chính
    production.py           Cấu hình server, đọc sau
    test_settings.py        Cấu hình chạy test
  apps/
    users/                  Tài khoản và xác thực
    samples/                Module CRUD mẫu để tham khảo
      models.py             Cấu trúc bảng dữ liệu
      services.py           Kiểm tra nghiệp vụ và ghi dữ liệu
      migrations/           Lịch sử thay đổi cấu trúc database
      tests/                Kiểm thử
      v1/
        urls.py             Đường dẫn API
        serializers/
          samples.py        JSON đầu vào/đầu ra và kiểm tra dữ liệu
        views/
          samples.py        Endpoint API: nhận HTTP và trả JSON
  shared/
    models.py               UUID và thông tin tạo/sửa dùng chung
    constants.py            Vai trò, trạng thái, mức ưu tiên
    mixins.py               API minimal và delete-many dùng chung
    serializers.py          Kiểm tra danh sách UUID
    services.py             Xóa nhiều bản ghi trong một giao dịch
    permissions.py          Kiểm tra quyền admin
    pagination.py           Cấu hình phân trang
    exceptions/handle.py    Định dạng lỗi API
```

Để hiểu một chức năng từ đầu đến cuối, đọc module `samples` trước. Không cần đọc hết phần xác thực JWT mới bắt đầu viết nghiệp vụ.

## Chạy test

Sau khi activate venv, chạy từ thư mục gốc trên cả CMD và Ubuntu:

```text
python -m pip install -r requirements-dev.txt
python src/manage.py test apps --settings=core.test_settings
python src/manage.py check
python -m ruff check src
```

Không dùng `test_settings` để chạy server thật. Test sử dụng database tạm, không thay dữ liệu local.

## Nguyên tắc của base

**HTTP request → API ViewSet → Serializer → Service → Model/ORM → Database → JSON response.**

Tên thư mục `views` theo quy ước DRF: đây là API handler, không render HTML. Model là cấu trúc dữ liệu ORM; không có tầng giao diện/template trong base.

Giữ rõ trách nhiệm, ưu tiên thành phần có sẵn của Django/DRF. Chưa cần repository, interface hoặc lớp service cơ sở. Hai mixin nhỏ chỉ dùng để chia sẻ minimal và delete-many giữa các module. Khi dự án có nhu cầu cụ thể mới bổ sung.

Phiên bản thư viện được ghi trong `requirements.txt`. [Ghi chú thay đổi](docs/REVIEW.md) mô tả những phần đã tinh gọn so với bản trước.
