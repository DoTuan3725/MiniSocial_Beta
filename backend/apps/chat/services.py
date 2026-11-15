"""CHAT SERVICE: hội thoại 1-1 / nhóm, tin nhắn, đã xem, typing, presence."""

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.users import services as user_services
from common.exceptions import NotFound, PermissionDenied, ServiceError
from common.realtime import push_to_users
from common.text import sanitize_text

from . import presence
from .models import Conversation, ConversationMember, Message


def member_ids(conversation_id):
    return [
        str(i)
        for i in ConversationMember.objects.filter(conversation_id=conversation_id).values_list("user_id", flat=True)
    ]


def assert_member(user, conversation_id):
    m = (
        ConversationMember.objects.filter(conversation_id=conversation_id, user=user)
        .select_related("conversation")
        .first()
    )
    if not m:
        raise PermissionDenied("Bạn không thuộc cuộc trò chuyện này")
    return m


def conversation_payload(conv, user):
    members = list(ConversationMember.objects.filter(conversation=conv))
    summaries = user_services.get_user_summaries([m.user_id for m in members])
    online = presence.online_ids([m.user_id for m in members])
    me = next((m for m in members if str(m.user_id) == str(user.id)), None)
    last = Message.objects.filter(conversation=conv).order_by("-created_at").first()
    unread_q = Message.objects.filter(conversation=conv).exclude(sender=user)
    if me and me.last_read_at:
        unread_q = unread_q.filter(created_at__gt=me.last_read_at)
    others = [m for m in members if str(m.user_id) != str(user.id)]
    return {
        "id": str(conv.id),
        "type": conv.type,
        "title": conv.title
        or ", ".join(summaries[str(m.user_id)]["full_name"] for m in others if str(m.user_id) in summaries),
        "members": [
            {
                **summaries.get(str(m.user_id), {"id": str(m.user_id)}),
                "role": m.role,
                "last_read_at": m.last_read_at.isoformat() if m.last_read_at else None,
                "is_online": str(m.user_id) in online,
            }
            for m in members
        ],
        "my_role": me.role if me else None,
        "last_message": message_payload(last) if last else None,
        "unread_count": unread_q.count(),
        "last_message_at": (conv.last_message_at or conv.created_at).isoformat(),
    }


def message_payload(msg, client_id=None):
    data = {
        "id": str(msg.id),
        "conversation_id": str(msg.conversation_id),
        "sender_id": str(msg.sender_id),
        "content": msg.content,
        "file_url": msg.file_url,
        "file_type": msg.file_type,
        "created_at": msg.created_at.isoformat(),
    }
    if client_id:
        data["client_id"] = client_id
    return data


def list_conversations(user, limit=50):
    ids = ConversationMember.objects.filter(user=user).values_list("conversation_id", flat=True)
    convs = Conversation.objects.filter(id__in=list(ids)).order_by("-last_message_at", "-created_at")[:limit]
    return [conversation_payload(c, user) for c in convs]


# ------------------------------------------------------------------ UC-22: Chat 1-1
@transaction.atomic
def get_or_create_direct(user, target_id):
    target = user_services.get_active_user_or_404(target_id)
    if str(target.id) == str(user.id):
        raise ServiceError("Không thể nhắn tin cho chính mình")
    if user_services.is_blocked(user.id, target.id):
        raise PermissionDenied("Không thể nhắn tin do quan hệ chặn")
    mine = ConversationMember.objects.filter(user=user).values("conversation_id")
    theirs = ConversationMember.objects.filter(user=target).values("conversation_id")
    existing = (
        Conversation.objects.filter(type=Conversation.Type.DIRECT, id__in=mine)
        .filter(id__in=theirs)
        .order_by("created_at")
        .first()
    )
    if existing:
        return existing, False
    if not user_services.are_friends(user.id, target.id):
        raise PermissionDenied("Hai bạn cần kết bạn trước khi nhắn tin")
    conv = Conversation.objects.create(type=Conversation.Type.DIRECT, created_by=user)
    ConversationMember.objects.bulk_create(
        [ConversationMember(conversation=conv, user=user), ConversationMember(conversation=conv, user=target)]
    )
    return conv, True


# ------------------------------------------------------------------ UC-23: Chat nhóm
def _validate_new_members(user, ids):
    friend_ids = user_services.get_friend_ids(user.id)
    invalid = [i for i in ids if str(i) not in friend_ids]
    if invalid:
        raise ServiceError("Chỉ có thể thêm bạn bè vào nhóm chat", errors={"member_ids": invalid})


@transaction.atomic
def create_group_chat(user, title, member_ids):
    ids = {str(i) for i in member_ids} - {str(user.id)}
    if len(ids) < 2:
        raise ServiceError("Nhóm chat cần ít nhất 3 người (bạn và 2 người khác)")
    _validate_new_members(user, ids)
    conv = Conversation.objects.create(
        type=Conversation.Type.GROUP,
        title=sanitize_text(title, 100) or "Nhóm chat",
        created_by=user,
        last_message_at=timezone.now(),
    )
    ConversationMember.objects.create(conversation=conv, user=user, role=ConversationMember.Role.ADMIN)
    ConversationMember.objects.bulk_create([ConversationMember(conversation=conv, user_id=i) for i in ids])
    push_to_users(ids, "conversation.new", {"conversation_id": str(conv.id)})
    return conv


