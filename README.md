# Mạng Xã Hội Mini (Mini Social Network) - Nhóm 1

> Đồ án Phát triển ứng dụng phía máy chủ nâng cao (HP 608819) · Khoa CNTT · Trường Đại học Xây dựng Hà Nội
> Kiến trúc **Modular Monolith (8 phân hệ)** · Django 5 + Daphne ASGI · React 18 (Vite) · MySQL 8 · Redis 7 · Celery · Docker Compose · Cloudflare Pages/R2 · Resend · Sentry

## Chạy toàn bộ hệ thống bằng 1 lệnh (NFR-PRT-01)

Yêu cầu: Docker Desktop (Windows/macOS) hoặc Docker Engine + Compose v2 (Linux).

```bash
cp .env.example .env                 # Windows: chạy run_docker.bat
docker compose up -d --build
docker compose exec backend python manage.py seed_demo   # dữ liệu mẫu (chạy 1 lần)
```

| Địa chỉ | Nội dung |
| --- | --- |
| http://localhost | Ứng dụng web |
| http://localhost/api/v1/docs/ | Swagger UI (bấm *Authorize*, dán access token) |
| http://localhost/django-admin/ | Django admin |
| http://localhost:9001 | MinIO console (minioadmin / minioadmin123) |
| localhost:3306 | MySQL cho DBeaver/TablePlus (social_user / social_pass123) |

Tài khoản demo: `admin@minisocial.local` / `Admin@123` và `linh@`, `son@`, `ha@`, `duc@`, `mai@`, `khoa@minisocial.local` / `Demo@123`.

**Mã OTP khi chạy local:** để trống `RESEND_API_KEY` thì mã được in ra log: `docker compose logs -f worker`.

Nếu từng chạy bản cũ: `docker compose down -v` để xóa CSDL cũ (migration đã được tạo lại).

## Cấu trúc thư mục

```text
codebase/
├── backend/                      Django 5 + Daphne ASGI + Celery
│   ├── config/                   settings (base/dev/prod/test), asgi, celery, urls
│   ├── common/                   BaseModel UUIDv7, Event Bus, phản hồi chuẩn, cursor pagination,
│   │                             Redis, Bleach, bộ lọc từ cấm, health check
│   ├── apps/
│   │   ├── authentication/       UC-01→06  JWT (SimpleJWT + Redis), OTP, Argon2id, Resend
│   │   ├── users/                UC-07→10  Hồ sơ, máy trạng thái kết bạn, chặn, tìm kiếm FTS
│   │   ├── posts/                UC-11→16  Bài viết, feed + cache, like, bình luận cây, chia sẻ
│   │   ├── media_files/          Pillow WebP, thumbnail, R2/MinIO (bảng post_media)
│   │   ├── groups/               UC-17→21  Nhóm công khai/kín, RBAC ADMIN/MOD/MEMBER
│   │   ├── chat/                 UC-22→24  WebSocket, chat 1-1/nhóm, presence, typing, đã xem
│   │   ├── notifications/        UC-25→26  Lắng nghe Event Bus, đẩy WebSocket
│   │   └── admin_management/     UC-27→28  Báo cáo đa hình, kiểm duyệt, khóa tài khoản, thống kê
│   ├── tests/                    53 test pytest (coverage 91%)
│   ├── load/locustfile.py        Kiểm thử tải 100 CCU
│   └── .importlinter             Bảo vệ ranh giới Modular Monolith
├── frontend/                     React 18 + Vite + Tailwind + TanStack Query + Zustand
│   └── src/{api,components,hooks,lib,pages,store,test}
├── docker/nginx/                 dev.conf, prod.conf, cloudflare-realip.conf
├── scripts/                      deploy, rollback, backup/restore, UFW, cập nhật IP Cloudflare
├── docs/                         USE_CASES, API_WEBSOCKET, DEPLOY, DECISIONS, VAN_DAP
├── .github/workflows/            ci.yml, deploy.yml, rollback.yml
├── docker-compose.yml            Môi trường dev (nginx, backend, worker, db, redis, minio, frontend)
└── docker-compose.prod.yml       Production (nginx, backend, worker, beat, db, redis, db-backup)
```

## Phát triển không dùng Docker

```bash
# Backend (cần MySQL + Redis; hoặc dùng SQLite để thử nhanh)
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
export DB_ENGINE=sqlite REDIS_URL=redis://localhost:6379/0 STORAGE_BACKEND=local CELERY_TASK_ALWAYS_EAGER=True MEDIA_PUBLIC_BASE_URL=http://localhost:8000/media
python manage.py migrate && python manage.py seed_demo
python manage.py runserver                 # Daphne ASGI, cổng 8000

# Frontend
cd frontend && npm install && npm run dev  # http://localhost:5173 (proxy /api, /ws -> :8000)
```

## Kiểm thử & chất lượng

```bash
cd backend
pytest --cov                     # SQLite: DB_ENGINE=sqlite pytest --cov
flake8 && black --check . && isort --check-only .
lint-imports                     # 10 contract kiến trúc
cd ../frontend && npm run lint && npm test && npm run build
```

## Tài liệu

- [docs/USE_CASES.md](docs/USE_CASES.md) - 28 Use Case, ánh xạ FR, API và test
- [docs/API_WEBSOCKET.md](docs/API_WEBSOCKET.md) - Danh sách endpoint, giao thức WebSocket
- [docs/DECISIONS.md](docs/DECISIONS.md) - Các quyết định thiết kế, xử lý mâu thuẫn tài liệu
- [docs/DEPLOY.md](docs/DEPLOY.md) - Triển khai VPS, Cloudflare, R2, Resend, Sentry, GitHub Actions
- [docs/VAN_DAP.md](docs/VAN_DAP.md) - Gợi ý chuẩn bị vấn đáp
- [NOTE_CHUC_NANG_FILE.md](NOTE_CHUC_NANG_FILE.md) - Chức năng từng tệp
