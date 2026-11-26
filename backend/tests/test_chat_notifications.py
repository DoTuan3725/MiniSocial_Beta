"""UC-22 -> UC-26: chat REST + WebSocket, presence, typing, đã xem, thông báo realtime."""

import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator

from apps.authentication.tokens import issue_tokens
from config.asgi import application

from .conftest import auth_client, befriend
from .factories import UserFactory

pytestmark = pytest.mark.django_db(transaction=True)


def test_direct_chat_requires_friendship(client_a, client_b, user, other):
    assert (
        client_a.post("/api/v1/chat/conversations/direct/", {"user_id": str(other.id)}, format="json").status_code
        == 403
    )
    befriend(user, other)
    r = client_a.post("/api/v1/chat/conversations/direct/", {"user_id": str(other.id)}, format="json")
    assert r.status_code == 201
    cid = r.data["data"]["id"]
    again = client_b.post("/api/v1/chat/conversations/direct/", {"user_id": str(user.id)}, format="json")
    assert again.status_code == 200 and again.data["data"]["id"] == cid

    client_a.post(f"/api/v1/chat/conversations/{cid}/messages/", {"content": "<b>Chào</b>"}, format="json")
    convs = client_b.get("/api/v1/chat/conversations/").data["data"]
    assert convs[0]["unread_count"] == 1 and convs[0]["last_message"]["content"] == "Chào"
    client_b.post(f"/api/v1/chat/conversations/{cid}/read/")
    assert client_b.get("/api/v1/chat/conversations/").data["data"][0]["unread_count"] == 0
    msgs = client_b.get(f"/api/v1/chat/conversations/{cid}/messages/").data["data"]["results"]
    assert len(msgs) == 1
    stranger = auth_client(UserFactory())
    assert stranger.get(f"/api/v1/chat/conversations/{cid}/messages/").status_code == 403


def test_group_chat_members(user, other):
    third = UserFactory()
    befriend(user, other)
    befriend(user, third)
    a = auth_client(user)
    r = a.post(
        "/api/v1/chat/conversations/group/",
        {"title": "Nhóm 1", "member_ids": [str(other.id), str(third.id)]},
        format="json",
    )
    assert r.status_code == 201
    cid = r.data["data"]["id"]
    assert len(r.data["data"]["members"]) == 3
    b = auth_client(other)
    assert b.delete(f"/api/v1/chat/conversations/{cid}/members/{third.id}/").status_code == 403
    assert a.delete(f"/api/v1/chat/conversations/{cid}/members/{third.id}/").status_code == 200
    assert b.delete(f"/api/v1/chat/conversations/{cid}/members/{other.id}/").status_code == 200


def test_websocket_message_typing_presence_and_notification(user, other):
    befriend(user, other)
    cid = (
        auth_client(user)
        .post("/api/v1/chat/conversations/direct/", {"user_id": str(other.id)}, format="json")
        .data["data"]["id"]
    )
    token_a, _ = issue_tokens(user)
    token_b, _ = issue_tokens(other)

    async def scenario():
        ws_b = WebsocketCommunicator(application, f"/ws/chat/?token={token_b}")
        assert (await ws_b.connect())[0]
        ws_a = WebsocketCommunicator(application, f"/ws/chat/?token={token_a}")
        assert (await ws_a.connect())[0]
        presence = await ws_b.receive_json_from(timeout=3)
        assert presence["type"] == "presence" and presence["data"]["is_online"]

        await ws_a.send_json_to({"type": "typing", "conversation_id": cid, "is_typing": True})
        typing = await ws_b.receive_json_from(timeout=3)
        assert typing["type"] == "typing" and typing["data"]["user_id"] == str(user.id)

        await ws_a.send_json_to(
            {"type": "message.send", "conversation_id": cid, "content": "xin chào", "client_id": "c1"}
        )
        got_b = await ws_b.receive_json_from(timeout=3)
        got_a = await ws_a.receive_json_from(timeout=3)
        assert got_b["type"] == "message.new" and got_b["data"]["content"] == "xin chào"
        assert got_a["data"]["client_id"] == "c1"

        await ws_a.send_json_to({"type": "ping"})
        assert (await ws_a.receive_json_from(timeout=3))["type"] == "pong"
        await ws_a.disconnect()
        offline = await ws_b.receive_json_from(timeout=3)
        assert offline["type"] == "presence" and offline["data"]["is_online"] is False
        await ws_b.disconnect()

    async_to_sync(scenario)()


def test_websocket_rejects_invalid_token():
    async def scenario():
        ws = WebsocketCommunicator(application, "/ws/chat/?token=abc")
        connected, code = await ws.connect()
        assert not connected

    async_to_sync(scenario)()


def test_notification_pushed_realtime(user, other):
    from asgiref.sync import sync_to_async

    token_a, _ = issue_tokens(user)
    sender = auth_client(other)

    async def scenario():
        ws = WebsocketCommunicator(application, f"/ws/?token={token_a}")
        assert (await ws.connect())[0]
        await sync_to_async(sender.post)("/api/v1/users/friends/requests/", {"user_id": str(user.id)}, format="json")
        msg = await ws.receive_json_from(timeout=3)
        await ws.disconnect()
        return msg

    msg = async_to_sync(scenario)()
    assert msg["type"] == "notification.new" and msg["data"]["verb"] == "FRIEND_REQUEST"
    assert msg["data"]["unread_count"] == 1


def test_notification_list_and_read(client_a, user, other):
    auth_client(other).post("/api/v1/users/friends/requests/", {"user_id": str(user.id)}, format="json")
    r = client_a.get("/api/v1/notifications/")
    assert r.data["data"]["unread_count"] == 1
    nid = r.data["data"]["results"][0]["id"]
    assert client_a.post(f"/api/v1/notifications/{nid}/read/").data["data"]["unread_count"] == 0
    sender = auth_client(other)
    sent = sender.get("/api/v1/users/friends/requests/?direction=sent").data["data"]
    sender.delete(f"/api/v1/users/friends/requests/{sent[0]['id']}/")
    assert client_a.post("/api/v1/notifications/read-all/").status_code == 200
    assert client_a.get("/api/v1/notifications/unread-count/").data["data"]["unread_count"] == 0
