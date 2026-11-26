# Bảng tra cứu chức năng từng tệp

> Mạng xã hội mini - Nhóm 1 · HP 608819. Đường dẫn tính từ thư mục `codebase/`, backend tính từ `backend/apps/<app>/`.


## Hạ tầng & DevOps

| Tệp | Chức năng |
| --- | --- |
| `docker-compose.yml` | Môi trường dev: nginx, backend (runserver/Daphne, tự migrate), worker (Celery + Beat), MySQL, Redis, MinIO + minio-init (tạo bucket public), frontend (Vite). |
| `docker-compose.prod.yml` | Production: nginx 80/443, backend (Daphne), worker, beat, MySQL (innodb 1G), Redis (512MB volatile-lru), db-backup (02:00). Image lấy từ GHCR theo IMAGE_TAG. |
| `.env.example / .env.prod.example` | Mẫu biến môi trường dev / production. |
| `docker/nginx/dev.conf` | Nginx dev: định tuyến /api, /ws (upgrade, timeout 86400s), SPA; rate limit đăng nhập 5 req/phút, API 30 req/s. |
| `docker/nginx/prod.conf` | Nginx prod: TLS Origin CA, HSTS, IP thật từ CF-Connecting-IP, log JSON, rate limit, giới hạn kết nối WebSocket. |
| `docker/nginx/cloudflare-realip.conf` | Dải IP Cloudflare được tin cậy cho real_ip. |
| `scripts/deploy.sh` | Pull image theo tag, khởi động lại backend/worker/beat, migrate, health check. |
| `scripts/rollback.sh, deploy_no_migrate.sh` | Quay lui về tag image cũ (< 30 giây, không cần revert Git). |
| `scripts/backup_loop.sh, restore_db.sh` | Sao lưu mysqldump nén gzip lúc 02:00, giữ N ngày / khôi phục. |
| `scripts/setup_ufw.sh, update_cloudflare_ips.sh` | Tường lửa chỉ mở 80/443 cho Cloudflare + SSH / cập nhật dải IP. |
| `.github/workflows/ci.yml` | CI: lint (flake8, black, isort, ESLint, Prettier) → import-linter → pytest trên MySQL (coverage ≥ 80%) + vitest + build. |
| `.github/workflows/deploy.yml` | CD khi merge main: build image amd64/arm64 → GHCR → Cloudflare Pages → SSH deploy → Discord. |
| `.github/workflows/rollback.yml` | Chạy tay: rollback về tag chỉ định. |
| `.pre-commit-config.yaml, .gitattributes, Makefile` | Hook trước commit, giữ LF cho script, lệnh tắt. |

## Backend - config/

| Tệp | Chức năng |
| --- | --- |
| `config/settings/base.py` | Cấu hình chung: 8 app, MySQL utf8mb4, Argon2, DRF + SimpleJWT, Redis (cache/broker/channel), CORS, R2/MinIO, Resend, log JSON, Sentry. |
| `config/settings/dev.py, prod.py, test.py` | Ghi đè theo môi trường (prod: cookie Secure, proxy SSL; test: fakeredis, channel layer RAM, Celery eager). |
| `config/asgi.py` | ProtocolTypeRouter: HTTP → Django, WebSocket → AllowedHostsOriginValidator + JWT middleware + routing chat. |
| `config/celery.py` | Khởi tạo Celery, lịch dọn tệp tạm mỗi giờ. |
| `config/urls.py` | Định tuyến /api/v1/<phân hệ>/, Swagger /api/v1/docs/, health /api/health/. |

## Backend - common/ (lớp nền tảng dùng chung)

| Tệp | Chức năng |
| --- | --- |
| `common/models.py` | BaseModel: khóa chính UUIDv7, created_at (index), updated_at. |
| `common/events.py` | Internal Event Bus: publish/subscribe, phát sau commit, danh mục tên sự kiện. |
| `common/responses.py, exceptions.py` | Phản hồi chuẩn {success, message, data/errors}; ServiceError → HTTP 4xx. |
| `common/pagination.py` | Cursor Pagination theo (created_at, id). |
| `common/redis_client.py` | Kết nối Redis dùng chung (test thay bằng fakeredis). |
| `common/realtime.py` | Đẩy sự kiện tới group WebSocket user_<id>. |
| `common/text.py` | Bleach lọc HTML, Unidecode bỏ dấu. |
| `common/badwords.py, data/badwords_vi.txt` | Bộ lọc từ thô tục tiếng Việt bằng Regex. |
| `common/stats.py, health.py, permissions.py, schema.py` | Đếm theo ngày, health check DB/Redis, quyền IsSystemAdmin, schema Swagger. |

