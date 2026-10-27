# Ghi chú về bản cơ bản

Theo mục tiêu dùng lại để khởi tạo dự án mới, base đã được tinh gọn:

- Giữ Django/DRF, user, JWT, CRUD mẫu, phân quyền, phân trang, tìm kiếm và schema OpenAPI JSON.
- Bỏ Google login, Celery/Redis, selectors riêng, mixin CRUD tổng quát và thống kê. Giữ lại hai API dùng chung minimal/delete-many.
- Dùng một serializer cho CRUD mẫu, thêm serializer rút gọn riêng cho minimal và các hành động sẵn có của ModelViewSet.
- Tách thư viện PostgreSQL/server sang requirements-production.txt, không bắt buộc khi chạy local.
- Comment giải thích và hướng dẫn đều bằng tiếng Việt.
- Chỉ phục vụ backend API: bỏ Django Admin, template engine, session, staticfiles và HTML renderer; ViewSet là endpoint HTTP/JSON.
- Có hướng dẫn sao chép base và thêm module trong NEW_PROJECT.md.

Các lỗi bảo mật đã sửa vẫn được bảo vệ: người đăng ký không tự chọn admin; không truy cập sample của người khác; refresh token được xoay vòng và blacklist; tài khoản bị khóa không dùng token cũ; mật khẩu được băm và kiểm tra độ mạnh.

## Nếu đã dùng phiên bản trước

- Các URL giao diện /admin/, /docs/, /redoc/ đã bỏ; lấy hợp đồng API tại /schema/ hoặc xuất file OpenAPI JSON.
- minimal và delete-many đã được khôi phục cho users/samples; vẫn là API JSON, không có giao diện.
- Google login, stats, change-status chưa có trong bản hiện tại.
- Đổi status bằng PATCH /api/v1/samples/{id}/.
- Phản hồi sample không còn owner_name/owner_email; chỉ trả ID owner.
- Login trả thông tin user bằng UserSerializer chung.
- Migration users/0002_delete_externalidentity bỏ bảng liên kết Google cũ. Giữ lịch sử migration để database đã dùng bản trước vẫn nâng cấp đúng; với database mới Django tự chạy cả lịch sử.
- Nếu đã có dữ liệu Google identity cần giữ, backup và lập kế hoạch chuyển dữ liệu trước khi áp dụng migration đó. Base cơ bản không còn luồng OAuth.

## Kiểm tra

Bản backend API hiện tại: có kiểm thử quyền đọc minimal, selected_ids, phân trang, xóa nhiều bản ghi và quy tắc bảo vệ user. Kết quả mới nhất lấy từ các lệnh kiểm thử trong README. Có test xác nhận API chỉ trả JSON, không có session/template và các URL giao diện cũ đã bị gỡ.

Django check, migration, Ruff và kiểm tra schema OpenAPI đều đạt. Cấu hình production qua check --deploy không có cảnh báo; chưa chạy Docker hoặc PostgreSQL thực tế tại máy này.

Chạy các lệnh trong README để kiểm tra phiên bản hiện tại. Test local dùng SQLite; test cạnh tranh refresh chỉ chạy trên PostgreSQL. CI có kiểm tra SQLite và PostgreSQL nhưng cần được chạy trên GitHub mới có kết quả của môi trường đó.

Không xem test pass là xác nhận sẵn sàng cho mọi hệ thống production. Khi dự án mới có nghiệp vụ, cần thêm test và cấu hình vận hành tương ứng.
