"""NOTIFICATION SERVICE: tạo thông báo, đẩy realtime qua WebSocket, đánh dấu đã đọc."""

from apps.users import services as user_services
from common.realtime import push_to_user

from .models import Notification


def payload(n, actors=None):
    actors = actors if actors is not None else user_services.get_user_summaries([n.actor_id])
    return {
        "id": str(n.id),
        "verb": n.verb,
        "entity_type": n.entity_type,
        "entity_id": str(n.entity_id) if n.entity_id else None,
        "content": n.content,
        "actor": actors.get(str(n.actor_id)) if n.actor_id else None,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
    }


def notify(recipient_id, verb, entity_type, entity_id, content, actor_id=None, dedupe=False):
    if actor_id and str(actor_id) == str(recipient_id):
        return None
    if actor_id and user_services.is_blocked(actor_id, recipient_id):
        return None
    if (
        dedupe
        and Notification.objects.filter(
            recipient_id=recipient_id, actor_id=actor_id, verb=verb, entity_id=entity_id, is_read=False
        ).exists()
    ):
        return None
    n = Notification.objects.create(
        recipient_id=recipient_id,
        actor_id=actor_id,
        verb=verb,
        entity_type=entity_type,
        entity_id=entity_id,
        content=content[:255],
    )
    data = payload(n)
    data["unread_count"] = unread_count(recipient_id)
    push_to_user(recipient_id, "notification.new", data)
    return n


def actor_name(actor_id):
    s = user_services.get_user_summary(actor_id)
    return s["full_name"] if s else "Ai đó"


def list_queryset(user):
    return Notification.objects.filter(recipient=user)


def serialize_many(items):
    items = list(items)
    actors = user_services.get_user_summaries({n.actor_id for n in items if n.actor_id})
    return [payload(n, actors) for n in items]


def unread_count(user_id):
    return Notification.objects.filter(recipient_id=user_id, is_read=False).count()


def mark_read(user, notification_id):
    return Notification.objects.filter(id=notification_id, recipient=user).update(is_read=True)


def mark_all_read(user):
    return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
