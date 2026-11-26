"""
Tạo dữ liệu mẫu để demo / bảo vệ đồ án:
    python manage.py seed_demo
Tài khoản: admin@minisocial.local / Admin@123 và 6 người dùng *@minisocial.local / Demo@123
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.chat import services as chat_services
from apps.groups import services as group_services
from apps.posts import services as post_services
from apps.users import services as user_services

DEMO_USERS = [
    ("linh", "Nguyễn Tuấn Linh"),
    ("son", "Lê Văn Sơn"),
    ("ha", "Trần Thu Hà"),
    ("duc", "Phạm Minh Đức"),
    ("mai", "Đỗ Ngọc Mai"),
    ("khoa", "Vũ Đăng Khoa"),
]

POSTS = [
    "Chào cả nhóm! Tuần này mình hoàn thành phần phân trang con trỏ cho bảng tin.",
    "Ai có tài liệu ôn Kết cấu thép thì chia sẻ mình với nhé.",
    "Chiều nay đá bóng sân trường lúc 17h, ai tham gia thả tim nhé ⚽",
    "Vừa deploy bản mới lên VPS, CI/CD chạy xanh hết 🎉",
]


class Command(BaseCommand):
    help = "Tạo dữ liệu demo (admin, người dùng, bạn bè, bài viết, nhóm, chat)"

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(email="admin@minisocial.local").exists():
            User.objects.create_superuser("admin@minisocial.local", "Admin@123", full_name="Quản trị viên")
        users = []
        for slug, name in DEMO_USERS:
            u = User.objects.filter(email=f"{slug}@minisocial.local").first()
            if not u:
                u = User.objects.create_user(
                    f"{slug}@minisocial.local", "Demo@123", full_name=name, email_verified=True
                )
            user_services.get_profile(u)
            users.append(u)
        a, b, c, d, e, f = users
        for x, y in [(a, b), (a, c), (b, c), (a, d), (c, e)]:
            if not user_services.are_friends(x.id, y.id):
                fr = user_services.send_friend_request(x, y.id)
                if fr.status != "ACCEPTED":
                    user_services.accept_friend_request(y, fr.id)
        if not user_services.relationship(f.id, a.id)["status"] == "PENDING_SENT":
            try:
                user_services.send_friend_request(f, a.id)
            except Exception:  # noqa: BLE001
                pass
        for author, text in zip([a, b, c, d], POSTS):
            post_services.create_post(author, content=text, privacy="PUBLIC")
        group = group_services.create_group(
            a, "CLB Lập trình HUCE", "Nơi trao đổi về lập trình, đồ án và cơ hội thực tập.", "PUBLIC"
        )
        group_services.join_group(b, group.id)
        private = group_services.create_group(c, "Nhóm đồ án 608819", "Nhóm kín của Nhóm 1.", "PRIVATE")
        group_services.join_group(e, private.id)
        post_services.create_post(a, content="Chào mừng các bạn đến với CLB!", group_id=group.id)
        conv, _ = chat_services.get_or_create_direct(a, b.id)
        chat_services.send_message(a, conv.id, "Ê Sơn, tối nay họp nhóm lúc 8h nhé")
        chat_services.send_message(b, conv.id, "Ok, mình chuẩn bị slide phần Chat rồi")
        self.stdout.write(
            self.style.SUCCESS(
                "Đã tạo dữ liệu demo. Admin: admin@minisocial.local / Admin@123 ; "
                "User: linh@minisocial.local / Demo@123"
            )
        )
