## Mô tả thay đổi
<!-- Làm gì, vì sao. Liên kết Use Case (UC-xx) / FR liên quan -->

## Loại thay đổi
- [ ] feat: tính năng mới
- [ ] fix: sửa lỗi
- [ ] refactor / test / docs / chore

## Kiểm tra trước khi xin review
- [ ] Đã chạy `pytest` và `lint-imports` ở máy local
- [ ] Không import models của phân hệ khác (chỉ gọi qua `services.py` hoặc Event Bus)
- [ ] Có migration nếu đổi model, đã cập nhật docs nếu đổi API
- [ ] Không commit `.env`, khóa bí mật

## Ảnh chụp / cách kiểm thử