## Backend - apps/authentication (UC-01→06)

| Tệp | Chức năng |
| --- | --- |
| `models.py` | Bảng users: email, full_name, search_name (FULLTEXT ngram), role, email_verified, is_active. |
| `otp.py` | OTP 6 số trên Redis: TTL 300s, lưu HMAC, sai 5 lần hủy, cooldown 60s. |
| `tokens.py` | Cấp/xoay vòng JWT, whitelist refresh trên Redis, phát hiện tái sử dụng, blacklist access. |
| `authentication.py` | Lớp xác thực DRF: SimpleJWT + kiểm tra blacklist/thu hồi. |
| `services.py` | Giao diện công khai: đăng ký, kích hoạt, đăng nhập mật khẩu/OTP, khóa brute-force, mật khẩu, tìm kiếm, khóa tài khoản, thống kê. |
| `emails.py, tasks.py` | Gửi email OTP qua Resend (Celery task, thử lại 3 lần). |
| `views.py, urls.py, serializers.py, validators.py` | API REST, đặt/xóa cookie refresh HttpOnly, kiểm tra mật khẩu mạnh. |
| `migrations/0002_fulltext_search_name.py` | Tạo FULLTEXT INDEX WITH PARSER ngram (chỉ MySQL). |

## Backend - apps/users (UC-07→10)

| Tệp | Chức năng |
| --- | --- |
| `models.py` | Bảng profiles, friendships (PENDING/ACCEPTED, UNIQUE + CHECK), blocks. |
| `services.py` | UserService: tóm tắt người dùng theo lô, hồ sơ, máy trạng thái kết bạn, chặn, gợi ý, ban/unban. |
| `listeners.py` | Tạo profile khi nhận sự kiện USER_REGISTERED. |
| `views.py, urls.py, serializers.py` | API hồ sơ, tìm kiếm, bạn bè, lời mời, chặn. |

## Backend - apps/posts (UC-11→16)

| Tệp | Chức năng |
| --- | --- |
| `models.py` | Bảng posts (composite index, xóa mềm, cờ vi phạm), comments (parent_id), likes (UNIQUE), shares. |
| `services.py` | PostService: quyền xem, đăng/sửa/xóa/ghim, feed + cache Redis, like, cây bình luận, chia sẻ, giao diện cho Admin. |
| `listeners.py` | Xóa cache feed khi có bài mới / đổi quan hệ bạn bè; xóa bài khi nhóm bị giải tán. |
| `views.py, urls.py` | API feed, bài viết, dòng thời gian, bài nhóm, like, bình luận, chia sẻ. |

## Backend - apps/media_files

| Tệp | Chức năng |
| --- | --- |
| `models.py` | Bảng post_media (PROCESSING/READY/FAILED), khóa ngoại chuỗi 'posts.Post'. |
| `services.py` | Kiểm tra chữ ký byte thật, ≤ 10MB, lưu tệp tạm, tạo bản ghi, đẩy task. |
| `tasks.py, processing.py` | Celery: Pillow nén WebP ≤ 1920px, thumbnail 150x150, đẩy lên R2/MinIO; dọn tệp tạm. |
| `storage.py` | S3Storage (boto3, R2/MinIO) và LocalStorage. |

## Backend - apps/groups (UC-17→21)

| Tệp | Chức năng |
| --- | --- |
| `models.py` | Bảng groups (search_name), group_members (role ADMIN/MOD/MEMBER, status PENDING/ACCEPTED/REJECTED). |
| `services.py` | GroupService: tạo/sửa/giải tán, tham gia/rời, duyệt, phân quyền, kick, quyền xem/đăng bài cho Post. |
| `views.py, urls.py` | API nhóm và thành viên. |

