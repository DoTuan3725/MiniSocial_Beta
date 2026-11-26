"""UC-27, UC-28: báo cáo vi phạm, xử lý, khóa tài khoản, dashboard + upload media đơn lẻ."""

import pytest

from apps.posts.models import Post

from .conftest import auth_client, make_image
from .factories import UserFactory

pytestmark = pytest.mark.django_db


def _new_post(client, content="nội dung"):
    return client.post("/api/v1/posts/", {"content": content}, format="multipart").data["data"]["id"]


def test_report_and_delete_content(client_a, client_b, admin_user, user):
    pid = _new_post(client_a)
    assert (
        client_a.post(
            "/api/v1/admin/reports/", {"target_type": "POST", "target_id": pid, "reason": "SPAM"}, format="json"
        ).status_code
        == 400
    )
    r = client_b.post(
        "/api/v1/admin/reports/", {"target_type": "POST", "target_id": pid, "reason": "SPAM"}, format="json"
    )
    assert r.status_code == 201
    assert (
        client_b.post(
            "/api/v1/admin/reports/", {"target_type": "POST", "target_id": pid, "reason": "SPAM"}, format="json"
        ).data["code"]
        == "DUPLICATE_REPORT"
    )
    assert client_b.get("/api/v1/admin/manage/reports/").status_code == 403

    admin = auth_client(admin_user)
    reports = admin.get("/api/v1/admin/manage/reports/").data["data"]["results"]
    assert reports[0]["target"]["id"] == pid
    r = admin.post(
        f"/api/v1/admin/manage/reports/{reports[0]['id']}/resolve/",
        {"decision": "RESOLVED", "action": "DELETE_CONTENT"},
        format="json",
    )
    assert r.status_code == 200
    assert Post.objects.get(id=pid).deleted_at is not None
    from apps.notifications.models import Notification

    assert Notification.objects.filter(recipient=client_b.user, verb="REPORT_RESOLVED").exists()


def test_ban_user_via_report_revokes_session(client_a, client_b, admin_user, user):
    r = client_b.post(
        "/api/v1/admin/reports/",
        {"target_type": "USER", "target_id": str(user.id), "reason": "HARASSMENT"},
        format="json",
    )
    assert r.status_code == 201
    admin = auth_client(admin_user)
    rid = admin.get("/api/v1/admin/manage/reports/").data["data"]["results"][0]["id"]
    admin.post(
        f"/api/v1/admin/manage/reports/{rid}/resolve/", {"decision": "RESOLVED", "action": "BAN_USER"}, format="json"
    )
    user.refresh_from_db()
    assert not user.is_active
    assert client_a.get("/api/v1/auth/me/").status_code == 401
    assert admin.post(f"/api/v1/admin/manage/users/{user.id}/unban/").status_code == 200


def test_reject_auto_report_unflags_post(client_a, admin_user):
    pid = _new_post(client_a, "vcl thật")
    admin = auth_client(admin_user)
    rid = admin.get("/api/v1/admin/manage/reports/").data["data"]["results"][0]["id"]
    admin.post(f"/api/v1/admin/manage/reports/{rid}/resolve/", {"decision": "REJECTED"}, format="json")
    assert Post.objects.get(id=pid).is_flagged is False


def test_warn_user(client_a, client_b, admin_user, user):
    pid = _new_post(client_a)
    client_b.post("/api/v1/admin/reports/", {"target_type": "POST", "target_id": pid, "reason": "OTHER"}, format="json")
    admin = auth_client(admin_user)
    rid = admin.get("/api/v1/admin/manage/reports/").data["data"]["results"][0]["id"]
    admin.post(
        f"/api/v1/admin/manage/reports/{rid}/resolve/",
        {"decision": "RESOLVED", "action": "WARN_USER", "notes": "Lần đầu"},
        format="json",
    )
    from apps.notifications.models import Notification

    assert Notification.objects.filter(recipient=user, verb="SYSTEM").exists()


def test_admin_users_and_dashboard(admin_user, user):
    UserFactory(email_verified=False)
    admin = auth_client(admin_user)
    assert (
        admin.get("/api/v1/admin/manage/users/?status=unverified").data["data"]["results"][0]["email_verified"] is False
    )
    assert (
        admin.post(f"/api/v1/admin/manage/users/{user.id}/ban/", {"reason": "spam"}, format="json").status_code == 200
    )
    assert admin.post(f"/api/v1/admin/manage/users/{admin_user.id}/ban/").status_code == 400
    d = admin.get("/api/v1/admin/manage/dashboard/").data["data"]
    assert d["total_users"] == 3 and d["banned_users"] == 1
    assert len(d["posts_per_day"]) == 14 and sum(d["new_users_per_day"].values()) == 3
    assert admin.get("/api/v1/admin/reports/reasons/").status_code == 200


def test_single_upload_avatar(client_a, settings):
    r = client_a.post("/api/v1/media/upload/", {"file": make_image(), "purpose": "avatar"}, format="multipart")
    assert r.status_code == 201
    url = r.data["data"]["url"]
    assert url.startswith(settings.MEDIA_PUBLIC_BASE_URL) and url.endswith(".webp")
    assert client_a.patch("/api/v1/users/me/", {"avatar_url": url}, format="json").status_code == 200


def test_cleanup_temp(settings, tmp_path):
    import os
    import time

    from apps.media_files.tasks import cleanup_temp_uploads

    settings.TEMP_UPLOAD_DIR = tmp_path
    old = tmp_path / "old.png"
    old.write_bytes(b"x")
    os.utime(old, (time.time() - 7200, time.time() - 7200))
    (tmp_path / "new.png").write_bytes(b"x")
    assert cleanup_temp_uploads() == 1


def test_seed_demo_command():
    from django.core.management import call_command

    call_command("seed_demo")
    assert Post.objects.count() >= 5
