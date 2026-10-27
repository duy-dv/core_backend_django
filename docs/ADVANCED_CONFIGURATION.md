# Cấu hình nâng cao: Redis, Celery và WebSocket

Tài liệu dành cho lúc dự án cần mở rộng từ **base backend API** hiện tại. Các đoạn code dưới đây là hướng dẫn để bạn thêm vào dự án mới; chúng **chưa được bật sẵn trong base**. Không bổ sung template, Django Admin hoặc frontend.

Ví dụ dùng Python 3.12, Django 5.2, Celery 5.x và Channels 4.x. Có thể áp dụng từng phần: cần cache thì chỉ làm Redis; cần tác vụ nền thì thêm Celery; cần thời gian thực thì thêm Channels.

## 1. Vai trò của từng thành phần

| Thành phần | Dùng khi nào? | Không thay thế cho |
|---|---|---|
| Redis cache | Lưu kết quả tính toán ngắn hạn, cache dùng chung giữa các web process | Database lưu dữ liệu nghiệp vụ |
| Celery worker | Gửi email, xuất báo cáo, xử lý việc lâu ngoài HTTP request | Web server hoặc WebSocket server |
| Celery broker | Nơi xếp hàng task chờ worker xử lý; ví dụ dùng Redis | Nơi lưu kết quả nghiệp vụ lâu dài |
| Celery result backend | Lưu trạng thái/kết quả task khi cần tra cứu | Hệ thống audit, lịch sử giao dịch |
| Channels + ASGI | Duy trì kết nối WebSocket với client | Hàng đợi task nền |
| Redis channel layer | Chuyển sự kiện giữa các process WebSocket và worker | Hộp thư bảo đảm người dùng nhận được mọi sự kiện |

Luồng kết hợp ví dụ:

```text
Client --HTTP--> DRF API --> PostgreSQL
                     |
                     +--sau commit--> Celery broker --> Worker
                                                       |
                                                       +--> Redis channel layer
                                                                 |
Client <--WebSocket JSON-- Channels consumer <--------------------+
```

Thông báo WebSocket có thể mất khi client mất kết nối. Nếu cần đọc lại, lưu thông báo trong database và cung cấp API lấy danh sách.

## 2. Chuẩn bị thư viện và biến môi trường

Từ thư mục gốc, tạo file **requirements-advanced.txt**:

```text
-r requirements-production.txt
redis>=5.2,<7
celery[redis]>=5.5,<6
channels>=4.3,<5
channels-redis>=4.3,<5
uvicorn[standard]>=0.34,<1
websockets>=15,<16
```

Đây là giới hạn phiên bản tham khảo cho phần tích hợp, không phải bộ lock đã kiểm thử của base. Sau khi tích hợp và kiểm thử, chốt các phiên bản của môi trường triển khai.

Windows CMD:

```bat
cd /d D:\DEVs\django-base
call .venv\Scripts\activate.bat
python -m pip install -r requirements-advanced.txt
```

Ubuntu:

```bash
cd /duong-dan/den/django-base
source .venv/bin/activate
python -m pip install -r requirements-advanced.txt
```

Thêm vào **.env** khi ứng dụng chạy trực tiếp trên máy:

```dotenv
REDIS_CACHE_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
CHANNEL_REDIS_URL=redis://127.0.0.1:6379/3
WEBSOCKET_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Các số /0, /1, /2, /3 giúp tách nhóm dữ liệu trên Redis standalone. Chúng vẫn dùng chung tiến trình, RAM và tài nguyên; không phải ranh giới bảo mật. Khi tải lớn nên tách Redis cache khỏi broker/channel layer để chính sách xóa cache không ảnh hưởng hàng đợi.

Trong Docker, đổi hostname **127.0.0.1 thành redis**; ví dụ `redis://redis:6379/1`. Đừng dùng localhost trong container để truy cập container Redis khác.

## 3. Redis

### 3.1. Khởi động Redis local

Cách dễ dùng trên cả Windows CMD và Ubuntu có Docker:

```text
docker run -d --name django-base-redis -p 127.0.0.1:6379:6379 -v django-base-redis-data:/data redis:7-alpine redis-server --appendonly yes
docker exec django-base-redis redis-cli ping
```

