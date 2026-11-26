from django.urls import path

from . import views

urlpatterns = [
    path("", views.GroupListCreateView.as_view(), name="groups"),
    path("<uuid:group_id>/", views.GroupDetailView.as_view(), name="group-detail"),
    path("<uuid:group_id>/join/", views.JoinView.as_view(), name="group-join"),
    path("<uuid:group_id>/leave/", views.LeaveView.as_view(), name="group-leave"),
    path("<uuid:group_id>/members/", views.MemberListView.as_view(), name="group-members"),
    path("<uuid:group_id>/members/<uuid:member_id>/", views.MemberDetailView.as_view(), name="group-member"),
    path("<uuid:group_id>/members/<uuid:member_id>/approve/", views.ApproveView.as_view(), name="group-approve"),
    path("<uuid:group_id>/members/<uuid:member_id>/reject/", views.RejectView.as_view(), name="group-reject"),
]
