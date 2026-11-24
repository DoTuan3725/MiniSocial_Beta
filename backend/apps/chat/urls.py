from django.urls import path

from . import views

urlpatterns = [
    path("conversations/", views.ConversationListView.as_view(), name="conversations"),
    path("conversations/direct/", views.DirectConversationView.as_view(), name="conversation-direct"),
    path("conversations/group/", views.GroupConversationView.as_view(), name="conversation-group"),
    path("conversations/<uuid:conversation_id>/", views.ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<uuid:conversation_id>/members/", views.MembersView.as_view(), name="conversation-members"),
    path(
        "conversations/<uuid:conversation_id>/members/<uuid:user_id>/",
        views.MemberDetailView.as_view(),
        name="conversation-member",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        views.MessageListCreateView.as_view(),
        name="conversation-messages",
    ),
    path("conversations/<uuid:conversation_id>/read/", views.ReadView.as_view(), name="conversation-read"),
    path("presence/", views.PresenceView.as_view(), name="presence"),
    path("unread/", views.UnreadView.as_view(), name="chat-unread"),
]