def add_members(user, conversation_id, new_ids):
    m = assert_member(user, conversation_id)
    if m.conversation.type != Conversation.Type.GROUP:
        raise ServiceError("Chỉ thêm thành viên vào nhóm chat")
    existing = set(member_ids(conversation_id))
    ids = {str(i) for i in new_ids} - existing
    _validate_new_members(user, ids)
    ConversationMember.objects.bulk_create(
        [ConversationMember(conversation_id=conversation_id, user_id=i) for i in ids]
    )
    push_to_users(ids, "conversation.new", {"conversation_id": str(conversation_id)})
    return ids


def remove_member(user, conversation_id, target_id):
    m = assert_member(user, conversation_id)
    if m.conversation.type != Conversation.Type.GROUP:
        raise ServiceError("Không thể rời cuộc trò chuyện 1-1")
    leaving_self = str(target_id) == str(user.id)
    if not leaving_self and m.role != ConversationMember.Role.ADMIN:
        raise PermissionDenied("Chỉ quản trị nhóm chat mới được xóa thành viên")
    deleted, _ = ConversationMember.objects.filter(conversation_id=conversation_id, user_id=target_id).delete()
    if not deleted:
        raise NotFound("Thành viên không thuộc nhóm chat")
    remaining = ConversationMember.objects.filter(conversation_id=conversation_id)
    if not remaining.exists():
        Conversation.objects.filter(id=conversation_id).delete()
    elif not remaining.filter(role=ConversationMember.Role.ADMIN).exists():
        first = remaining.order_by("created_at").first()
        first.role = ConversationMember.Role.ADMIN
        first.save(update_fields=["role"])


# ------------------------------------------------------------------ Tin nhắn
def messages_queryset(user, conversation_id):
    assert_member(user, conversation_id)
    return Message.objects.filter(conversation_id=conversation_id)


@transaction.atomic
def send_message(user, conversation_id, content="", file_url="", file_type="", client_id=None):
    m = assert_member(user, conversation_id)
    content = sanitize_text(content, 5000)
    file_url = (file_url or "").strip()
    if file_url and not file_url.startswith(settings.MEDIA_PUBLIC_BASE_URL):
        raise ServiceError("Tệp đính kèm không hợp lệ")
    if not content and not file_url:
        raise ServiceError("Tin nhắn trống")
    ids = member_ids(conversation_id)
    if m.conversation.type == Conversation.Type.DIRECT:
        other = next((i for i in ids if i != str(user.id)), None)
        if other and user_services.is_blocked(user.id, other):
            raise PermissionDenied("Không thể nhắn tin do quan hệ chặn")
    msg = Message.objects.create(
        conversation_id=conversation_id,
        sender=user,
        content=content,
        file_url=file_url,
        file_type=file_type if file_type in ("IMAGE", "VIDEO") else ("IMAGE" if file_url else ""),
    )
    Conversation.objects.filter(id=conversation_id).update(last_message_at=msg.created_at)
    ConversationMember.objects.filter(conversation_id=conversation_id, user=user).update(last_read_at=msg.created_at)
    payload = message_payload(msg, client_id)
    payload["sender"] = user_services.summarize(user)
    transaction.on_commit(lambda: push_to_users(ids, "message.new", payload))
    return msg


def mark_read(user, conversation_id):
    assert_member(user, conversation_id)
    now = timezone.now()
    ConversationMember.objects.filter(conversation_id=conversation_id, user=user).update(last_read_at=now)
    push_to_users(
        member_ids(conversation_id),
        "message.read",
        {"conversation_id": str(conversation_id), "user_id": str(user.id), "read_at": now.isoformat()},
    )
    return now


def broadcast_typing(user, conversation_id, is_typing):
    """Tín hiệu đang soạn tin: chỉ đi qua RAM (Redis Channel Layer), không ghi MySQL."""
    assert_member(user, conversation_id)
    others = [i for i in member_ids(conversation_id) if i != str(user.id)]
    push_to_users(
        others,
        "typing",
        {
            "conversation_id": str(conversation_id),
            "user_id": str(user.id),
            "full_name": user.full_name,
            "is_typing": bool(is_typing),
        },
    )


def total_unread(user):
    count = 0
    for m in ConversationMember.objects.filter(user=user):
        q = Message.objects.filter(conversation_id=m.conversation_id).exclude(sender=user)
        if m.last_read_at:
            q = q.filter(created_at__gt=m.last_read_at)
        count += 1 if q.exists() else 0
    return count


# ------------------------------------------------------------------ Presence (UC-24)
def online_friends(user):
    return sorted(presence.online_ids(user_services.get_friend_ids(user.id)))


def notify_presence(user_id, is_online):
    push_to_users(user_services.get_friend_ids(user_id), "presence", {"user_id": str(user_id), "is_online": is_online})
