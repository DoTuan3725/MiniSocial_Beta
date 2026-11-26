"""GROUP SERVICE - giao diện công khai của phân hệ Group (RBAC + máy trạng thái thành viên)."""

from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.utils import timezone

from apps.users import services as user_services
from common import events
from common.exceptions import NotFound, PermissionDenied, ServiceError
from common.text import sanitize_text, unaccent

from .models import Group, GroupMember

ROLE_RANK = {GroupMember.Role.MEMBER: 1, GroupMember.Role.MOD: 2, GroupMember.Role.ADMIN: 3}


def _accepted():
    return Q(members__status=GroupMember.Status.ACCEPTED)


def _annotated():
    return Group.objects.annotate(members_count=Count("members", filter=_accepted()))


def get_group(group_id):
    group = _annotated().filter(id=group_id).first()
    if not group:
        raise NotFound("Không tìm thấy nhóm")
    return group


def membership(user_id, group_id):
    return GroupMember.objects.filter(group_id=group_id, user_id=user_id).first()


def _active_member(user_id, group_id):
    return GroupMember.objects.filter(group_id=group_id, user_id=user_id, status=GroupMember.Status.ACCEPTED).first()


# ------------------------------------------------------------------ Dành cho phân hệ Post
def can_view_posts(user_id, group_id):
    group = Group.objects.filter(id=group_id).only("privacy").first()
    if not group:
        return False
    return group.privacy == Group.Privacy.PUBLIC or _active_member(user_id, group_id) is not None


def can_post(user_id, group_id):
    return _active_member(user_id, group_id) is not None


def can_moderate(user_id, group_id):
    m = _active_member(user_id, group_id)
    return bool(m and m.role in (GroupMember.Role.ADMIN, GroupMember.Role.MOD))


def get_group_briefs(group_ids):
    ids = [str(g) for g in group_ids if g]
    return {
        str(g.id): {"id": str(g.id), "name": g.name, "privacy": g.privacy} for g in Group.objects.filter(id__in=ids)
    }


def group_ids_of_user(user_id):
    return [
        str(i)
        for i in GroupMember.objects.filter(user_id=user_id, status=GroupMember.Status.ACCEPTED).values_list(
            "group_id", flat=True
        )
    ]


# ------------------------------------------------------------------ UC-17: Tạo & quản lý nhóm
@transaction.atomic
def create_group(user, name, description="", privacy=Group.Privacy.PUBLIC):
    name = sanitize_text(name, 100)
    if not name:
        raise ServiceError("Tên nhóm không được để trống")
    group = Group.objects.create(
        name=name, description=sanitize_text(description, 2000), privacy=privacy, created_by=user
    )
    GroupMember.objects.create(
        group=group,
        user=user,
        role=GroupMember.Role.ADMIN,
        status=GroupMember.Status.ACCEPTED,
        joined_at=timezone.now(),
    )
    return get_group(group.id)


def _require_role(user, group_id, min_role):
    m = _active_member(user.id, group_id)
    if not m or ROLE_RANK[m.role] < ROLE_RANK[min_role]:
        raise PermissionDenied("Bạn không có quyền quản lý nhóm này")
    return m


def update_group(user, group_id, data):
    _require_role(user, group_id, GroupMember.Role.ADMIN)
    group = Group.objects.get(id=group_id)
    if "name" in data:
        name = sanitize_text(data["name"], 100)
        if not name:
            raise ServiceError("Tên nhóm không được để trống")
        group.name = name
    if "description" in data:
        group.description = sanitize_text(data["description"], 2000)
    if "privacy" in data:
        group.privacy = data["privacy"]
    if "cover_url" in data:
        group.cover_url = data["cover_url"] or ""
    group.save()
    return get_group(group_id)


@transaction.atomic
def delete_group(user, group_id):
    _require_role(user, group_id, GroupMember.Role.ADMIN)
    Group.objects.filter(id=group_id).delete()
    events.publish(events.GROUP_DELETED, group_id=str(group_id), actor_id=str(user.id))


def list_groups(user, query=None, mine=False):
    qs = _annotated().order_by("-created_at")
    if mine:
        qs = qs.filter(id__in=group_ids_of_user(user.id))
    if query:
        for word in unaccent(query).split():
            qs = qs.filter(search_name__icontains=word)
    return qs


def my_memberships(user, group_ids):
    rows = GroupMember.objects.filter(user=user, group_id__in=list(group_ids))
    return {str(m.group_id): {"role": m.role, "status": m.status} for m in rows}


