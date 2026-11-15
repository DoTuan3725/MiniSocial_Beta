from django.urls import path

from . import views

urlpatterns = [
    path("me/", views.MyProfileView.as_view(), name="users-me"),
    path("search/", views.SearchView.as_view(), name="users-search"),
    path("suggestions/", views.SuggestionsView.as_view(), name="users-suggestions"),
    path("friends/", views.FriendListView.as_view(), name="friends-list"),
    path("friends/requests/", views.FriendRequestListCreateView.as_view(), name="friend-requests"),
    path(
        "friends/requests/<uuid:friendship_id>/accept/", views.FriendRequestAcceptView.as_view(), name="friend-accept"
    ),
    path(
        "friends/requests/<uuid:friendship_id>/decline/",
        views.FriendRequestDeclineView.as_view(),
        name="friend-decline",
    ),
    path("friends/requests/<uuid:friendship_id>/", views.FriendRequestCancelView.as_view(), name="friend-cancel"),
    path("friends/<uuid:user_id>/", views.UnfriendView.as_view(), name="friend-remove"),
    path("blocks/", views.BlockListCreateView.as_view(), name="blocks"),
    path("blocks/<uuid:user_id>/", views.UnblockView.as_view(), name="unblock"),
    path("<uuid:user_id>/", views.UserProfileView.as_view(), name="users-detail"),
]
