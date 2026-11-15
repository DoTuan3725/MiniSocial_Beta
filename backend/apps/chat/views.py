from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.views import APIView

from common.pagination import MessageCursorPagination, paginate
from common.responses import api_success

from . import services


class DirectSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class GroupChatSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100, required=False, allow_blank=True)
    member_ids = serializers.ListField(child=serializers.UUIDField(), min_length=2)


class MembersSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)


class SendSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    file_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    file_type = serializers.CharField(max_length=10, required=False, allow_blank=True)
    client_id = serializers.CharField(max_length=64, required=False, allow_blank=True)


class ConversationListView(APIView):
    def get(self, request):
        return api_success(services.list_conversations(request.user))


class DirectConversationView(APIView):
    """UC-22: mở (hoặc tạo) hội thoại 1-1 với bạn bè."""

    @extend_schema(request=DirectSerializer)
    def post(self, request):
        s = DirectSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        conv, created = services.get_or_create_direct(request.user, s.validated_data["user_id"])
        return api_success(services.conversation_payload(conv, request.user), status_code=201 if created else 200)


class GroupConversationView(APIView):
    """UC-23: tạo nhóm chat từ danh sách bạn bè."""

    @extend_schema(request=GroupChatSerializer)
    def post(self, request):
        s = GroupChatSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        conv = services.create_group_chat(
            request.user, s.validated_data.get("title", ""), s.validated_data["member_ids"]
        )
        return api_success(
            services.conversation_payload(conv, request.user), "Đã tạo nhóm chat", status.HTTP_201_CREATED
        )


class ConversationDetailView(APIView):
    def get(self, request, conversation_id):
        m = services.assert_member(request.user, conversation_id)
        return api_success(services.conversation_payload(m.conversation, request.user))


class MembersView(APIView):
    @extend_schema(request=MembersSerializer)
    def post(self, request, conversation_id):
        s = MembersSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        added = services.add_members(request.user, conversation_id, s.validated_data["user_ids"])
        return api_success({"added": sorted(added)}, "Đã thêm thành viên")


class MemberDetailView(APIView):
    def delete(self, request, conversation_id, user_id):
        services.remove_member(request.user, conversation_id, user_id)
        return api_success(message="Đã cập nhật thành viên nhóm chat")


class MessageListCreateView(APIView):
    """UC-24: lịch sử tin nhắn (cursor, mới nhất trước) / gửi tin nhắn qua REST (dự phòng khi mất WebSocket)."""

    def get(self, request, conversation_id):
        qs = services.messages_queryset(request.user, conversation_id)
        return paginate(request, qs, lambda page: [services.message_payload(m) for m in page], MessageCursorPagination)

    @extend_schema(request=SendSerializer)
    def post(self, request, conversation_id):
        s = SendSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        msg = services.send_message(request.user, conversation_id, **s.validated_data)
        return api_success(
            services.message_payload(msg, s.validated_data.get("client_id")), status_code=status.HTTP_201_CREATED
        )


class ReadView(APIView):
    @extend_schema(request=None)
    def post(self, request, conversation_id):
        read_at = services.mark_read(request.user, conversation_id)
        return api_success({"read_at": read_at.isoformat()})


class PresenceView(APIView):
    """Danh sách ID bạn bè đang online (chấm xanh)."""

    def get(self, request):
        return api_success({"online": services.online_friends(request.user)})


class UnreadView(APIView):
    def get(self, request):
        return api_success({"unread_conversations": services.total_unread(request.user)})
