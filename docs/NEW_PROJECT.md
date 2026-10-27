# Dùng base để tạo backend dự án mới

Base chỉ chứa backend. Frontend (web/mobile) đặt ở dự án riêng và gọi API; không thêm template, trang HTML hay mã frontend vào source này.

## 1. Sao chép sang thư mục mới

Giữ thư mục base để dùng lại. Tạo dự án ở **một thư mục mới**, không sao chép đè lên dự án đang có.

Không mang theo `.venv`, `.env`, database local, file cache hoặc lịch sử Git của base.

Windows CMD:

```bat
robocopy D:\DEVs\django-base D:\DEVs\my-project /E /XD .venv .git __pycache__ staticfiles .ruff_cache /XF .env *.sqlite3 .coverage schema.yml
cd /d D:\DEVs\my-project
```

Robocopy có thể trả mã 1 khi đã copy thành công; chỉ mã từ 8 trở lên mới biểu thị lỗi.

Ubuntu, dùng rsync (cài bằng `sudo apt install rsync` nếu chưa có):

```bash
cd /duong-dan/den/django-base
mkdir ../my-project
rsync -a --exclude='.venv' --exclude='.git' --exclude='__pycache__' \
  --exclude='staticfiles' --exclude='.ruff_cache' --exclude='.env' \
  --exclude='*.sqlite3' --exclude='.coverage' --exclude='schema.yml' ./ ../my-project/
cd ../my-project
```

Nếu đã đưa base lên GitHub, cũng có thể bật **Template repository** rồi dùng **Use this template** để tạo repository mới.

## 2. Tạo môi trường mới

Chạy lại hướng dẫn trong [SETUP](SETUP.md): tạo venv, cài thư viện, tạo `.env`, migrate và createsuperuser. Không dùng lại database hoặc tài khoản quản trị từ dự án cũ.

Sinh SECRET_KEY mới:

```text
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Chép kết quả vào `.env`. Chỉnh tên API trong `SPECTACULAR_SETTINGS` của `core/settings.py`, rồi sửa README theo tên dự án.

Tên thư mục `core` chỉ là nơi chứa cấu hình; không bắt buộc đổi tên nó theo tên sản phẩm.

## 3. Tạo module nghiệp vụ đầu tiên

Ví dụ tạo module `products`. Bắt đầu bằng cách sao chép mẫu đang chạy được, sau đó đổi các trường theo nghiệp vụ.

Từ thư mục gốc dự án mới, đã activate venv:

Windows CMD:

```bat
mkdir src\apps\products
python src\manage.py startapp products src\apps\products
mkdir src\apps\products\v1
mkdir src\apps\products\v1\serializers
mkdir src\apps\products\v1\views
type nul > src\apps\products\v1\__init__.py
type nul > src\apps\products\v1\serializers\__init__.py
type nul > src\apps\products\v1\views\__init__.py
copy src\apps\samples\models.py src\apps\products\models.py
copy src\apps\samples\services.py src\apps\products\services.py
copy src\apps\samples\v1\serializers\samples.py src\apps\products\v1\serializers\products.py
copy src\apps\samples\v1\views\samples.py src\apps\products\v1\views\products.py
copy src\apps\samples\v1\urls.py src\apps\products\v1\urls.py
```

Ubuntu:

```bash
mkdir -p src/apps/products
python src/manage.py startapp products src/apps/products
mkdir -p src/apps/products/v1/serializers src/apps/products/v1/views
touch src/apps/products/v1/__init__.py
touch src/apps/products/v1/serializers/__init__.py src/apps/products/v1/views/__init__.py
cp src/apps/samples/models.py src/apps/products/models.py
cp src/apps/samples/services.py src/apps/products/services.py
cp src/apps/samples/v1/serializers/samples.py src/apps/products/v1/serializers/products.py
cp src/apps/samples/v1/views/samples.py src/apps/products/v1/views/products.py
cp src/apps/samples/v1/urls.py src/apps/products/v1/urls.py
```

Không sao chép migrations của samples sang products. Django sẽ tạo migration mới cho Product.

## 4. Sửa tên trong module mới

Chỉ tìm/thay trong **src/apps/products**, không sửa toàn bộ repository:

| Tên cũ | Tên mới |
|---|---|
| SampleItem | Product |
| samples | products |
| sample_items | products |
| sample-v1 | product-v1 |

Thay `SampleItem` sẽ đồng thời đổi tên `SampleItemSerializer`, `SampleItemService` và `SampleItemViewSetV1`. Đổi mô tả tiếng Việt từ “mục mẫu” sang “sản phẩm”.

Trong `apps/products/apps.py`, sửa tên đầy đủ:

```python
from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.products"
    verbose_name = "Sản phẩm"
```

Thêm `"apps.products.apps.ProductsConfig"` vào INSTALLED_APPS trong `core/settings.py`.

Thêm URL trong urlpatterns của `core/urls.py`:

```python
path("api/v1/products/", include("apps.products.v1.urls")),
```

Lúc này Product vẫn có các trường giống sample, nhưng module API độc lập đã được đăng ký. Bạn có thể đổi dần field trong model, serializer và `writable_fields` của service theo nghiệp vụ thật.

Lệnh startapp sinh cả `admin.py` và `views.py` ở gốc products. Hai file này không dùng trong base backend API; xóa chúng bằng `del src\apps\products\admin.py src\apps\products\views.py` (CMD) hoặc `rm src/apps/products/admin.py src/apps/products/views.py` (Ubuntu). API của module nằm trong v1/views.

## 5. Tạo database và thử API mới

```text
python src/manage.py makemigrations products
python src/manage.py migrate
python src/manage.py check
python src/manage.py runserver
```

Dùng curl/Postman gọi `/api/v1/products/` với cùng JWT đã đăng nhập. Schema JSON tại `/schema/` có các endpoint mới.

Thêm test trong `apps/products/tests.py`, tham khảo các tình huống của samples:

- Chưa đăng nhập bị từ chối.
- Tạo đúng dữ liệu thì thành công.
- Không đọc/sửa/xóa được dữ liệu người khác.
- Admin có quyền phù hợp.
- Dữ liệu sai không được lưu.

Chạy lại:

```text
python src/manage.py test apps --settings=core.test_settings
```

## 6. Khi nghiệp vụ lớn hơn

Giữ logic tính toán và quy tắc ghi dữ liệu trong service. Khi truy vấn quá dài hoặc được dùng lại nhiều nơi, lúc đó mới tách `selectors.py`. Khi thực sự cần tác vụ nền mới thêm Celery; cần đăng nhập Google mới thêm OAuth.

Có thể giữ module samples làm ví dụ. Nếu muốn bỏ hẳn khỏi dự án mới, xóa các file/module liên quan và gỡ đăng ký app/URL trong một thay đổi có kiểm tra; với database đã có dữ liệu phải lập kế hoạch migration riêng.
