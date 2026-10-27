# Sử dụng API

Chạy server trước. Backend chỉ nhận/trả dữ liệu qua HTTP, không có trang HTML. Dùng curl/Postman để gọi API; nhập [schema JSON](http://127.0.0.1:8000/schema/) vào công cụ hỗ trợ OpenAPI nếu cần xem hợp đồng API.

## Thử theo thứ tự

1. Gọi `POST /api/v1/users/auth/register/` để tạo tài khoản thường.
2. Gọi `POST /api/v1/users/auth/login/` bằng email và mật khẩu vừa tạo.
3. Sao chép `access`; gửi header `Authorization: Bearer ACCESS_TOKEN` trong curl hoặc chọn Bearer Token ở Postman.
4. Gọi `POST /api/v1/samples/` để tạo dữ liệu.
5. Gọi `GET /api/v1/samples/` để xem danh sách.
6. Dùng ID vừa nhận để xem, sửa hoặc xóa bản ghi.

Các URL đều kết thúc bằng `/`.

## Tài khoản

| Method | Đường dẫn | Chức năng |
|---|---|---|
| POST | /api/v1/users/auth/register/ | Đăng ký tài khoản thường |
| POST | /api/v1/users/auth/login/ | Đăng nhập bằng email/mật khẩu |
| POST | /api/v1/users/auth/refresh/ | Lấy cặp token mới |
| POST | /api/v1/users/auth/logout/ | Vô hiệu hóa refresh token hiện tại |
| GET | /api/v1/users/me/ | Xem thông tin bản thân |
| GET, POST | /api/v1/users/ | Admin xem danh sách/tạo tài khoản |
| GET, PUT, PATCH, DELETE | /api/v1/users/{id}/ | Admin xem/sửa/xóa tài khoản |

Dữ liệu đăng ký:

```json
{
  "email": "demo@example.com",
  "password": "LocalDemo-pass-123",
  "full_name": "Người dùng thử"
}
```

Mật khẩu tối thiểu 10 ký tự và được kiểm tra bằng bộ quy tắc của Django. `phone_number` không bắt buộc. Không gửi `role`, `is_staff` hay `is_superuser` khi đăng ký.

Đăng nhập trả `access`, `refresh` và `user`. Khi gọi API cần xác thực, gửi header:

```text
Authorization: Bearer ACCESS_TOKEN
```

Access mặc định hết hạn sau 15 phút. Gửi refresh đến endpoint refresh:

```json
{"refresh": "REFRESH_TOKEN"}
```

Lưu lại **cả access và refresh mới**; refresh cũ không dùng lại được. Client không gửi nhiều yêu cầu refresh đồng thời.

Logout cũng nhận JSON như trên và trả 204, không có body. Logout không thu hồi ngay access token đã cấp; nó vẫn dùng được đến khi hết hạn. Khóa tài khoản, vô hiệu hóa tài khoản hoặc đổi mật khẩu sẽ chặn token cũ.

Role admin hoặc superuser quản lý API. `is_staff` chỉ giữ để tương thích model User của Django, không dùng để cấp quyền API và không có trang Django Admin. Staff và manager hiện có quyền dữ liệu mẫu như nhau. API không cho sửa/xóa chính tài khoản admin đang dùng hoặc superuser.

## CRUD mẫu

| Method | Đường dẫn | Chức năng |
|---|---|---|
| GET | /api/v1/samples/ | Danh sách bản ghi của mình |
| POST | /api/v1/samples/ | Tạo bản ghi |
| GET | /api/v1/samples/{id}/ | Xem chi tiết |
| PUT | /api/v1/samples/{id}/ | Cập nhật, cần các trường bắt buộc |
| PATCH | /api/v1/samples/{id}/ | Chỉ cập nhật các trường được gửi |
| DELETE | /api/v1/samples/{id}/ | Xóa bản ghi |

Admin được quản lý tất cả sample. Người dùng thường chỉ truy cập sample của mình.

Tạo mới đơn giản:

```json
{"title": "Công việc đầu tiên", "description": "Dữ liệu để thử API"}
```

Các trường mở rộng:

| Trường | Giá trị |
|---|---|
| status | ACTIVE, INACTIVE, ARCHIVED; mặc định ACTIVE |
| priority | LOW, MEDIUM, HIGH, CRITICAL; mặc định MEDIUM |
| metadata | Dữ liệu JSON bổ sung, mặc định {} |

`owner`, `created_by`, `updated_by` và các mốc thời gian do máy chủ gán. Client không được sửa. Đổi status bằng PATCH thông thường, không có endpoint riêng.

Lọc và tìm kiếm:

```text
/api/v1/samples/?status=ACTIVE&search=đầu&page=1&page_size=20
/api/v1/samples/?ordering=-created_at
```

Page size mặc định 10, tối đa 100. Danh sách trả về:

```json
{"count": 1, "next": null, "previous": null, "results": [{"id": "...", "title": "..."}]}
```

Lỗi đầu vào trả 400, giữ lỗi theo từng trường:

```json
{"detail": "Yêu cầu không hợp lệ.", "errors": {"title": ["Trường này không được để trống."]}}
```

## Ví dụ Windows CMD

```bat
curl -X POST http://127.0.0.1:8000/api/v1/users/auth/register/ -H "Content-Type: application/json" -d "{\"email\":\"demo@example.com\",\"password\":\"LocalDemo-pass-123\",\"full_name\":\"Demo\"}"
curl -X POST http://127.0.0.1:8000/api/v1/users/auth/login/ -H "Content-Type: application/json" -d "{\"email\":\"demo@example.com\",\"password\":\"LocalDemo-pass-123\"}"
set ACCESS=DAN_ACCESS_TOKEN_VAO_DAY
curl -X POST http://127.0.0.1:8000/api/v1/samples/ -H "Authorization: Bearer %ACCESS%" -H "Content-Type: application/json" -d "{\"title\":\"Ban ghi dau tien\"}"
curl http://127.0.0.1:8000/api/v1/samples/ -H "Authorization: Bearer %ACCESS%"
```

## Ví dụ Ubuntu

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"LocalDemo-pass-123","full_name":"Demo"}'
curl -X POST http://127.0.0.1:8000/api/v1/users/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"LocalDemo-pass-123"}'
export ACCESS='DAN_ACCESS_TOKEN_VAO_DAY'
curl -X POST http://127.0.0.1:8000/api/v1/samples/ \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"title":"Ban ghi dau tien"}'
curl http://127.0.0.1:8000/api/v1/samples/ -H "Authorization: Bearer $ACCESS"
```

Mật khẩu ví dụ chỉ dùng thử ở local, không dùng làm mật khẩu thật.

Tạo quản trị viên bằng `python src/manage.py createsuperuser`, rồi đăng nhập qua endpoint login như tài khoản thường.

Có thể xuất schema ra file để nhập vào công cụ tài liệu bên ngoài:

```text
python src/manage.py spectacular --format openapi-json --file openapi.json
```

## Lấy dữ liệu rút gọn và xóa nhiều bản ghi

| Method | Đường dẫn | Quyền |
|---|---|---|
| GET | /api/v1/users/minimal/ | Admin |
| POST | /api/v1/users/delete-many/ | Admin |
| GET | /api/v1/samples/minimal/ | Người đăng nhập: dữ liệu của mình; admin: mọi bản ghi |
| POST | /api/v1/samples/delete-many/ | Người đăng nhập: dữ liệu của mình; admin: mọi bản ghi |

### minimal

Dùng cho frontend cần dữ liệu gọn để hiển thị ô lựa chọn. Đây chỉ là API dữ liệu, không chứa HTML.

- User: id, email, full_name, role.
- Sample: id, title, status.
- Hỗ trợ page, page_size, search, ordering và các bộ lọc giống API list.
- selected_ids nhận tối đa 100 UUID phân cách bằng dấu phẩy. ID sai định dạng trả 400. ID không tồn tại hoặc ngoài quyền đọc không được bổ sung vào kết quả.

Ví dụ:

```text
GET /api/v1/samples/minimal/?search=demo&page_size=10&selected_ids=UUID_1,UUID_2
```

Kết quả có count, next, previous, results như API list. Các mục đã chọn không nằm trên trang tìm kiếm được thêm vào results, không lặp ID và không vượt quyền đọc. Vì vậy results có thể dài hơn page_size; count/next/previous vẫn mô tả kết quả tìm kiếm, không tính thêm mục được chọn.

### delete_many

Tên hàm Python là delete_many; URL là **delete-many/**. Gửi JSON:

```json
{"ids": ["UUID_1", "UUID_2"]}
```

Danh sách cần từ 1 đến 100 UUID. ID trùng được xử lý một lần. Thành công trả **204, body rỗng**. Nếu một ID không tồn tại/ngoài phạm vi đọc thì trả 400; nếu không được phép xóa thì trả 403. Trong cả hai trường hợp không xóa bản ghi nào.

Admin không được dùng API này để xóa chính mình hoặc superuser. Các bộ lọc tìm kiếm không quyết định danh sách bị xóa: ids là danh sách chỉ định, được giới hạn bởi phạm vi quyền của người gọi.
