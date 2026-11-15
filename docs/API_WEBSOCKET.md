# Tài liệu API (REST) và WebSocket

Tài liệu đầy đủ, có thể thử trực tiếp: **Swagger UI** tại `/api/v1/docs/` (bấm *Authorize*, dán access token).
Tài liệu này là bản tóm tắt để tra cứu nhanh.

## Quy ước chung

- Tiền tố `/api/v1/`, JSON, xác thực bằng header `Authorization: Bearer <access_token>`.
- Phản hồi thành công: `{ "success": true, "message": "...", "data": ... }`.
- Phản hồi lỗi: `{ "success": false, "message": "...", "errors": {...}, "code": "MA_LOI" }` với mã HTTP đúng ngữ nghĩa (400, 401, 403, 404, 429).
- Danh sách dùng phân trang con trỏ: `data = { results: [...], next: "<url có ?cursor=>", previous }`.
- Refresh token nằm trong cookie `refresh_token` (HttpOnly, Secure, SameSite=Strict, Path=/api/v1/auth/). Frontend gọi API với `withCredentials: true`.
- Mã lỗi đáng chú ý: `EMAIL_NOT_VERIFIED`, `ACCOUNT_BANNED`, `LOGIN_LOCKED`, `OTP_INVALID`, `OTP_EXPIRED`, `OTP_LOCKED`, `OTP_COOLDOWN`, `REFRESH_REUSED`, `FILE_TOO_LARGE`, `FILE_TYPE_NOT_ALLOWED`, `DUPLICATE_REPORT`.

## Danh sách endpoint

### /api/v1/auth/

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| POST | `/api/v1/auth/register/` | UC-01: Đăng ký -> tạo user email_verified=False -> gửi OTP kích hoạt qua email. |
| POST | `/api/v1/auth/verify-email/` | UC-01: Nhập OTP -> kích hoạt tài khoản -> cấp ngay cặp token. |
| POST | `/api/v1/auth/otp/request/` | Gửi (lại) OTP cho: register / login / reset. Chống spam 60 giây/lần. |
| POST | `/api/v1/auth/login/` | UC-02: Đăng nhập bằng mật khẩu. Sai 5 lần -> khóa 15 phút (HTTP 429). |
| POST | `/api/v1/auth/login/otp/` | UC-03: Đăng nhập không mật khẩu bằng OTP gửi qua email. |
| POST | `/api/v1/auth/refresh/` | UC-04: Đọc refresh token từ HttpOnly Cookie -> xoay vòng -> cặp token mới. |
| POST | `/api/v1/auth/logout/` | UC-05: Thu hồi refresh token, đưa access token vào blacklist Redis, xóa cookie. |
| POST | `/api/v1/auth/password/forgot/` | UC-06: Yêu cầu OTP đặt lại mật khẩu. |
| POST | `/api/v1/auth/password/reset/` | UC-06: Nhập OTP + mật khẩu mới. Mọi phiên cũ bị thu hồi. |
| POST | `/api/v1/auth/password/change/` | UC-06: Đổi mật khẩu khi đang đăng nhập -> thu hồi phiên khác, cấp token mới cho phiên này. |
| GET | `/api/v1/auth/me/` |  |

### /api/v1/users/

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| GET,PATCH | `/api/v1/users/me/` | UC-07: xem / cập nhật hồ sơ của chính mình. |
| GET | `/api/v1/users/search/` | UC-08: tìm kiếm người dùng theo tên tiếng Việt có/không dấu. |
| GET | `/api/v1/users/suggestions/` |  |
| GET | `/api/v1/users/friends/` | Danh sách bạn bè của mình hoặc của người khác (?user_id=). |
| GET,POST | `/api/v1/users/friends/requests/` | UC-09: xem lời mời (direction=received/sent) / gửi lời mời kết bạn. |
| POST | `/api/v1/users/friends/requests/{friendship_id}/accept/` |  |
| POST | `/api/v1/users/friends/requests/{friendship_id}/decline/` |  |
| DELETE | `/api/v1/users/friends/requests/{friendship_id}/` |  |
| DELETE | `/api/v1/users/friends/{user_id}/` |  |
| GET,POST | `/api/v1/users/blocks/` | UC-10: danh sách chặn / chặn người dùng. |
| DELETE | `/api/v1/users/blocks/{user_id}/` |  |
| GET | `/api/v1/users/{user_id}/` | UC-07: xem trang cá nhân người khác (bị chặn thì coi như không tồn tại). |

