# Kiến trúc backend API

Đây là backend phân lớp đơn giản, không xây trang web theo MVC/MVT. Frontend là ứng dụng riêng. Không có template, form HTML, session đăng nhập hay trang quản trị Django.

## Bốn phần cần nắm

| Phần | Trách nhiệm | Ví dụ |
|---|---|---|
| Model | Khai báo dữ liệu lưu trong database | SampleItem có title và owner |
| Serializer | Chuyển JSON ↔ dữ liệu Python; kiểm tra dữ liệu đầu vào | title không được rỗng |
| API ViewSet | Nhận HTTP và trả JSON, kiểm tra đăng nhập/phạm vi dữ liệu | Chỉ lấy sample của người đang đăng nhập |
| Service | Xử lý nghiệp vụ khi ghi dữ liệu | Gán người tạo, kiểm tra quyền rồi lưu |

`ViewSet` là tên lớp của DRF để triển khai endpoint, không phải giao diện. Model/serializer vẫn cần cho ORM và dữ liệu JSON dù backend không có tầng template. URL nối địa chỉ API với ViewSet. `core` chứa cấu hình chung; `apps` chứa từng chức năng; `shared` chứa các phần dùng lại.

## Ví dụ: tạo sample

Client gửi:

```text
POST /api/v1/samples/
{"title": "Việc cần làm"}
```

Luồng thực tế:

1. `core/urls.py` chuyển URL sang `apps/samples/v1/urls.py`.
2. Router gọi hành động create có sẵn trong `ModelViewSet`.
3. DRF kiểm tra JWT và dùng `SampleItemSerializer` kiểm tra dữ liệu.
4. DRF gọi `perform_create()` trong view.
5. View gọi `SampleItemService.create_item()`.
6. Service gán owner/created_by/updated_by bằng người đang đăng nhập và lưu model.
7. Serializer chuyển bản ghi vừa tạo thành JSON; DRF trả HTTP 201.

Ở view có dòng:

```python
serializer.instance = SampleItemService.create_item(
    owner=self.request.user,
    **serializer.validated_data,
)
```

`validated_data` là dữ liệu đã qua kiểm tra. `**` truyền các phần tử của dict thành tham số. `instance` là bản ghi vừa được lưu, để DRF biết cần trả dữ liệu nào.

## Vì sao có service?

CRUD rất nhỏ có thể gọi `serializer.save()` trực tiếp. Base này giữ một file `services.py` để khi thêm quy tắc nghiệp vụ, bạn có chỗ rõ ràng để viết.

Ví dụ sau này cần kiểm tra hạn mức trước khi tạo đơn hàng: đặt ở service để API, tác vụ nền hoặc management command đều dùng lại được. Không truyền `request` vào service; chỉ truyền người thực hiện, đối tượng và dữ liệu cần thiết.

## Phân quyền nằm ở đâu?

- Đăng nhập: cấu hình mặc định trong `core/settings.py`.
- Quyền quản trị user: `IsAdmin` trong `shared/permissions.py`.
- Chỉ đọc dữ liệu của mình: `get_queryset()` trong sample view.
- Kiểm tra quyền trước khi ghi: service kiểm tra owner hoặc admin.

`get_object()` của DRF cũng tìm trong `get_queryset()`. Vì vậy biết UUID của người khác vẫn không đọc/sửa/xóa được bản ghi của họ.

`role=admin` hoặc `is_superuser=True` cho quản trị qua API. Trường `is_staff` được giữ để tương thích model User, không quyết định quyền API. UUID là mã định danh, không thay thế phân quyền.

## Model dùng chung

`BaseAuditModel` có thông tin người tạo/người sửa và thời gian. `UUIDModel` kế thừa phần đó và thêm ID kiểu UUID.

Hai model này có `abstract = True`: không tạo bảng riêng. Khi SampleItem kế thừa UUIDModel, các trường được thêm vào bảng sample.

Các trường created_by/updated_by được gán trong service khi ghi qua API. Chúng không phải lịch sử chỉnh sửa đầy đủ. Base không cung cấp giao diện quản trị hoặc lịch sử audit đầy đủ.

## Transaction và khóa hàng

`@transaction.atomic` gom việc ghi thành một giao dịch: lỗi thì hoàn tác các thay đổi trong giao dịch.

`select_for_update()` khóa hàng trong khi sửa/xóa để hạn chế hai thao tác ghi chồng nhau. PostgreSQL hỗ trợ khóa này; SQLite local không có cùng mức bảo vệ cạnh tranh. Bạn có thể dùng sẵn cách làm trong sample service trước khi tìm hiểu sâu hơn.

## SOLID ở mức vừa đủ

Base ưu tiên **mỗi thành phần có một trách nhiệm rõ ràng**, các module ít phụ thuộc nhau và chỉ dùng kế thừa khi có ích. DRF cung cấp sẵn ModelViewSet, serializer và permission nên không viết lại một bộ framework khác bên trong dự án.

Chưa cần thêm interface cho mọi class, repository cho mọi model hoặc lớp BaseService. Khi dự án có nhu cầu tích hợp/mở rộng cụ thể, mới quyết định cần abstraction nào.

## Thứ tự đọc code được gợi ý

1. `apps/samples/models.py`.
2. `apps/samples/v1/serializers/samples.py`.
3. `apps/samples/v1/views/samples.py`.
4. `apps/samples/services.py`.
5. `apps/samples/v1/urls.py`.
6. `apps/samples/tests/test_api.py`.

Sau đó mới đọc `users` để hiểu đăng ký, password hashing và JWT.

## Hai API dùng chung: minimal và delete-many

`shared/mixins.py` chứa hai mixin nhỏ, không phải giao diện. Mỗi ViewSet có thể kế thừa chúng để thêm endpoint JSON:

- `MinimalMixin`: dùng cùng get_queryset để giữ phạm vi quyền; get_serializer_class chọn serializer rút gọn. Có phân trang, tìm kiếm và selected_ids.
- `BulkDeleteMixin`: validate danh sách UUID rồi gọi shared/services.py. Hàm check_delete_permission của từng module áp dụng đúng quy tắc như xóa đơn.

Users yêu cầu admin cho cả hai API. Samples giới hạn owner/admin. Với module mới, khai báo serializer minimal và kiểm tra quyền xóa trước khi dùng lại mixin.

Xóa nhiều bản ghi dùng QuerySet.delete trong một transaction, không gọi perform_destroy cho từng bản ghi. Nếu nghiệp vụ sau này có tác dụng phụ riêng khi xóa (ví dụ dọn file), cần triển khai thêm vào service xóa nhiều, không chỉ sửa service xóa đơn. Xóa user vẫn cascade dữ liệu sample của họ theo model.
