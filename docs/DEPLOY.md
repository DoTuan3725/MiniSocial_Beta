# Hướng dẫn triển khai Production

Sơ đồ: Người dùng → Cloudflare (DNS proxy, SSL Full Strict, WAF) →
`yourdomain.vn` = Cloudflare Pages (React SPA) | `api.yourdomain.vn` = VPS (Nginx → Daphne/Celery/MySQL/Redis) |
`media.yourdomain.vn` = Cloudflare R2. Email qua Resend, lỗi qua Sentry → Discord.

## 1. Chuẩn bị tài khoản dịch vụ

| Dịch vụ | Việc cần làm | Lấy giá trị |
| --- | --- | --- |
| Tên miền | Trỏ nameserver về Cloudflare | |
| Cloudflare R2 | Tạo bucket `minisocial-media`; Settings > Custom domain `media.yourdomain.vn`; tạo API token quyền Object Read & Write | `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `MEDIA_PUBLIC_BASE_URL` |
| Cloudflare Pages | Tạo project (Direct Upload), gắn domain `yourdomain.vn` | `CF_PAGES_PROJECT`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` (quyền Pages Edit) |
| Resend | **Verify domain** (thêm bản ghi SPF/DKIM vào Cloudflare DNS), tạo API key | `RESEND_API_KEY`, `EMAIL_FROM=MiniSocial <no-reply@yourdomain.vn>` |
| Sentry | Tạo 2 project: Django và React; Settings > Integrations > Discord | `SENTRY_DSN`, `VITE_SENTRY_DSN` |
| Discord | Kênh `#deploy` > Integrations > Webhook | `DISCORD_WEBHOOK_URL` |

> **Lưu ý Resend:** chưa verify domain thì chỉ gửi được tới email chủ tài khoản Resend. Khi demo
> không có domain, để trống `RESEND_API_KEY` và xem mã OTP trong `docker compose logs worker`.

## 2. Cloudflare DNS & SSL

- Bản ghi A `api` → IP VPS (Proxy cam **bật**). CNAME `@`/`www` do Pages tự tạo. CNAME `media` do R2 tạo.
- SSL/TLS > Overview: **Full (strict)**. SSL/TLS > Origin Server > Create Certificate (15 năm) →
  lưu thành `/opt/minisocial/certs/origin.pem` và `origin.key` (quyền 600).
- Security > WAF: bật Managed Rules; Bot Fight Mode.

## 3. Chuẩn bị VPS (Ubuntu 22.04/24.04, Oracle Cloud ARM hoặc VPS thương mại)

```bash
# Docker + Compose plugin
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
# Mã nguồn
sudo mkdir -p /opt/minisocial && sudo chown $USER /opt/minisocial
git clone git@github.com:<org>/<repo>.git /opt/minisocial
cd /opt/minisocial
cp .env.prod.example .env && chmod 600 .env && nano .env      # điền giá trị thật
mkdir -p certs backups                                         # đặt chứng chỉ Origin CA vào certs/
sudo SSH_PORT=22 ./scripts/setup_ufw.sh                        # chỉ mở 80/443 cho Cloudflare + SSH
```

Sửa `server_name api.yourdomain.vn` trong `docker/nginx/prod.conf` cho đúng domain.

**UFW + Docker:** Docker tự thêm luật iptables cho cổng publish và có thể bỏ qua UFW. Chỉ Nginx
publish cổng 80/443, các container khác không publish nên vẫn an toàn. Nếu muốn chặn chặt hơn,
bật Cloudflare "Authenticated Origin Pulls" hoặc dùng `ufw-docker`.

Đăng nhập GHCR và chạy lần đầu:

```bash
echo <GHCR_READ_TOKEN> | docker login ghcr.io -u <github-user> --password-stdin
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
curl -s https://api.yourdomain.vn/api/health/
```

## 4. GitHub

**Settings > Branches:** bảo vệ `main` (bắt buộc PR, 1 approve, CI xanh), cấm push trực tiếp.

**Settings > Secrets and variables > Actions**

| Loại | Tên | Giá trị |
| --- | --- | --- |
| Secret | `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_SSH_PORT` | Thông tin SSH (khóa riêng, không dùng mật khẩu) |
| Secret | `GHCR_READ_TOKEN` | Personal Access Token quyền `read:packages` |
| Secret | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | Từ Cloudflare |
| Secret | `DISCORD_WEBHOOK_URL` | Webhook Discord |
| Variable | `CF_PAGES_PROJECT` | Tên project Pages |
| Variable | `VITE_API_URL` | `https://api.yourdomain.vn` |
| Variable | `VITE_WS_URL` | `wss://api.yourdomain.vn` |
| Variable | `VITE_SENTRY_DSN` | DSN Sentry của React |

## 5. Quy trình CI/CD

1. Tạo nhánh `feature/<module>-<việc>` từ `develop`, commit theo Conventional Commits.
2. Mở PR → **CI**: Lint → Architecture Guard (import-linter) → Test (pytest trên MySQL, coverage ≥ 80%; vitest; build).
3. Merge `develop` → `main` → **Deploy**: build image amd64+arm64 → GHCR (`:<sha>` và `:latest`) → Pages → SSH chạy `scripts/deploy.sh` (pull, up, migrate, health check) → báo Discord.

## 6. Vận hành hằng ngày

```bash
cd /opt/minisocial
docker compose -f docker-compose.prod.yml ps                     # trạng thái container
docker compose -f docker-compose.prod.yml logs -f backend worker # log
./scripts/rollback.sh <sha-cũ>                                   # quay lui < 30 giây (hoặc workflow "Rollback Production")
ls backups/                                                      # bản sao lưu MySQL lúc 02:00 hằng ngày
./scripts/restore_db.sh backups/social_db_YYYYMMDD_020000.sql.gz # khôi phục
./scripts/update_cloudflare_ips.sh && docker compose -f docker-compose.prod.yml restart nginx
```

Log container được xoay vòng tự động (json-file, tối đa 5 x 100MB mỗi container). Health check
`/api/health/` có thể gắn vào UptimeRobot / Better Stack (ping 60 giây) để cảnh báo khi 503.