## Backend - apps/chat (UC-22→24)

| Tệp | Chức năng |
| --- | --- |
| `models.py` | Bảng conversations, conversation_members (last_read_at), messages (index conversation, created_at). |
| `consumers.py` | RealtimeConsumer: nhận message.send / typing / read / ping, đẩy sự kiện về client. |
| `middleware.py` | Xác thực JWT ở bước bắt tay WebSocket (?token=). |
| `presence.py` | Trạng thái online trên Redis (đếm kết nối + TTL 70s). |
| `services.py, views.py, urls.py, routing.py` | Hội thoại 1-1/nhóm, gửi tin, đã xem, typing, REST dự phòng, route /ws/chat/. |

## Backend - apps/notifications (UC-25→26)

| Tệp | Chức năng |
| --- | --- |
| `models.py` | Bảng notifications (đa hình entity_type + entity_id). |
| `listeners.py` | Lắng nghe 10 loại sự kiện và tạo thông báo tiếng Việt. |
| `services.py, views.py, urls.py` | Tạo + đẩy WebSocket (chống trùng), danh sách, đánh dấu đã đọc. |

## Backend - apps/admin_management (UC-27→28)

| Tệp | Chức năng |
| --- | --- |
| `models.py` | Bảng reports (đa hình POST/COMMENT/USER, báo cáo tự động, action_taken). |
| `services.py` | Gửi báo cáo, xử lý (gỡ nội dung, cảnh cáo, khóa), đóng báo cáo cùng đối tượng, dashboard. |
| `listeners.py` | Tạo báo cáo tự động khi bài/bình luận bị bộ lọc gắn cờ. |
| `management/commands/seed_demo.py` | Tạo dữ liệu demo. |

## Backend - kiểm thử

| Tệp | Chức năng |
| --- | --- |
| `tests/` | 53 test: auth, users, posts, groups, chat/WebSocket/notification, admin/media. |
| `load/locustfile.py` | Kịch bản tải 100 người dùng đồng thời. |
| `.importlinter` | 10 contract: phân tầng không vòng + cấm import models/views/serializers chéo. |

## Frontend - src/

| Tệp | Chức năng |
| --- | --- |
| `main.jsx, App.jsx` | Khởi tạo React Query, Router, Sentry ErrorBoundary; khôi phục phiên bằng refresh token khi F5; định tuyến bảo vệ. |
| `api/client.js` | Axios: gắn access token, tự refresh khi 401 (gom lời gọi đồng thời). |
| `api/endpoints.js` | Hàm gọi API theo phân hệ. |
| `store/auth.js, realtime.js, toast.js` | Zustand: token trong RAM, trạng thái online/typing/socket, thông báo nổi. |
| `hooks/useRealtimeConnection.js` | 1 kết nối WebSocket, tự kết nối lại, ping, cập nhật cache khi có tin nhắn/thông báo. |
| `hooks/useCursorList.js, useDebounced.js` | Phân trang con trỏ vô hạn, debounce tìm kiếm. |
| `components/AppShell.jsx` | Khung ứng dụng: thanh trên, điều hướng trái/dưới (mobile), người liên hệ online, huy hiệu chưa đọc. |
| `components/PostCard.jsx, PostComposer.jsx, CommentThread.jsx` | Thẻ bài viết (like, bình luận, chia sẻ, sửa, ghim, báo cáo), soạn bài kèm ảnh, cây bình luận. |
| `components/FriendButton.jsx, ReportDialog.jsx, ui.jsx` | Nút trạng thái kết bạn, hộp báo cáo, thành phần dùng chung (Avatar, RetryImage, Modal, Tabs...). |
| `pages/auth/*` | Đăng nhập (mật khẩu/OTP), đăng ký, kích hoạt OTP, quên mật khẩu. |
| `pages/*` | Bảng tin, trang cá nhân, bạn bè, tìm kiếm, nhóm, chi tiết nhóm, chat, thông báo, bài viết, cài đặt. |
| `pages/admin/AdminPage.jsx` | Thống kê (biểu đồ), xử lý báo cáo, quản lý người dùng. |
| `test/` | Vitest + Testing Library. |
