from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.views import APIView

from apps.users import services as user_services
from common.responses import api_success

from . import services
from .models import Group, GroupMember


class GroupWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    privacy = serializers.ChoiceField(choices=Group.Privacy.choices, required=False)
    cover_url = serializers.CharField(max_length=500, required=False, allow_blank=True)


class RoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=GroupMember.Role.choices)


def group_payload(group, membership=None):
    return {
        "id": str(group.id),
        "name": group.name,
        "description": group.description,
        "cover_url": group.cover_url,
        "privacy": group.privacy,
        "members_count": getattr(group, "members_count", 0),
        "created_by": str(group.created_by_id),
        "created_at": group.created_at.isoformat(),
        "my_membership": membership,
    }


class GroupListCreateView(APIView):
    """UC-17: danh sách nhóm (?q=, ?mine=1) / tạo nhóm (người tạo là ADMIN)."""

    def get(self, request):
        groups = list(
            services.list_groups(request.user, request.query_params.get("q"), request.query_params.get("mine") == "1")[
                :100
            ]
        )
        mine = services.my_memberships(request.user, [g.id for g in groups])
        return api_success([group_payload(g, mine.get(str(g.id))) for g in groups])

    @extend_schema(request=GroupWriteSerializer)
    def post(self, request):
        s = GroupWriteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        group = services.create_group(request.user, **s.validated_data)
        return api_success(
            group_payload(group, {"role": "ADMIN", "status": "ACCEPTED"}), "Đã tạo nhóm", status.HTTP_201_CREATED
        )


class GroupDetailView(APIView):
    def get(self, request, group_id):
        group = services.get_group(group_id)
        return api_success(group_payload(group, services.my_memberships(request.user, [group.id]).get(str(group.id))))

    @extend_schema(request=GroupWriteSerializer)
    def patch(self, request, group_id):
        s = GroupWriteSerializer(data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        group = services.update_group(request.user, group_id, s.validated_data)
        return api_success(
            group_payload(group, services.my_memberships(request.user, [group.id]).get(str(group.id))),
            "Đã cập nhật nhóm",
        )

    def delete(self, request, group_id):
        services.delete_group(request.user, group_id)
        return api_success(message="Đã giải tán nhóm")


class JoinView(APIView):
    """UC-18: tham gia nhóm công khai ngay / gửi yêu cầu vào nhóm kín."""

    @extend_schema(request=None)
    def post(self, request, group_id):
        m = services.join_group(request.user, group_id)
        msg = "Đã tham gia nhóm" if m.status == "ACCEPTED" else "Đã gửi yêu cầu, vui lòng chờ quản trị viên duyệt"
        return api_success({"role": m.role, "status": m.status}, msg)


class LeaveView(APIView):
    @extend_schema(request=None)
    def post(self, request, group_id):
        services.leave_group(request.user, group_id)
        return api_success(message="Đã rời nhóm")


class MemberListView(APIView):
    """?status=ACCEPTED (mặc định) | PENDING (chỉ ADMIN/MOD)."""

    def get(self, request, group_id):
        st = request.query_params.get("status", "ACCEPTED").upper()
        return api_success([services.member_payload(m) for m in services.list_members(request.user, group_id, st)])


class ApproveView(APIView):
    """UC-19: duyệt yêu cầu tham gia."""

    @extend_schema(request=None)
    def post(self, request, group_id, member_id):
        services.review_member(request.user, group_id, member_id, True)
        return api_success(message="Đã duyệt thành viên")


class RejectView(APIView):
    @extend_schema(request=None)
    def post(self, request, group_id, member_id):
        services.review_member(request.user, group_id, member_id, False)
        return api_success(message="Đã từ chối yêu cầu")


class MemberDetailView(APIView):
    """UC-20: đổi vai trò (PATCH, chỉ ADMIN) / mời ra khỏi nhóm (DELETE)."""

    @extend_schema(request=RoleSerializer)
    def patch(self, request, group_id, member_id):
        s = RoleSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        m = services.change_role(request.user, group_id, member_id, s.validated_data["role"])
        return api_success(
            {"id": str(m.id), "role": m.role, "user": user_services.get_user_summary(m.user_id)}, "Đã cập nhật vai trò"
        )

    def delete(self, request, group_id, member_id):
        services.kick_member(request.user, group_id, member_id)
        return api_success(message="Đã xóa thành viên khỏi nhóm")
