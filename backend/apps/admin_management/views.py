from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.views import APIView

from apps.authentication import services as auth_services
from common.pagination import paginate
from common.permissions import IsSystemAdmin
from common.responses import api_success

from . import services
from .models import Report


class ReportCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=Report.TargetType.choices)
    target_id = serializers.UUIDField()
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    details = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class ResolveSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=[Report.Status.RESOLVED, Report.Status.REJECTED])
    action = serializers.ChoiceField(choices=Report.Action.choices, required=False, default=Report.Action.NONE)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class BanSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ReportSubmitView(APIView):
    """UC-27: người dùng báo cáo bài viết / bình luận / tài khoản."""

    @extend_schema(request=ReportCreateSerializer)
    def post(self, request):
        s = ReportCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        services.submit_report(request.user, **s.validated_data)
        return api_success(message="Đã gửi báo cáo tới quản trị viên", status_code=status.HTTP_201_CREATED)


class ReportReasonsView(APIView):
    def get(self, request):
        return api_success(
            [{"value": v, "label": label} for v, label in Report.Reason.choices if v != "OFFENSIVE_LANGUAGE"]
        )


class AdminReportListView(APIView):
    """UC-28: danh sách báo cáo (?status=PENDING|RESOLVED|REJECTED&target_type=)."""

    permission_classes = [IsSystemAdmin]

    def get(self, request):
        qs = services.report_queryset(
            request.query_params.get("status", "PENDING") or None, request.query_params.get("target_type")
        )
        return paginate(request, qs, services.serialize_reports)


class AdminReportResolveView(APIView):
    permission_classes = [IsSystemAdmin]

    @extend_schema(request=ResolveSerializer)
    def post(self, request, report_id):
        s = ResolveSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        report = services.resolve_report(request.user, report_id, **s.validated_data)
        return api_success(services.report_payload(report), "Đã xử lý báo cáo")


class AdminUserListView(APIView):
    """UC-28: danh sách người dùng (?q=, ?status=active|banned|unverified)."""

    permission_classes = [IsSystemAdmin]

    def get(self, request):
        qs = auth_services.admin_user_queryset(request.query_params.get("q"), request.query_params.get("status"))
        return paginate(
            request, qs.select_related("profile"), lambda page: [services.user_admin_payload(u) for u in page]
        )


class AdminBanView(APIView):
    permission_classes = [IsSystemAdmin]

    @extend_schema(request=BanSerializer)
    def post(self, request, user_id):
        s = BanSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        services.ban(request.user, user_id, s.validated_data.get("reason", ""))
        return api_success(message="Đã khóa tài khoản")


class AdminUnbanView(APIView):
    permission_classes = [IsSystemAdmin]

    @extend_schema(request=None)
    def post(self, request, user_id):
        services.unban(user_id)
        return api_success(message="Đã mở khóa tài khoản")


class AdminDashboardView(APIView):
    """UC-28: thống kê DAU/MAU, người dùng & bài viết mới theo ngày, báo cáo chờ xử lý."""

    permission_classes = [IsSystemAdmin]

    def get(self, request):
        return api_success(services.dashboard())
