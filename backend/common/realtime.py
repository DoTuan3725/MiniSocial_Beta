"""Đẩy gói tin tới WebSocket của một người dùng qua Redis Channel Layer (group 'user_<id>')."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def user_group(user_id):
    return f"user_{user_id}"


def push_to_user(user_id, event_type, data):
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(user_group(user_id), {"type": "push", "event": event_type, "data": data})
    except Exception:  # noqa: BLE001
        logger.exception("Không đẩy được sự kiện realtime %s tới %s", event_type, user_id)


def push_to_users(user_ids, event_type, data):
    for uid in set(str(u) for u in user_ids):
        push_to_user(uid, event_type, data)
