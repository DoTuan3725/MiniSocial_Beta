"""UC-17 -> UC-21: nhóm công khai/kín, duyệt, phân quyền, kick, bài viết trong nhóm."""

import pytest

from .conftest import auth_client
from .factories import UserFactory

pytestmark = pytest.mark.django_db


def test_public_group_flow(client_a, client_b):
    g = client_a.post("/api/v1/groups/", {"name": "CLB Cờ", "privacy": "PUBLIC"}, format="json").data["data"]
    assert g["my_membership"]["role"] == "ADMIN"
    r = client_b.post(f"/api/v1/groups/{g['id']}/join/")
    assert r.data["data"]["status"] == "ACCEPTED"
    r = client_b.post("/api/v1/posts/", {"content": "chào nhóm", "group_id": g["id"]}, format="multipart")
    assert r.status_code == 201 and r.data["data"]["group"]["name"] == "CLB Cờ"
    assert len(client_a.get(f"/api/v1/posts/group/{g['id']}/").data["data"]["results"]) == 1
    # bài nhóm không xuất hiện trong feed cá nhân
    assert client_b.get("/api/v1/posts/feed/").data["data"]["results"] == []
    assert client_b.post(f"/api/v1/groups/{g['id']}/leave/").status_code == 200
    assert client_a.post(f"/api/v1/groups/{g['id']}/leave/").status_code == 400  # admin duy nhất


def test_private_group_approval_and_visibility(client_a, client_b, other):
    from apps.notifications.models import Notification

    g = client_a.post("/api/v1/groups/", {"name": "Nhóm kín", "privacy": "PRIVATE"}, format="json").data["data"]
    client_a.post("/api/v1/posts/", {"content": "bí mật", "group_id": g["id"]}, format="multipart")
    assert client_b.get(f"/api/v1/posts/group/{g['id']}/").status_code == 403
    assert client_b.post(f"/api/v1/groups/{g['id']}/join/").data["data"]["status"] == "PENDING"
    assert client_b.post("/api/v1/posts/", {"content": "x", "group_id": g["id"]}, format="multipart").status_code == 403
    pending = client_a.get(f"/api/v1/groups/{g['id']}/members/?status=PENDING").data["data"]
    assert client_b.get(f"/api/v1/groups/{g['id']}/members/?status=PENDING").status_code == 403
    assert client_a.post(f"/api/v1/groups/{g['id']}/members/{pending[0]['id']}/approve/").status_code == 200
    assert Notification.objects.filter(recipient=other, verb="GROUP_JOIN_APPROVED").exists()
    assert len(client_b.get(f"/api/v1/posts/group/{g['id']}/").data["data"]["results"]) == 1


def test_roles_and_kick(user):
    owner, mod, member = auth_client(user), auth_client(UserFactory()), auth_client(UserFactory())
    gid = owner.post("/api/v1/groups/", {"name": "G"}, format="json").data["data"]["id"]
    mod.post(f"/api/v1/groups/{gid}/join/")
    member.post(f"/api/v1/groups/{gid}/join/")
    members = {m["user"]["id"]: m["id"] for m in owner.get(f"/api/v1/groups/{gid}/members/").data["data"]}
    mod_mid, member_mid = members[str(mod.user.id)], members[str(member.user.id)]
    assert member.patch(f"/api/v1/groups/{gid}/members/{mod_mid}/", {"role": "MOD"}, format="json").status_code == 403
    assert owner.patch(f"/api/v1/groups/{gid}/members/{mod_mid}/", {"role": "MOD"}, format="json").status_code == 200
    # MOD xóa được bài của thành viên và kick thành viên, nhưng không kick được ADMIN
    pid = member.post("/api/v1/posts/", {"content": "spam", "group_id": gid}, format="multipart").data["data"]["id"]
    assert mod.delete(f"/api/v1/posts/{pid}/").status_code == 200
    owner_mid = members[str(user.id)]
    assert mod.delete(f"/api/v1/groups/{gid}/members/{owner_mid}/").status_code == 403
    assert mod.delete(f"/api/v1/groups/{gid}/members/{member_mid}/").status_code == 200


def test_update_and_delete_group(client_a, client_b):
    g = client_a.post("/api/v1/groups/", {"name": "Cũ"}, format="json").data["data"]
    assert client_b.patch(f"/api/v1/groups/{g['id']}/", {"name": "Mới"}, format="json").status_code == 403
    assert client_a.patch(f"/api/v1/groups/{g['id']}/", {"name": "Mới"}, format="json").data["data"]["name"] == "Mới"
    pid = client_a.post("/api/v1/posts/", {"content": "x", "group_id": g["id"]}, format="multipart").data["data"]["id"]
    assert client_a.get("/api/v1/groups/?q=moi").data["data"][0]["id"] == g["id"]
    assert client_a.delete(f"/api/v1/groups/{g['id']}/").status_code == 200
    from apps.posts.models import Post

    assert Post.objects.get(id=pid).deleted_at is not None