Kết quả mong đợi: **PONG**. Lệnh docker run chỉ chạy lần đầu; những lần sau dùng `docker start django-base-redis`.

Ubuntu có thể dùng gói hệ điều hành thay vì Docker:

```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
redis-cli ping
```

Chọn một cách, tránh chạy hai Redis cùng port 6379. WSL không bật systemd có thể dùng Redis trong Docker.

### 3.2. Cấu hình Django cache

Thêm ở cuối **src/core/settings.py**:

```python
# Có URL thì dùng Redis; nếu chưa cấu hình, base vẫn chạy bằng cache trong bộ nhớ.
REDIS_CACHE_URL = os.getenv("REDIS_CACHE_URL", "")

if REDIS_CACHE_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_CACHE_URL,
            "KEY_PREFIX": "my-project",
            "TIMEOUT": 300,
            "OPTIONS": {
                "socket_connect_timeout": 3,
                "socket_timeout": 3,
            },
        }
    }
```

Đổi KEY_PREFIX theo dự án. Django có RedisCache sẵn; không cần thêm django-redis cho ví dụ này. [Tài liệu Django cache](https://docs.djangoproject.com/en/5.2/topics/cache/).

Kiểm tra từ thư mục gốc, dùng được trên CMD và Ubuntu:

```text
python src/manage.py shell -c "from django.core.cache import cache; cache.set('demo:ping', 'pong', timeout=30); print(cache.get('demo:ping'))"
```

Kết quả mong đợi: `pong`.

### 3.3. Dùng cache đúng phạm vi dữ liệu

Ví dụ trong service đã có `actor` được xác thực:

```python
from django.core.cache import cache

from apps.samples.models import SampleItem

# Ví dụ này chỉ đếm bản ghi thuộc actor, kể cả actor là admin.
key = f"samples:owned-count:{actor.pk}"
count = cache.get(key)
if count is None:
    count = SampleItem.objects.filter(owner=actor).count()
    cache.set(key, count, timeout=60)
```

Không dùng một key chung cho kết quả theo quyền của từng user. Khi thay đổi dữ liệu, có thể xóa key sau commit:

```python
from django.db import transaction
from django.core.cache import cache

transaction.on_commit(lambda: cache.delete(f"samples:owned-count:{actor.pk}"))
```

Ví dụ cache này chấp nhận dữ liệu cũ tối đa TTL, không dùng để quyết định số dư, quyền truy cập hoặc giao dịch cần chính xác tuyệt đối. Khi có race đọc/ghi hoặc bulk delete, cần thiết kế invalidation cho toàn bộ các owner bị ảnh hưởng.

Không gọi `cache.clear()` để “dọn nhanh” một Redis DB đang dùng chung. Khi Redis cache hỏng, DRF throttle dùng cache này cũng có thể lỗi; hãy theo dõi và chọn chính sách lỗi phù hợp.

## 4. Celery

### 4.1. Tạo ứng dụng Celery

Tạo **src/core/celery.py**:

```python
"""Khởi tạo Celery và tự tìm tasks.py trong các ứng dụng."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

Bổ sung vào **src/core/__init__.py**:

```python
"""Nạp Celery khi Django khởi động."""

from .celery import app as celery_app

__all__ = ("celery_app",)
```

Sau bước này, Celery trở thành dependency bắt buộc của dự án đã chọn tích hợp. Đây là thay đổi của dự án mở rộng, không phải yêu cầu của base gốc. [Hướng dẫn Celery với Django](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html).

### 4.2. Cấu hình trong settings.py

```python
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2")

# Chỉ trao đổi dữ liệu JSON; không truyền model instance hoặc HTTP request vào task.
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_EXPIRES = 3600
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_TASK_TIME_LIMIT = 300
```

Result backend chỉ cần khi ứng dụng muốn đọc trạng thái/kết quả task. Nếu không cần, dùng `ignore_result=True` cho task tương ứng.

### 4.3. Task mẫu

Tạo **src/apps/samples/tasks.py**:

```python
"""Task kiểm tra worker, không thay đổi dữ liệu nghiệp vụ."""

from celery import shared_task


@shared_task
def add_numbers(a, b):
    return a + b
```

Chạy worker trên Ubuntu hoặc terminal Ubuntu của WSL, sau khi activate **venv Linux riêng** và vào thư mục dự án:

```bash
cd src
python -m celery -A core worker --loglevel=INFO
```

Mở terminal thứ hai, activate cùng môi trường và đứng tại thư mục gốc:

```text
python src/manage.py shell -c "from apps.samples.tasks import add_numbers; task = add_numbers.delay(2, 3); print(task.id); print(task.get(timeout=15))"
```

Kết quả mong đợi: một task ID và số **5**. `get()` ở đây chỉ để thử trong terminal. Không chờ `get()` trong HTTP request; API nên trả task ID hoặc ID bản ghi công việc và cho client kiểm tra sau.

**Windows CMD:** Celery không hỗ trợ Windows native. Chạy worker bằng Docker theo mục 6 hoặc trong WSL. Không dùng `--pool=solo` làm cấu hình worker production và không dùng venv Windows trong Ubuntu/WSL. [FAQ chính thức của Celery](https://docs.celeryq.dev/en/stable/faq.html#does-celery-support-windows).

### 4.4. Gửi task sau khi database commit

Nếu API đang tạo bản ghi trong transaction, gửi task sau khi commit để worker không đọc trước khi dữ liệu tồn tại:

```python
from django.db import transaction

from apps.samples.tasks import add_numbers

with transaction.atomic():
    # Thực hiện các thao tác lưu dữ liệu tại đây.
    transaction.on_commit(lambda: add_numbers.delay(2, 3))
```

Với task nghiệp vụ, truyền ID hoặc chuỗi UUID rồi để task tự đọc database. Task có tác dụng phụ phải có tính idempotent: được chạy lại cũng không gây gửi hai lần, trừ tiền hai lần hoặc tạo bản ghi trùng.

`on_commit` không bảo đảm gửi thành công khi broker mất kết nối sau commit. Nếu nghiệp vụ không được phép mất công việc, cần transactional outbox và cơ chế gửi lại. Retry chỉ cho lỗi tạm thời có thể phục hồi; đặt giới hạn số lần và thời gian chờ.

### 4.5. Lịch định kỳ — tùy chọn

Ví dụ thêm vào settings.py:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "kiem-tra-moi-nam-phut": {
        "task": "apps.samples.tasks.add_numbers",
        "schedule": crontab(minute="*/5"),
        "args": (2, 3),
    },
}
```

Chạy trong terminal Linux riêng, từ `src`:

```bash
python -m celery -A core beat --loglevel=INFO
```

Beat chỉ gửi lịch, worker mới thực thi. Mỗi lịch chỉ chạy một Beat để tránh gửi trùng; không cần django-celery-beat hoặc Django Admin cho ví dụ này.

## 5. WebSocket bằng Django Channels

### 5.1. Phạm vi ví dụ xác thực

Base đang dùng **Bearer JWT**, không dùng session. Không thêm AuthMiddlewareStack của Channels vì cơ chế đó mặc định phục vụ session/cookie.

Ví dụ hoàn chỉnh dưới đây dùng `Authorization: Bearer ACCESS_TOKEN` trong handshake, phù hợp **Postman và client Python/server**. Thư viện WebSocket native của trình duyệt không cho đặt Authorization tùy ý. Nếu client là browser, đọc mục 5.8 trước khi chọn cơ chế xác thực.

WebSocket không tự áp dụng permission hoặc throttle của DRF. Ví dụ chỉ cho mỗi user nhận sự kiện trong nhóm riêng của họ; không cho client tự chọn user ID hoặc group.

### 5.2. Cấu hình Channels

Thêm `"channels"` vào INSTALLED_APPS của **src/core/settings.py**, rồi bổ sung:

```python
ASGI_APPLICATION = "core.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("CHANNEL_REDIS_URL", "redis://127.0.0.1:6379/3")],
            "prefix": "my-project-ws",
            "capacity": 100,
            "expiry": 60,
        },
    }
}

# Đây là origin của client, gồm scheme + host + port, không phải URL ws://.
WEBSOCKET_ALLOWED_ORIGINS = env_list(
    "WEBSOCKET_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
```

Dùng Redis channel layer khi có nhiều web process hoặc Celery worker gửi sự kiện; InMemoryChannelLayer không chia sẻ giữa các process. [Tài liệu channel layers](https://channels.readthedocs.io/en/stable/topics/channel_layers.html).

### 5.3. Middleware JWT riêng cho WebSocket

Tạo **src/apps/users/websocket_auth.py**:

```python
"""Xác thực JWT của handshake; không tạo session hoặc cookie."""

from channels.db import database_sync_to_async
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.exceptions import TokenError

from apps.users.authentication import ActiveJWTAuthentication


@database_sync_to_async
def authenticate_access_token(raw_token):
    # Tái sử dụng kiểm tra token, mật khẩu thay đổi và tài khoản bị khóa của base.
    auth = ActiveJWTAuthentication()
    token = auth.get_validated_token(raw_token)
    return auth.get_user(token), token


class JWTWebSocketMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        authorization = headers.get(b"authorization", b"")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != b"bearer":
            await send({"type": "websocket.close", "code": 4401})
            return

        try:
            user, token = await authenticate_access_token(parts[1])
        except (APIException, TokenError):
            await send({"type": "websocket.close", "code": 4401})
            return

        authenticated_scope = dict(scope)
        authenticated_scope["user"] = user
        authenticated_scope["access_token"] = parts[1]
        authenticated_scope["token_expires_at"] = token["exp"]
        await self.app(authenticated_scope, receive, send)
```

database_sync_to_async đưa truy vấn ORM đồng bộ ra khỏi event loop. Không gọi trực tiếp ORM đồng bộ trong consumer async. [Tài liệu xác thực Channels](https://channels.readthedocs.io/en/stable/topics/authentication.html), [tài liệu consumer](https://channels.readthedocs.io/en/stable/topics/consumers.html).

### 5.4. Consumer nhận thông báo riêng của user

Tạo **src/apps/samples/consumers.py**:

```python
"""Kênh thông báo JSON theo từng tài khoản, không render HTML."""

import asyncio
import time

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.exceptions import TokenError

from apps.users.websocket_auth import authenticate_access_token


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_name = f"user.{self.scope['user'].pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # Client phải lấy token mới qua HTTP và kết nối lại khi token hết hạn.
        self.expiry_task = asyncio.create_task(self.close_when_expired())

    async def close_when_expired(self):
        remaining = max(0, self.scope["token_expires_at"] - time.time())
        await asyncio.sleep(remaining)
        await self.close(code=4401)

    async def disconnect(self, close_code):
        task = getattr(self, "expiry_task", None)
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def still_authorized(self):
        # Kiểm tra lại trước mỗi lần trao đổi, để khóa/đổi mật khẩu có hiệu lực.
        try:
            await authenticate_access_token(self.scope["access_token"])
        except (APIException, TokenError):
            await self.close(code=4401)
            return False
        return True

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        # Ví dụ này chỉ có lệnh ping; không mở API nghiệp vụ ghi dữ liệu qua socket.
        if not await self.still_authorized():
            return
        if bytes_data is not None or text_data != "ping":
            await self.close(code=4400)
            return
        await self.send_json({"type": "pong"})

    async def notify(self, event):
        # group_send với type=notify sẽ gọi hàm này.
        if await self.still_authorized():
            await self.send_json({"type": "notification", "data": event["data"]})
```

Việc kiểm tra lại tài khoản tạo thêm query cho mỗi sự kiện; phù hợp ví dụ nhỏ. Khi tải cao, thiết kế cơ chế thu hồi kết nối và cache quyền rõ ràng, không bỏ kiểm tra mà không có phương án thay thế. Kết nối im lặng của tài khoản vừa khóa sẽ đóng khi token hết hạn; nếu có sự kiện đến trước đó thì bị từ chối trước khi gửi dữ liệu.

### 5.5. Routing và ASGI

Tạo **src/apps/samples/routing.py**:

```python
from django.urls import path

from apps.samples.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]
```

Thay nội dung **src/core/asgi.py**:

```python
"""Phân luồng HTTP và WebSocket trong cùng backend ASGI."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.asgi import get_asgi_application

# Khởi tạo Django trước khi import consumer/middleware có dùng model.
django_application = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import OriginValidator  # noqa: E402
from django.conf import settings  # noqa: E402

from apps.samples.routing import websocket_urlpatterns  # noqa: E402
from apps.users.websocket_auth import JWTWebSocketMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_application,
    "websocket": OriginValidator(
        JWTWebSocketMiddleware(URLRouter(websocket_urlpatterns)),
        settings.WEBSOCKET_ALLOWED_ORIGINS,
    ),
})
```

OriginValidator nằm ngoài JWT middleware để từ chối origin lạ trước khi xử lý tiếp. CORS_ALLOWED_ORIGINS không tự bảo vệ WebSocket. Origin là lớp kiểm tra bổ sung; client không phải browser có thể tự đặt header này, nên vẫn phải xác thực và phân quyền. [Bảo mật WebSocket của Channels](https://channels.readthedocs.io/en/stable/topics/security.html).

### 5.6. Chạy server ASGI

Từ thư mục gốc đã activate venv, dùng được trên CMD và Ubuntu:

```text
python -m uvicorn core.asgi:application --app-dir src --host 127.0.0.1 --port 8000 --reload --ws-max-size 65536
```

Không dùng runserver mặc định của base để thử WebSocket. Uvicorn cần hỗ trợ giao thức WebSocket; requirements-advanced dùng extra standard cho mục đích này. Khi chạy production bỏ --reload và dùng wss:// qua reverse proxy TLS.

### 5.7. Kiểm tra kết nối và gửi sự kiện

Đăng nhập qua HTTP như tài liệu API để lấy access token và ID của user.

Tạo tạm **ws_client.py** tại thư mục gốc:

```python
"""Client kiểm tra bằng Python; không phải mã frontend của base."""

from getpass import getpass

from websockets.sync.client import connect

token = getpass("Nhập access token: ")
with connect(
    "ws://127.0.0.1:8000/ws/notifications/",
    origin="http://localhost:3000",
    additional_headers={"Authorization": f"Bearer {token}"},
) as socket:
    socket.send("ping")
    print(socket.recv())  # Mong đợi {"type": "pong"}
    print("Đang chờ một thông báo...")
    print(socket.recv())
```

Chạy `python ws_client.py`. Trong terminal khác, từ thư mục gốc:

```text
python src/manage.py shell -c "from asgiref.sync import async_to_sync; from channels.layers import get_channel_layer; async_to_sync(get_channel_layer().group_send)('user.THAY_UUID_USER_DANG_KET_NOI', {'type': 'notify', 'data': {'message': 'Xin chao'}})"
```

Phải thay UUID bằng ID chính xác của tài khoản vừa đăng nhập. Nhóm được tính từ danh tính đã xác thực, không do client đăng ký tùy ý.

Nếu dùng Postman WebSocket, đặt header Authorization và Origin tương ứng trước khi connect. Từ chối trước khi accept thường hiện thành HTTP handshake 403; đừng chỉ chờ mã đóng 4401 ở client.

### 5.8. Khi frontend là trình duyệt

Không đưa access/refresh token dài hạn vào query string để lách giới hạn header của browser. URL dễ xuất hiện trong log. Ví dụ header ở trên cần được thay hoặc mở rộng trước khi dùng với WebSocket native trong trình duyệt.

Hai lựa chọn phù hợp với backend JWT:

1. **Ticket ngắn hạn, dùng một lần:** frontend gọi POST /api/v1/ws-ticket/ bằng Bearer JWT; backend tạo ticket ngẫu nhiên, lưu identity trong Redis khoảng 30 giây. Browser kết nối với ticket; middleware lấy và xóa ticket bằng thao tác nguyên tử (ví dụ Redis GETDEL), rồi kiểm tra lại tài khoản. Che ticket khỏi access log. Không dùng cache.get rồi cache.delete riêng lẻ vì có thể bị dùng lại đồng thời.
2. **Xác thực ở message đầu tiên:** cho kết nối nhưng chưa vào group hoặc nhận dữ liệu; yêu cầu access token trong khoảng 5 giây. Chỉ sau xác thực mới đăng ký group. Giới hạn số kết nối chưa xác thực và không ghi nội dung token vào log.

Đây là phương án thiết kế để bổ sung theo client thực tế, **chưa có endpoint ticket hoặc consumer xác thực message đầu tiên trong ví dụ**. Không thêm cookie/session chỉ để tái sử dụng AuthMiddlewareStack.

## 6. Chạy toàn bộ bằng Docker Compose

Phần này chỉ áp dụng **sau khi đã thêm các file/cấu hình ở trên**. Giữ docker-compose.yml của base; tạo thêm **docker-compose.advanced.yml**.

Trước hết sửa Dockerfile để cài dependency mới:

```dockerfile
# Thay hai dòng COPY/RUN cài requirements hiện tại bằng:
COPY requirements.txt requirements-production.txt requirements-advanced.txt ./
RUN pip install --no-cache-dir -r requirements-advanced.txt
```

Nội dung docker-compose.advanced.yml:

```yaml
# Chạy kèm file Compose gốc, không phải một stack độc lập.
x-app-environment: &app-environment
  DJANGO_SETTINGS_MODULE: core.settings
  POSTGRES_DB: ${POSTGRES_DB:-django_base}
  POSTGRES_USER: ${POSTGRES_USER:-django}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-local-dev-only}
  POSTGRES_HOST: postgres
  POSTGRES_PORT: 5432
  REDIS_CACHE_URL: redis://redis:6379/0
  CELERY_BROKER_URL: redis://redis:6379/1
  CELERY_RESULT_BACKEND: redis://redis:6379/2
  CHANNEL_REDIS_URL: redis://redis:6379/3

services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes: ["redis_advanced_data:/data"]
    ports: ["127.0.0.1:6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  web:
    environment: *app-environment
    command: sh -c "python manage.py migrate --noinput && uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --ws-max-size 65536"
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready/', timeout=3)"]
      interval: 5s
      timeout: 5s
      retries: 15

  worker:
    build: .
    env_file: .env
    environment: *app-environment
    command: celery -A core worker --loglevel=INFO
    depends_on:
      web:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  redis_advanced_data:
```

Nếu đang chạy container Redis độc lập ở mục 3, dừng nó trước để nhường port:

```text
docker stop django-base-redis
```

Các lệnh sau dùng được trên Windows CMD và Ubuntu:

```text
docker compose -f docker-compose.yml -f docker-compose.advanced.yml config
docker compose -f docker-compose.yml -f docker-compose.advanced.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.advanced.yml ps
docker compose -f docker-compose.yml -f docker-compose.advanced.yml logs --tail=100 worker
docker compose -f docker-compose.yml -f docker-compose.advanced.yml exec web python manage.py shell -c "from apps.samples.tasks import add_numbers; print(add_numbers.delay(2, 3).get(timeout=15))"
```

Web kế thừa build/ports/env_file và phụ thuộc PostgreSQL từ Compose gốc. Worker dùng chung database và các URL Redis, đợi web chạy xong migrate và khỏe mới khởi động. Cách migrate trong lệnh web chỉ dành cho stack local một web instance.

Beat tùy chọn chạy trong một terminal riêng:

```text
docker compose -f docker-compose.yml -f docker-compose.advanced.yml run --rm worker celery -A core beat --loglevel=INFO
```

Chỉ chạy một instance Beat. Khi vận hành dài hạn cần lưu trạng thái scheduler ngoài container tạm.

Dừng stack, giữ dữ liệu volume:

```text
docker compose -f docker-compose.yml -f docker-compose.advanced.yml down
```

## 7. Kết hợp task nền và thông báo WebSocket

Sau khi đã tích hợp Celery và Channels, thêm vào **src/apps/samples/tasks.py**:

```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


@shared_task(ignore_result=True)
def notify_user(user_id, message):
    # user_id phải được xác định/kiểm tra quyền từ nghiệp vụ ở backend.
    async_to_sync(get_channel_layer().group_send)(
        f"user.{user_id}",
        {"type": "notify", "data": {"message": message}},
    )
```

Gọi từ service sau khi lưu dữ liệu:

```python
from django.db import transaction

from apps.samples.tasks import notify_user

transaction.on_commit(
    lambda: notify_user.delay(str(actor.pk), "Dữ liệu đã được xử lý.")
)
```

Đây là thông báo tức thời, không phải xác nhận người dùng đã đọc hoặc chắc chắn nhận được. Nếu cần độ tin cậy, lưu notification/event trong PostgreSQL, có ID và trạng thái; WebSocket chỉ báo để client gọi API đồng bộ lại.

## 8. Production và lỗi thường gặp

### Triển khai

- Web chạy ASGI; worker và Beat là tiến trình riêng, cùng phiên bản code và cấu hình.
- Đặt DJANGO_SETTINGS_MODULE=core.production trong môi trường của cả web/worker/Beat. Với CMD dùng set, Ubuntu dùng export; cấu hình local Compose ở trên cố ý dùng core.settings.
- Redis chỉ ở mạng nội bộ; dùng ACL/password và TLS khi hạ tầng yêu cầu. Không commit URL chứa secret.
- Cache có thể chấp nhận eviction; broker cần chính sách bộ nhớ/persistence riêng. Tách instance khi cần tránh tranh chấp tài nguyên.
- PostgreSQL lưu dữ liệu nghiệp vụ; Redis channel layer không thay thế lịch sử sự kiện.
- Origin allowlist phải là địa chỉ frontend thật, ví dụ https://app.example.com; ALLOWED_HOSTS vẫn là host backend.
- Giới hạn kích thước message, số kết nối/user/IP và tốc độ gửi ở proxy/consumer. Throttle của DRF không áp dụng cho socket.
- Theo dõi queue length, task lỗi/chạy lâu, Redis memory, số kết nối socket và tỷ lệ reconnect.

Đoạn location minh họa khi Nginx đã có server TLS hợp lệ:

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}
```

Đây không phải cấu hình Nginx đầy đủ. Đảm bảo ping/heartbeat ngắn hơn idle timeout và có reconnect ở client. Chỉ bật TRUST_PROXY_SSL_HEADER khi upstream không bị truy cập trực tiếp từ mạng không tin cậy.

### Chẩn đoán

| Hiện tượng | Kiểm tra |
|---|---|
| Connection refused Redis | Redis đã chạy chưa? URL dùng localhost ở host hay redis trong container? |
| Task cứ PENDING | Worker có chạy? Đúng broker/task ID/result backend không? PENDING cũng có thể là ID không tồn tại |
| Received unregistered task | File tasks.py nằm trong app đã đăng ký chưa? Restart worker sau khi thêm task |
| Worker không thấy bản ghi vừa tạo | Gửi task bằng transaction.on_commit; đảm bảo worker cùng DB với web |
| SQLite database is locked | Nhiều tiến trình cùng ghi; chuyển PostgreSQL khi dùng worker thực tế |
| WebSocket handshake 403 | Kiểm tra Origin, header Bearer, token còn hạn và tài khoản hoạt động |
| WebSocket 404/không upgrade | Chạy đúng Uvicorn ASGI chưa? Routing /ws/ có đúng không? |
| Có socket nhưng không nhận sự kiện | Group user.ID và CHANNEL_REDIS_URL/prefix có giống ở web/worker không? |
| Browser không gửi được Authorization | Áp dụng ticket/message đầu tiên ở mục 5.8; không copy client header trực tiếp sang browser |
| Socket đóng 4401 | Token hết hạn/không hợp lệ hoặc tài khoản không còn được truy cập; login/refresh HTTP rồi nối lại |

## 9. Kiểm tra sau khi tích hợp

Thực hiện lần lượt:

1. Redis ping trả PONG; cache set/get trả pong.
2. Task add_numbers trả 5 qua worker thật, không chỉ eager mode.
3. HTTP login và CRUD cũ vẫn hoạt động; minimal/delete-many không bị ảnh hưởng.
4. Client có JWT hợp lệ và origin cho phép nhận pong qua WebSocket.
5. Thiếu/sai token, token hết hạn, tài khoản bị khóa hoặc origin lạ bị từ chối.
6. Hai user kết nối cùng lúc chỉ nhận thông báo của nhóm mình.
7. Khi tắt một web process hoặc reconnect, client có thể đồng bộ lại dữ liệu qua API.

Cấu hình test của base dùng cache bộ nhớ. Sau khi thêm Celery có thể bật CELERY_TASK_ALWAYS_EAGER=True trong test_settings cho unit test, nhưng cần test tích hợp riêng với broker thật. Test WebSocket có thể dùng WebsocketCommunicator của Channels và InMemoryChannelLayer trong một process; không dùng kết quả đó để khẳng định Redis/multi-process đã hoạt động.

**Phạm vi kiểm chứng của tài liệu:** các ví dụ được đối chiếu với cấu trúc base và tài liệu chính thức; không khẳng định Redis, worker, Channels hay cấu hình proxy đã được chạy end-to-end trong workspace này.