### /api/v1/posts/

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| POST | `/api/v1/posts/` | UC-11: đăng bài (multipart: content, privacy, group_id, files[] <= 10 tệp, mỗi tệp <= 10MB). |
| GET | `/api/v1/posts/feed/` | UC-13: Bảng tin = bài của chính mình + bài PUBLIC/FRIENDS của bạn bè (loại người bị chặn), |
| GET | `/api/v1/posts/user/{user_id}/` | Dòng thời gian trang cá nhân. Trang đầu kèm danh sách bài đã ghim. |
| GET | `/api/v1/posts/user/{user_id}/shares/` |  |
| GET | `/api/v1/posts/group/{group_id}/` | UC-21: bài viết trong nhóm. |
| PATCH,DELETE | `/api/v1/posts/comments/{comment_id}/` |  |
| GET,PATCH,DELETE | `/api/v1/posts/{post_id}/` | UC-12: xem / sửa / xóa mềm bài viết. |
| POST | `/api/v1/posts/{post_id}/pin/` |  |
| GET,POST | `/api/v1/posts/{post_id}/like/` | UC-14: thích / bỏ thích (toggle, idempotent nhờ UNIQUE(post,user)). |
| GET,POST | `/api/v1/posts/{post_id}/comments/` | UC-15: cây bình luận / thêm bình luận hoặc trả lời (parent_id). |
| POST | `/api/v1/posts/{post_id}/share/` | UC-16: chia sẻ bài viết công khai lên trang cá nhân. |

### /api/v1/media/

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| POST | `/api/v1/media/upload/` | Tải 1 tệp (avatar / cover / chat). Trả về URL đích; ảnh sẵn sàng sau khi Celery nén xong (~1-2s). |

### /api/v1/groups/

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| GET,POST | `/api/v1/groups/` | UC-17: danh sách nhóm (?q=, ?mine=1) / tạo nhóm (người tạo là ADMIN). |
| GET,PATCH,DELETE | `/api/v1/groups/{group_id}/` |  |
| POST | `/api/v1/groups/{group_id}/join/` | UC-18: tham gia nhóm công khai ngay / gửi yêu cầu vào nhóm kín. |
| POST | `/api/v1/groups/{group_id}/leave/` |  |
| GET | `/api/v1/groups/{group_id}/members/` | ?status=ACCEPTED (mặc định) hoặc PENDING (chỉ ADMIN/MOD). |
| PATCH,DELETE | `/api/v1/groups/{group_id}/members/{member_id}/` | UC-20: đổi vai trò (PATCH, chỉ ADMIN) / mời ra khỏi nhóm (DELETE). |
| POST | `/api/v1/groups/{group_id}/members/{member_id}/approve/` | UC-19: duyệt yêu cầu tham gia. |
| POST | `/api/v1/groups/{group_id}/members/{member_id}/reject/` |  |

