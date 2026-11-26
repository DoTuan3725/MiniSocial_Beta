# Danh mục 28 Use Case (UC-01 → UC-28)

Không tài liệu cũ nào liệt kê đủ 28 UC (SRS chỉ có 12). Bảng dưới được lập từ các mã FR trong SRS/Báo cáo,
chia đúng theo khung đánh số của `pipeline_du_an_v2`: AUTH 01–06, USER 07–10, POST 11–16, GROUP 17–21,
CHAT 22–24, NOTIFICATION 25–26, ADMIN 27–28. Phân hệ MEDIA không có UC riêng (phục vụ POST, USER, CHAT).

**Nhóm cần rà soát và chốt lại bảng này** trước khi đưa vào báo cáo.

| Mã | Tên Use Case | Tác nhân | Phân hệ | FR liên quan | API chính | Test |
| --- | --- | --- | --- | --- | --- | --- |
| UC-01 | Đăng ký tài khoản & kích hoạt bằng OTP email | Khách | auth | FR-AUTH-01, 02, 08 | `POST /auth/register/`, `POST /auth/verify-email/` | `test_auth::test_register_then_verify_issues_tokens` |
| UC-02 | Đăng nhập bằng mật khẩu (khóa 15 phút khi sai 5 lần) | Khách | auth | FR-AUTH-03, 09 | `POST /auth/login/` | `test_password_login_and_bruteforce_lock` |
| UC-03 | Đăng nhập không mật khẩu bằng OTP | Khách | auth | FR-AUTH-03 | `POST /auth/otp/request/`, `POST /auth/login/otp/` | `test_passwordless_otp_login` |
| UC-04 | Duy trì phiên: làm mới token (Token Rotation) | Người dùng | auth | FR-AUTH-04 | `POST /auth/refresh/` | `test_refresh_rotation_and_reuse_detection` |
| UC-05 | Đăng xuất | Người dùng | auth | FR-AUTH-05 | `POST /auth/logout/` | `test_logout_blacklists_access_token` |
| UC-06 | Quên mật khẩu / đổi mật khẩu | Khách, Người dùng | auth | FR-AUTH-06, 07 | `POST /auth/password/forgot/`, `/reset/`, `/change/` | `test_forgot_and_reset_password` |
| UC-07 | Xem & cập nhật hồ sơ (ảnh đại diện, ảnh bìa, tiểu sử) | Người dùng | user, media | FR-USER-01, 02 | `GET/PATCH /users/me/`, `GET /users/{id}/`, `POST /media/upload/` | `test_profile_view_and_update` |
| UC-08 | Tìm kiếm người dùng (có dấu / không dấu) | Người dùng | user | FR-USER-03 | `GET /users/search/?q=` | `test_search_without_diacritics` |
| UC-09 | Quản lý kết bạn: gửi, chấp nhận, từ chối, thu hồi, hủy kết bạn | Người dùng | user | FR-USER-04 → 07 | `/users/friends/...` | `test_friend_state_machine` |
| UC-10 | Chặn / bỏ chặn người dùng | Người dùng | user | FR-USER-08 | `POST /users/blocks/`, `DELETE /users/blocks/{id}/` | `test_block_removes_friendship_and_hides_profile` |
| UC-11 | Đăng bài viết (văn bản + tối đa 10 ảnh/video, quyền riêng tư) | Người dùng | post, media | FR-POST-01, 02, FR-MED-01 → 04 | `POST /posts/` | `test_create_post_with_images_processed_to_webp` |
| UC-12 | Sửa, xóa mềm, ghim bài viết | Người dùng | post | FR-POST-02 | `PATCH/DELETE /posts/{id}/`, `POST /posts/{id}/pin/` | `test_edit_delete_pin` |
| UC-13 | Xem bảng tin bạn bè (cursor, trống thì gợi ý kết bạn) | Người dùng | post | FR-POST-06 | `GET /posts/feed/` | `test_feed_rules`, `test_feed_cursor_pagination` |
| UC-14 | Thích / bỏ thích bài viết | Người dùng | post | FR-POST-03 | `POST /posts/{id}/like/` | `test_like_toggle_and_notification` |
| UC-15 | Bình luận đa cấp (thêm, trả lời, sửa, xóa) | Người dùng | post | FR-POST-04 | `/posts/{id}/comments/`, `/posts/comments/{id}/` | `test_comment_tree_and_delete_subtree` |
| UC-16 | Chia sẻ bài viết công khai lên trang cá nhân | Người dùng | post | FR-POST-07 | `POST /posts/{id}/share/` | `test_share_only_public` |
| UC-17 | Tạo, sửa, giải tán nhóm | Người dùng | group | FR-GRP-01, 06 | `POST /groups/`, `PATCH/DELETE /groups/{id}/` | `test_update_and_delete_group` |
| UC-18 | Tham gia / rời nhóm (công khai vào ngay, nhóm kín chờ duyệt) | Người dùng | group | FR-GRP-02, 06 | `POST /groups/{id}/join/`, `/leave/` | `test_public_group_flow` |
| UC-19 | Duyệt yêu cầu tham gia nhóm kín | Admin/Mod nhóm | group | FR-GRP-02 | `POST /groups/{id}/members/{mid}/approve/`, `/reject/` | `test_private_group_approval_and_visibility` |
| UC-20 | Phân quyền & xóa thành viên nhóm (ADMIN > MOD > MEMBER) | Admin nhóm | group | FR-GRP-03 | `PATCH/DELETE /groups/{id}/members/{mid}/` | `test_roles_and_kick` |
| UC-21 | Đăng & xem bài trong nhóm, kiểm duyệt bài nhóm | Thành viên nhóm | group, post | FR-GRP-04 | `POST /posts/` (group_id), `GET /posts/group/{id}/` | `test_public_group_flow` |
| UC-22 | Chat 1-1 realtime với bạn bè | Người dùng | chat | FR-CHAT-01, 03 | `POST /chat/conversations/direct/`, WebSocket `message.send` | `test_direct_chat_requires_friendship` |
| UC-23 | Chat nhóm (tạo, thêm, xóa thành viên, rời nhóm) | Người dùng | chat | FR-CHAT-02 | `POST /chat/conversations/group/`, `/members/` | `test_group_chat_members` |
| UC-24 | Trạng thái online, đang soạn tin, đã xem, lịch sử cursor | Người dùng | chat | FR-CHAT-04 → 07 | WebSocket `typing`, `read`, `presence`; `GET .../messages/` | `test_websocket_message_typing_presence_and_notification` |
| UC-25 | Nhận thông báo realtime | Người dùng, Hệ thống | notification | FR-NOTI-01 | Event Bus → WebSocket `notification.new` | `test_notification_pushed_realtime` |
| UC-26 | Xem danh sách thông báo, đánh dấu đã đọc | Người dùng | notification | FR-NOTI-02, 03 | `GET /notifications/`, `POST .../read/`, `/read-all/` | `test_notification_list_and_read` |
| UC-27 | Báo cáo vi phạm (thủ công + bộ lọc từ cấm tự động) | Người dùng, Hệ thống | admin | FR-POST-08 | `POST /admin/reports/` | `test_report_and_delete_content`, `test_badwords_flag_post_and_auto_report` |
| UC-28 | Quản trị: xử lý báo cáo, khóa/mở tài khoản, thống kê | Quản trị viên | admin | FR-ADM-01 → 04 | `/admin/manage/...` | `test_ban_user_via_report_revokes_session`, `test_admin_users_and_dashboard` |

