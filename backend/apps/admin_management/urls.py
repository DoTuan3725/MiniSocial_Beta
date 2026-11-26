from django.urls import path

from . import views

urlpatterns = [
    path("reports/", views.ReportSubmitView.as_view(), name="report-submit"),
    path("reports/reasons/", views.ReportReasonsView.as_view(), name="report-reasons"),
    path("manage/reports/", views.AdminReportListView.as_view(), name="admin-reports"),
    path(
        "manage/reports/<uuid:report_id>/resolve/", views.AdminReportResolveView.as_view(), name="admin-report-resolve"
    ),
    path("manage/users/", views.AdminUserListView.as_view(), name="admin-users"),
    path("manage/users/<uuid:user_id>/ban/", views.AdminBanView.as_view(), name="admin-ban"),
    path("manage/users/<uuid:user_id>/unban/", views.AdminUnbanView.as_view(), name="admin-unban"),
    path("manage/dashboard/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
]
