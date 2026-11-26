# Quyết định thiết kế & xử lý mâu thuẫn giữa các tài liệu

Nguyên tắc chung: khi các tài liệu mâu thuẫn, lấy **`pipeline_du_an_v2`** (bản mới nhất, 05/11/2026) làm chuẩn.
Các điểm dưới đây là quyết định đã chốt với nhóm hoặc do không tài liệu nào quy định.

## Đã chốt với nhóm

| # | Vấn đề | Quyết định |
| --- | --- | --- |
| 1 | Luồng upload ảnh (Kịch bản 3 nói server nén, Bước 6 nói client upload thẳng qua Presigned URL) | **Server nhận file → kiểm tra MIME thật + ≤ 10MB → Celery nén WebP + thumbnail 150x150 → đẩy lên R2.** Bỏ Presigned URL. |
| 2 | Dịch vụ email OTP | **Resend.** Không có `RESEND_API_KEY` thì mã OTP in ra log của worker (dev). |
| 3 | Phạm vi | Backend + Frontend + DevOps + Tài liệu. |

## Do nhóm phát triển tự quyết (cần cả nhóm nắm để vấn đáp)

| # | Vấn đề | Quyết định | Lý do |
| --- | --- | --- | --- |
| 4 | 15 bảng (báo cáo) hay 16 bảng (pipeline) | 16 bảng, gồm `reports`. Bảng chat đổi tên `conv_members` → `conversation_members` cho khớp pipeline. | Pipeline là chuẩn |
| 5 | Chưa kích hoạt và bị khóa đều dùng `is_active=False` | Thêm cột `users.email_verified`; `is_active` chỉ dùng cho khóa tài khoản | Báo lỗi đăng nhập đúng nghĩa ("chưa kích hoạt" khác "bị khóa") |
| 6 | SimpleJWT kèm app `token_blacklist` tạo thêm 2 bảng | Dùng SimpleJWT để ký/kiểm tra token, còn whitelist refresh + blacklist access đặt trên **Redis** | Giữ đúng 16 bảng, đúng pipeline ("Token Blacklist" trên Redis) |
| 7 | Feed gồm bài nhóm? (SRS: có, báo cáo: chỉ bạn bè) | Feed = bài của mình + bài PUBLIC/FRIENDS của bạn bè. Bài nhóm xem ở trang nhóm. Chưa có bạn vẫn hiện bài của mình + gợi ý | Đúng quy tắc trong báo cáo, tránh feed rỗng khi mới đăng ký |
| 8 | Bài trong nhóm kín có phải duyệt từng bài? | Không. Chỉ duyệt thành viên; ADMIN/MOD xóa được bài vi phạm | Pipeline không yêu cầu, giảm độ phức tạp |
| 9 | Bộ lọc từ cấm đặt ở đâu | `common/badwords.py` (lớp dùng chung), danh sách `common/data/badwords_vi.txt`. Bài viết vi phạm bị **gắn cờ + ẩn** và phát sự kiện → phân hệ Admin tự tạo báo cáo. Bình luận vi phạm bị **che bằng \*\*\*** | Nếu đặt trong app Admin thì Post ↔ Admin phụ thuộc vòng |
| 10 | So khớp từ cấm có bỏ dấu không | **Không** bỏ dấu (bỏ dấu sẽ bắt nhầm "các", "lon"...). Liệt kê riêng các biến thể không dấu (dm, vcl...) | Tránh báo cáo sai |
| 11 | Tìm kiếm tiếng Việt | Cột `users.search_name` lưu tên không dấu (Unidecode) + **FULLTEXT INDEX với ngram parser** (token 2 ký tự) | FULLTEXT thường bỏ qua từ ngắn như "an", "ly" |
| 12 | Trạng thái online | Redis key có TTL 70s, làm mới bằng ping 25s (thay vì Set thuần) | Tự dọn trạng thái "online ma" khi server dừng đột ngột |
| 13 | Một hay nhiều WebSocket | Một kết nối `/ws/chat/` cho chat + thông báo + online | Ít kết nối, đơn giản cho frontend |
| 14 | Domain production | Frontend `yourdomain.vn` (Cloudflare Pages), API `api.yourdomain.vn` (VPS) | Pages không tự proxy `/api` sang VPS; cookie SameSite=Strict vẫn hoạt động vì cùng site |
| 15 | Redis đầy RAM | `maxmemory 512mb` + `volatile-lru` (pipeline ghi "LRU") | `allkeys-lru` có thể xóa nhầm hàng đợi Celery và OTP |
| 16 | Phụ thuộc giữa phân hệ | Phân tầng một chiều: admin → (posts, chat, notifications) → (groups, media) → users → auth. Kiểm tra bằng import-linter (10 contract) | Không phụ thuộc vòng (NFR-MNT-01) |
| 17 | `post_media` thuộc app nào | App `media_files` (đúng bảng 4.1 pipeline), khóa ngoại dạng chuỗi `'posts.Post'` | Không import model chéo |
| 18 | Lệnh rollback trong pipeline `docker compose pull backend:tag_on_dinh_cu` | Sai cú pháp → thay bằng biến `IMAGE_TAG` trong compose: `./scripts/rollback.sh <sha>` | Lệnh gốc không chạy được |
| 19 | Web Push (Service Worker) | Chưa làm; thông báo realtime qua WebSocket | Cần VAPID key, ưu tiên P3 |
| 20 | Migration | Tạo lại từ đầu → mỗi máy chạy `docker compose down -v` một lần | Schema thay đổi nhiều |

## Những điểm mã nguồn cũ đã sửa

- Feed hiển thị cả bài "Chỉ mình tôi" của bạn bè.
- Ai biết `conversation_id` cũng vào được phòng chat (không kiểm tra thành viên) → lỗ hổng IDOR.
- Refresh token cũ vẫn dùng lại được (không có rotation thật).
- Các app import chéo model của nhau.
- `makemigrations` chạy tự động mỗi lần khởi động container.
- Frontend chỉ có dữ liệu giả, chưa gọi API.
- Migration FULLTEXT bị lỗi trên MySQL thật (DDL trong transaction) → đã sửa, kiểm thử trên MySQL 8.0.