## Đặc tả mẫu: UC-13 Xem bảng tin

| Mục | Nội dung |
| --- | --- |
| Tác nhân | Người dùng đã đăng nhập |
| Tiền điều kiện | Có access token hợp lệ |
| Luồng chính | 1. Frontend gọi `GET /api/v1/posts/feed/`. 2. Service lấy danh sách bạn bè (`friendships.status = ACCEPTED`), trừ người có quan hệ chặn. 3. Truy vấn `posts` của chính mình + bài `PUBLIC/FRIENDS` của bạn bè, không thuộc nhóm, chưa xóa mềm, không bị gắn cờ; sắp xếp `created_at DESC`, phân trang con trỏ 10 bài. 4. Trang đầu: danh sách ID được cache trong Redis (`feed:<uid>:first`, TTL 120s) và bị xóa khi bạn bè đăng bài mới / quan hệ bạn bè thay đổi. 5. Trả `{results, next, has_friends}`. |
| Luồng thay thế | `has_friends = false`: frontend hiện trạng thái trống kèm nút "Tìm bạn bè" và danh sách gợi ý (vẫn hiện bài của chính mình). Access token hết hạn (401): frontend tự gọi `/auth/refresh/` rồi gửi lại. |
| Hậu điều kiện | Không thay đổi dữ liệu |
