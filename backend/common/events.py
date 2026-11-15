"""
INTERNAL EVENT BUS - trục giao tiếp liên phân hệ.

Phân hệ phát sự kiện không cần biết ai lắng nghe (decoupled):
    publish(POST_LIKED, post_id=..., actor_id=..., author_id=...)
Phân hệ khác đăng ký trong AppConfig.ready():
    @subscribe(POST_LIKED)
    def on_post_liked(payload): ...

Sự kiện chỉ được phát SAU KHI giao dịch DB commit (transaction.on_commit)
để listener không đọc phải dữ liệu chưa tồn tại. Một listener lỗi không làm hỏng luồng chính.
"""

import logging
from collections import defaultdict

from django.db import transaction

logger = logging.getLogger("event_bus")

# ---- Danh mục sự kiện ----
USER_REGISTERED = "user_registered"
USER_BANNED = "user_banned"
FRIEND_REQUEST_SENT = "friend_request_sent"
FRIEND_ACCEPTED = "friend_accepted"
FRIENDSHIP_CHANGED = "friendship_changed"
POST_CREATED = "post_created"
POST_DELETED = "post_deleted"
POST_LIKED = "post_liked"
POST_SHARED = "post_shared"
POST_FLAGGED = "post_flagged"
COMMENT_CREATED = "comment_created"
COMMENT_FLAGGED = "comment_flagged"
GROUP_JOIN_REQUESTED = "group_join_requested"
GROUP_JOIN_APPROVED = "group_join_approved"
GROUP_DELETED = "group_deleted"
REPORT_CREATED = "report_created"
REPORT_RESOLVED = "report_resolved"
USER_WARNED = "user_warned"

_subscribers = defaultdict(list)


def subscribe(event_name):
    def decorator(func):
        if func not in _subscribers[event_name]:
            _subscribers[event_name].append(func)
        return func

    return decorator


def _dispatch(event_name, payload):
    for handler in list(_subscribers.get(event_name, [])):
        try:
            handler(payload)
        except Exception:  # noqa: BLE001 - listener lỗi không được làm hỏng luồng chính
            logger.exception("Listener %s lỗi khi xử lý sự kiện %s", handler.__name__, event_name)


def publish(event_name, **payload):
    payload["event"] = event_name
    transaction.on_commit(lambda: _dispatch(event_name, payload))


def subscribers_of(event_name):
    return list(_subscribers.get(event_name, []))
