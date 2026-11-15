from django.urls import path

from . import views

urlpatterns = [
    path("", views.PostCreateView.as_view(), name="post-create"),
    path("feed/", views.FeedView.as_view(), name="feed"),
    path("user/<uuid:user_id>/", views.UserPostsView.as_view(), name="user-posts"),
    path("user/<uuid:user_id>/shares/", views.UserSharesView.as_view(), name="user-shares"),
    path("group/<uuid:group_id>/", views.GroupPostsView.as_view(), name="group-posts"),
    path("comments/<uuid:comment_id>/", views.CommentDetailView.as_view(), name="comment-detail"),
    path("<uuid:post_id>/", views.PostDetailView.as_view(), name="post-detail"),
    path("<uuid:post_id>/pin/", views.PinView.as_view(), name="post-pin"),
    path("<uuid:post_id>/like/", views.LikeView.as_view(), name="post-like"),
    path("<uuid:post_id>/comments/", views.CommentListCreateView.as_view(), name="post-comments"),
    path("<uuid:post_id>/share/", views.ShareView.as_view(), name="post-share"),
]