# ------------------------------------------------------------------ UC-18: Tham gia / rời nhóm
@transaction.atomic
def join_group(user, group_id):
    group = get_group(group_id)
    member = membership(user.id, group_id)
    if member and member.status == GroupMember.Status.ACCEPTED:
        raise ServiceError("Bạn đã là thành viên của nhóm")
    if member and member.status == GroupMember.Status.PENDING:
        raise ServiceError("Yêu cầu tham gia đang chờ duyệt")
    is_public = group.privacy == Group.Privacy.PUBLIC
    status = GroupMember.Status.ACCEPTED if is_public else GroupMember.Status.PENDING
    member, _ = GroupMember.objects.update_or_create(
        group=group,
        user=user,
        defaults={
            "role": GroupMember.Role.MEMBER,
            "status": status,
            "joined_at": timezone.now() if is_public else None,
        },
    )
    if not is_public:
        mod_ids = GroupMember.objects.filter(
            group=group, status=GroupMember.Status.ACCEPTED, role__in=[GroupMember.Role.ADMIN, GroupMember.Role.MOD]
        ).values_list("user_id", flat=True)
        events.publish(
            events.GROUP_JOIN_REQUESTED,
            group_id=str(group.id),
            group_name=group.name,
            actor_id=str(user.id),
            recipient_ids=[str(i) for i in mod_ids],
        )
    return member


def leave_group(user, group_id):
    member = _active_member(user.id, group_id) or membership(user.id, group_id)
    if not member:
        raise NotFound("Bạn không thuộc nhóm này")
    if member.role == GroupMember.Role.ADMIN and member.status == GroupMember.Status.ACCEPTED:
        other_admins = GroupMember.objects.filter(
            group_id=group_id, role=GroupMember.Role.ADMIN, status=GroupMember.Status.ACCEPTED
        ).exclude(id=member.id)
        if not other_admins.exists():
            raise ServiceError("Bạn là quản trị viên duy nhất. Hãy chỉ định quản trị viên khác hoặc giải tán nhóm.")
    member.delete()


# ------------------------------------------------------------------ UC-19, UC-20: Duyệt, phân quyền, kick
def list_members(user, group_id, status=GroupMember.Status.ACCEPTED):
    group = get_group(group_id)
    if status != GroupMember.Status.ACCEPTED and not can_moderate(user.id, group_id):
        raise PermissionDenied("Chỉ quản trị viên / kiểm duyệt viên xem được danh sách chờ duyệt")
    if group.privacy == Group.Privacy.PRIVATE and not _active_member(user.id, group_id):
        raise PermissionDenied("Nhóm kín: chỉ thành viên xem được danh sách thành viên")
    return (
        GroupMember.objects.filter(group_id=group_id, status=status)
        .select_related("user__profile")
        .order_by(
            Case(
                When(role=GroupMember.Role.ADMIN, then=Value(0)),
                When(role=GroupMember.Role.MOD, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            "joined_at",
            "created_at",
        )
    )


def _target(group_id, member_id):
    target = GroupMember.objects.filter(id=member_id, group_id=group_id).first()
    if not target:
        raise NotFound("Không tìm thấy thành viên")
    return target


@transaction.atomic
def review_member(moderator, group_id, member_id, approve):
    _require_role(moderator, group_id, GroupMember.Role.MOD)
    target = _target(group_id, member_id)
    if target.status != GroupMember.Status.PENDING:
        raise ServiceError("Yêu cầu này đã được xử lý")
    if approve:
        target.status = GroupMember.Status.ACCEPTED
        target.joined_at = timezone.now()
        group = Group.objects.get(id=group_id)
        events.publish(
            events.GROUP_JOIN_APPROVED,
            group_id=str(group_id),
            group_name=group.name,
            actor_id=str(moderator.id),
            recipient_id=str(target.user_id),
        )
    else:
        target.status = GroupMember.Status.REJECTED
    target.save()
    return target


def change_role(admin, group_id, member_id, role):
    _require_role(admin, group_id, GroupMember.Role.ADMIN)
    if role not in ROLE_RANK:
        raise ServiceError("Vai trò không hợp lệ")
    target = _target(group_id, member_id)
    if target.status != GroupMember.Status.ACCEPTED:
        raise ServiceError("Chỉ phân quyền cho thành viên chính thức")
    if str(target.user_id) == str(admin.id) and role != GroupMember.Role.ADMIN:
        if (
            not GroupMember.objects.filter(
                group_id=group_id, role=GroupMember.Role.ADMIN, status=GroupMember.Status.ACCEPTED
            )
            .exclude(id=target.id)
            .exists()
        ):
            raise ServiceError("Nhóm cần ít nhất một quản trị viên")
    target.role = role
    target.save(update_fields=["role", "updated_at"])
    return target


def kick_member(moderator, group_id, member_id):
    actor = _require_role(moderator, group_id, GroupMember.Role.MOD)
    target = _target(group_id, member_id)
    if str(target.user_id) == str(moderator.id):
        raise ServiceError("Dùng chức năng rời nhóm để tự rời")
    if ROLE_RANK[target.role] >= ROLE_RANK[actor.role]:
        raise PermissionDenied("Không thể xóa thành viên có vai trò ngang hoặc cao hơn bạn")
    target.delete()


def member_payload(m):
    return {
        "id": str(m.id),
        "user": user_services.summarize(m.user),
        "role": m.role,
        "status": m.status,
        "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        "requested_at": m.created_at.isoformat(),
    }


def group_stats():
    return {"total_groups": Group.objects.count()}
