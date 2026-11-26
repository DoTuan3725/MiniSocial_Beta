# Gợi ý chuẩn bị vấn đáp (40% điểm)

Mỗi thành viên tự trả lời được các câu về phân hệ mình phụ trách, chỉ ra đúng file code.

| Câu hỏi thường gặp | Ý chính | Xem code |
| --- | --- | --- |
| Vì sao Modular Monolith mà không Microservices? | 100 CCU, 1 VPS, 5 người; microservices tốn chi phí mạng, giao dịch phân tán. Ranh giới module vẫn rõ (services.py + Event Bus, import-linter) nên tách được sau này. | `backend/.importlinter`, `common/events.py` |
| Làm sao bảo đảm module không dính nhau? | Chỉ gọi qua `services.py`; sự kiện qua `common/events.py`; CI chặn import model chéo và phụ thuộc vòng. | `.importlinter`, `.github/workflows/ci.yml` |
| Vì sao UUIDv7? | 48 bit đầu là timestamp → ghi nối tiếp B-Tree như số tự tăng; phần ngẫu nhiên → không đoán được ID (chống IDOR, không lộ quy mô). UUIDv4 làm phân mảnh index. | `common/models.py` |
| Bài viết được quản lý trong bảng thế nào? | `posts.author_id`, `group_id` (NULL nếu trang cá nhân), `privacy`; ảnh ở `post_media` (1-N); bộ đếm lưu sẵn; xóa mềm `deleted_at`; `is_flagged` khi vi phạm; `likes` UNIQUE(post,user). | `apps/posts/models.py` |
| Feed chạy thế nào? | Fan-out on Read, index (author, created_at), cursor pagination, cache ID trang đầu trên Redis, xóa cache khi bạn bè đăng bài. | `apps/posts/services.py` (`feed_queryset`) |
| Vì sao không lưu JWT trong LocalStorage? | XSS đọc được. Access token 15 phút trong RAM, refresh 7 ngày trong cookie HttpOnly + SameSite=Strict, có rotation và phát hiện tái sử dụng. | `apps/authentication/tokens.py`, `frontend/src/api/client.js` |
| OTP lưu ở đâu, chống dò thế nào? | Redis TTL 300s, chỉ lưu HMAC; sai 5 lần hủy mã; gửi lại sau 60s. | `apps/authentication/otp.py` |
| Realtime chat hoạt động ra sao? | Daphne ASGI + Channels; mỗi user một group `user_<id>` trên Redis Channel Layer; tin lưu MySQL rồi broadcast; typing chỉ qua RAM. | `apps/chat/consumers.py`, `services.py` |
| Thông báo được tạo ở đâu? | Phân hệ phát sự kiện (POST_LIKED...) sau khi commit; phân hệ Notification lắng nghe, tạo bản ghi, đẩy WebSocket. | `apps/notifications/listeners.py` |
| Upload ảnh an toàn thế nào? | Kiểm tra chữ ký byte thật (không tin đuôi file), Pillow verify, ≤ 10MB; Celery nén WebP; lưu R2 (0đ phí tải về). | `apps/media_files/services.py`, `tasks.py` |
| Chống XSS / SQLi / CSRF? | Bleach lọc HTML đầu vào + React escape đầu ra; ORM tham số hóa; cookie SameSite=Strict; Cloudflare WAF. | `common/text.py` |
| Rollback khi lỗi? | Image gắn tag theo commit trên GHCR; `rollback.sh <sha>` đổi IMAGE_TAG và khởi động lại < 30s. | `scripts/rollback.sh` |
