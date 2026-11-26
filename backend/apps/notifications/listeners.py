"""
Phân hệ Notification tự lắng nghe sự kiện từ Event Bus và tạo thông báo.
Các phân hệ phát sự kiện không hề biết tới phân hệ này (decoupled).
"""

from common import events

from .models import Notification as N
from .services import actor_name, notify

V, E = N.Verb, N.EntityType


@events.subscribe(events.FRIEND_REQUEST_SENT)
def on_friend_request(p):
    notify(
        p["recipient_id"],
        V.FRIEND_REQUEST,
        E.USER,
        p["actor_id"],
        f"{actor_name(p['actor_id'])} đã gửi cho bạn lời mời kết bạn",
        p["actor_id"],
    )


@events.subscribe(events.FRIEND_ACCEPTED)
def on_friend_accepted(p):
    notify(
        p["recipient_id"],
        V.FRIEND_ACCEPTED,
        E.USER,
        p["actor_id"],
        f"{actor_name(p['actor_id'])} đã chấp nhận lời mời kết bạn",
        p["actor_id"],
    )


@events.subscribe(events.POST_LIKED)
def on_post_liked(p):
    notify(
        p["recipient_id"],
        V.POST_LIKED,
        E.POST,
        p["post_id"],
        f"{actor_name(p['actor_id'])} đã thích bài viết của bạn",
        p["actor_id"],
        dedupe=True,
    )


@events.subscribe(events.COMMENT_CREATED)
def on_comment(p):
    name = actor_name(p["actor_id"])
    for rid in p.get("recipient_ids", []):
        if rid == p.get("post_author_id"):
            notify(
                rid, V.POST_COMMENTED, E.POST, p["post_id"], f"{name} đã bình luận về bài viết của bạn", p["actor_id"]
            )
        else:
            notify(rid, V.COMMENT_REPLIED, E.POST, p["post_id"], f"{name} đã trả lời bình luận của bạn", p["actor_id"])


@events.subscribe(events.POST_SHARED)
def on_post_shared(p):
    notify(
        p["recipient_id"],
        V.POST_SHARED,
        E.POST,
        p["post_id"],
        f"{actor_name(p['actor_id'])} đã chia sẻ bài viết của bạn",
        p["actor_id"],
    )


@events.subscribe(events.GROUP_JOIN_REQUESTED)
def on_group_join_requested(p):
    name = actor_name(p["actor_id"])
    for rid in p.get("recipient_ids", []):
        notify(
            rid,
            V.GROUP_JOIN_REQUEST,
            E.GROUP,
            p["group_id"],
            f"{name} muốn tham gia nhóm {p.get('group_name', '')}",
            p["actor_id"],
        )


@events.subscribe(events.GROUP_JOIN_APPROVED)
def on_group_join_approved(p):
    notify(
        p["recipient_id"],
        V.GROUP_JOIN_APPROVED,
        E.GROUP,
        p["group_id"],
        f"Bạn đã được duyệt vào nhóm {p.get('group_name', '')}",
        p["actor_id"],
    )


@events.subscribe(events.REPORT_RESOLVED)
def on_report_resolved(p):
    if p.get("reporter_id"):
        notify(
            p["reporter_id"],
            V.REPORT_RESOLVED,
            E.REPORT,
            p["report_id"],
            "Báo cáo vi phạm của bạn đã được quản trị viên xử lý. Cảm ơn bạn!",
        )


@events.subscribe(events.USER_WARNED)
def on_user_warned(p):
    notify(
        p["user_id"],
        V.SYSTEM,
        E.REPORT,
        p.get("report_id"),
        f"Cảnh cáo từ quản trị viên: {p.get('note') or 'nội dung của bạn vi phạm tiêu chuẩn cộng đồng'}",
    )
