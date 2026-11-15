"""ADMIN & MODERATION SERVICE (UC-27, UC-28)."""

from django.db import transaction
from django.utils import timezone

from apps.authentication import services as auth_services
from apps.groups import services as group_services
from apps.media_files import services as media_services
from apps.posts import services as post_services
from apps.users import services as user_services
from common import events
from common.exceptions import NotFound, ServiceError
from common.text import sanitize_text

from .models import Report

T, A, S = Report.TargetType, Report.Action, Report.Status


def _resolve_target_owner(target_type, target_id):
    if target_type == T.POST:
        brief = post_services.get_post_brief(target_id)
        return brief and brief["author_id"]
    if target_type == T.COMMENT:
        brief = post_services.get_comment_brief(target_id)
        return brief and brief["author_id"]
    if target_type == T.USER:
        return str(target_id) if user_services.get_user_summary(target_id) else None
    return None


# ------------------------------------------------------------------ UC-27: Báo cáo vi phạm
def submit_report(user, target_type, target_id, reason, details=""):
    owner = _resolve_target_owner(target_type, target_id)
    if not owner:
        raise NotFound("Đối tượng bị báo cáo không tồn tại")
    if str(owner) == str(user.id):
        raise ServiceError("Bạn không thể báo cáo nội dung của chính mình")
    if Report.objects.filter(reporter=user, target_type=target_type, target_id=target_id, status=S.PENDING).exists():
        raise ServiceError("Bạn đã báo cáo nội dung này, quản trị viên đang xem xét", code="DUPLICATE_REPORT")
    report = Report.objects.create(
        reporter=user,
        target_type=target_type,
        target_id=target_id,
        reported_user_id=owner,
        reason=reason,
        details=sanitize_text(details, 2000),
    )
    events.publish(events.REPORT_CREATED, report_id=str(report.id))
    return report


def create_auto_report(target_type, target_id, owner_id, words):
    return Report.objects.create(
        is_auto=True,
        target_type=target_type,
        target_id=target_id,
        reported_user_id=owner_id,
        reason=Report.Reason.OFFENSIVE_LANGUAGE,
        details="Bộ lọc tự động phát hiện: " + ", ".join(words),
    )


def _target_preview(r):
    if r.target_type == T.POST:
        return post_services.get_post_brief(r.target_id)
    if r.target_type == T.COMMENT:
        return post_services.get_comment_brief(r.target_id)
    return user_services.get_user_summary(r.target_id)


def report_payload(r, users=None):
    users = (
        users
        if users is not None
        else user_services.get_user_summaries([r.reporter_id, r.reported_user_id, r.resolved_by_id])
    )
    return {
        "id": str(r.id),
        "is_auto": r.is_auto,
        "reporter": users.get(str(r.reporter_id)) if r.reporter_id else None,
        "reported_user": users.get(str(r.reported_user_id)) if r.reported_user_id else None,
        "target_type": r.target_type,
        "target_id": str(r.target_id),
        "target": _target_preview(r),
        "reason": r.reason,
        "reason_label": r.get_reason_display(),
        "details": r.details,
        "status": r.status,
        "action_taken": r.action_taken,
        "resolved_by": users.get(str(r.resolved_by_id)) if r.resolved_by_id else None,
        "resolution_notes": r.resolution_notes,
        "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        "created_at": r.created_at.isoformat(),
    }


def serialize_reports(items):
    items = list(items)
    ids = set()
    for r in items:
        ids |= {r.reporter_id, r.reported_user_id, r.resolved_by_id}
    users = user_services.get_user_summaries(ids)
    return [report_payload(r, users) for r in items]


def report_queryset(status=None, target_type=None):
    qs = Report.objects.all()
    if status:
        qs = qs.filter(status=status)
    if target_type:
        qs = qs.filter(target_type=target_type)
    return qs


@transaction.atomic
def resolve_report(admin, report_id, decision, action=A.NONE, notes=""):
    report = Report.objects.select_for_update().filter(id=report_id).first()
    if not report:
        raise NotFound("Không tìm thấy báo cáo")
    if report.status != S.PENDING:
        raise ServiceError("Báo cáo đã được xử lý trước đó")
    notes = sanitize_text(notes, 2000)
    if decision == S.REJECTED:
        action = A.NONE
        if report.target_type == T.POST:
            post_services.unflag_post(report.target_id)
    elif decision == S.RESOLVED:
        if action == A.DELETE_CONTENT:
            if report.target_type == T.POST:
                post_services.soft_delete_post(report.target_id)
            elif report.target_type == T.COMMENT:
                post_services.delete_comment(report.target_id)
            else:
                raise ServiceError("Không thể gỡ nội dung của báo cáo loại USER, hãy chọn Khóa tài khoản")
        elif action == A.BAN_USER:
            if not report.reported_user_id:
                raise ServiceError("Không xác định được người vi phạm")
            user_services.ban_user(report.reported_user_id, notes)
        elif action == A.WARN_USER and report.reported_user_id:
            events.publish(
                events.USER_WARNED, user_id=str(report.reported_user_id), report_id=str(report.id), note=notes
            )
    else:
        raise ServiceError("decision phải là RESOLVED hoặc REJECTED")

    now = timezone.now()
    # Đóng luôn mọi báo cáo đang chờ trên cùng đối tượng
    same_target = Report.objects.filter(target_type=report.target_type, target_id=report.target_id, status=S.PENDING)
    reporter_ids = [str(i) for i in same_target.exclude(reporter__isnull=True).values_list("reporter_id", flat=True)]
    same_target.update(status=decision, action_taken=action, resolved_by=admin, resolution_notes=notes, resolved_at=now)
    for rid in reporter_ids:
        events.publish(events.REPORT_RESOLVED, report_id=str(report.id), reporter_id=rid, decision=decision)
    report.refresh_from_db()
    return report


# ------------------------------------------------------------------ UC-28: Quản lý người dùng & thống kê
def ban(admin, user_id, reason=""):
    if str(admin.id) == str(user_id):
        raise ServiceError("Không thể tự khóa tài khoản của mình")
    return user_services.ban_user(user_id, reason)


def unban(user_id):
    return user_services.unban_user(user_id)


def user_admin_payload(u):
    return {
        **user_services.summarize(u),
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "email_verified": u.email_verified,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "created_at": u.created_at.isoformat(),
        "reports_received": Report.objects.filter(reported_user_id=u.id).count(),
    }


def dashboard():
    users = auth_services.user_stats()
    posts = post_services.post_stats()
    return {
        **users,
        **posts,
        **group_services.group_stats(),
        **media_services.storage_stats(),
        "pending_reports": Report.objects.filter(status=S.PENDING).count(),
        "auto_reports": Report.objects.filter(is_auto=True).count(),
    }