### /api/v1/chat/

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| GET | `/api/v1/chat/conversations/` |  |
| POST | `/api/v1/chat/conversations/direct/` | UC-22: mở (hoặc tạo) hội thoại 1-1 với bạn bè. |
| POST | `/api/v1/chat/conversations/group/` | UC-23: tạo nhóm chat từ danh sách bạn bè. |
| GET | `/api/v1/chat/conversations/{conversation_id}/` |  |
| POST | `/api/v1/chat/conversations/{conversation_id}/members/` |  |
| DELETE | `/api/v1/chat/conversations/{conversation_id}/members/{user_id}/` |  |
| GET,POST | `/api/v1/chat/conversations/{conversation_id}/messages/` | UC-24: lịch sử tin nhắn (cursor, mới nhất trước) / gửi tin nhắn qua REST (dự phòng khi mất WebSocket). |
| POST | `/api/v1/chat/conversations/{conversation_id}/read/` |  |
| GET | `/api/v1/chat/presence/` | Danh sách ID bạn bè đang online (chấm xanh). |
| GET | `/api/v1/chat/unread/` |  |

### /api/v1/notifications/

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| GET | `/api/v1/notifications/` | UC-26: danh sách thông báo (cursor) kèm số chưa đọc. |
| GET | `/api/v1/notifications/unread-count/` |  |
| POST | `/api/v1/notifications/read-all/` |  |
| POST | `/api/v1/notifications/{notification_id}/read/` |  |

### /api/v1/admin/

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| POST | `/api/v1/admin/reports/` | UC-27: người dùng báo cáo bài viết / bình luận / tài khoản. |
| GET | `/api/v1/admin/reports/reasons/` |  |
| GET | `/api/v1/admin/manage/reports/` | UC-28: danh sách báo cáo (?status=PENDING/RESOLVED/REJECTED&target_type=). |
| POST | `/api/v1/admin/manage/reports/{report_id}/resolve/` |  |
| GET | `/api/v1/admin/manage/users/` | UC-28: danh sách người dùng (?q=, ?status=active/banned/unverified). |
| POST | `/api/v1/admin/manage/users/{user_id}/ban/` |  |
| POST | `/api/v1/admin/manage/users/{user_id}/unban/` |  |
| GET | `/api/v1/admin/manage/dashboard/` | UC-28: thống kê DAU/MAU, người dùng & bài viết mới theo ngày, báo cáo chờ xử lý. |

Ngoài ra: `GET /api/health/` (200 nếu MySQL + Redis hoạt động, 503 nếu không).

## WebSocket

Một kết nối cho mỗi tab: `wss://<api-domain>/ws/chat/?token=<access_token>`
(dev: `ws://localhost/ws/chat/?token=...`). Token sai/hết hạn → server đóng kết nối với mã `4401`;
frontend refresh token rồi kết nối lại.

### Client → Server

| type | Trường | Ý nghĩa |
| --- | --- | --- |
| `message.send` | `conversation_id`, `content`, `file_url?`, `file_type?`, `client_id?` | Gửi tin nhắn (lưu MySQL rồi phát tới mọi thành viên) |
| `typing` | `conversation_id`, `is_typing` | Tín hiệu đang soạn tin (chỉ đi qua Redis, không ghi DB) |
| `read` | `conversation_id` | Đánh dấu đã xem (cập nhật `last_read_at`) |
| `ping` | | Giữ trạng thái online (gửi 25 giây/lần; TTL online 70 giây) |

### Server → Client (`{ "type": ..., "data": {...} }`)

| type | Khi nào |
| --- | --- |
| `message.new` | Có tin nhắn mới (kèm `client_id` để frontend thay tin nhắn tạm) |
| `message.read` | Thành viên khác đã xem |
| `typing` | Thành viên khác đang soạn tin |
| `presence` | Bạn bè vừa online / offline |
| `notification.new` | Thông báo mới (kèm `unread_count`) |
| `conversation.new` | Được thêm vào nhóm chat mới |
| `pong`, `error` | Phản hồi ping / lỗi nghiệp vụ |

Kiến trúc: mỗi kết nối tham gia group `user_<id>` trên Redis Channel Layer. Server gửi gói tin
tới từng thành viên qua group này nên một người mở nhiều tab vẫn nhận đủ.
