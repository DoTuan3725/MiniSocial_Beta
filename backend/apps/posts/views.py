from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView

from common.pagination import TimeCursorPagination, paginate
from common.responses import api_success

from . import services
from .models import Post


class PostCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True, max_length=10000)
    privacy = serializers.ChoiceField(choices=Post.Privacy.choices, required=False, default=Post.Privacy.PUBLIC)
    group_id = serializers.UUIDField(required=False, allow_null=True)
    files = serializers.ListField(child=serializers.FileField(), required=False)


class PostUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True, max_length=10000)
    privacy = serializers.ChoiceField(choices=Post.Privacy.choices, required=False)


class CommentSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000)
    parent_id = serializers.UUIDField(required=False, allow_null=True)


class ShareSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000, required=False, allow_blank=True)


def _serializer_for(viewer):
    return lambda page: services.serialize_posts(page, viewer)


class FeedView(APIView):
    """
    UC-13: Bảng tin = bài của chính mình + bài PUBLIC/FRIENDS của bạn bè (loại người bị chặn),
    phân trang con trỏ. Trang đầu được cache danh sách ID trong Redis.
    has_friends=false -> frontend hiển thị gợi ý kết bạn.
    """

    @extend_schema(parameters=[OpenApiParameter("cursor", str)])
    def get(self, request):
        user = request.user
        qs, has_friends = services.feed_queryset(user)
        extra = {"has_friends": has_friends}
        message = "Thành công" if has_friends else "Bảng tin trống, hãy kết bạn để xem bài viết mới!"
        first_page = "cursor" not in request.query_params and "page_size" not in request.query_params
        if first_page:
            cached = services.get_cached_first_page(user.id)
            if cached is not None:
                posts = services.posts_by_ids(cached["ids"])
                return api_success(
                    {
                        "results": services.serialize_posts(posts, user),
                        "next": cached["next"],
                        "previous": None,
                        **extra,
                        "cached": True,
                    },
                    message,
                )
        paginator = TimeCursorPagination()
        page = paginator.paginate_queryset(qs, request)
        if first_page:
            services.set_cached_first_page(user.id, [str(p.id) for p in page], paginator.get_next_link())
        return paginator.get_paginated_response(services.serialize_posts(page, user), extra=extra, message=message)


class PostCreateView(APIView):
    """UC-11: đăng bài (multipart: content, privacy, group_id, files[] <= 10 tệp, mỗi tệp <= 10MB)."""

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(request={"multipart/form-data": PostCreateSerializer})
    def post(self, request):
        data = request.data
        s = PostCreateSerializer(
            data={k: data.get(k) for k in ("content", "privacy", "group_id") if data.get(k) not in (None, "")}
        )
        s.is_valid(raise_exception=True)
        files = request.FILES.getlist("files")
        post = services.create_post(request.user, files=files, **s.validated_data)
        msg = "Đã đăng bài viết"
        if post.is_flagged:
            msg = "Bài viết chứa từ ngữ không phù hợp và đang chờ quản trị viên xem xét"
        return api_success(services.serialize_posts([post], request.user)[0], msg, status.HTTP_201_CREATED)


class PostDetailView(APIView):
    """UC-12: xem / sửa / xóa mềm bài viết."""

    def get(self, request, post_id):
        post = services.get_visible_post(request.user, post_id)
        return api_success(services.serialize_posts([post], request.user)[0])

    @extend_schema(request=PostUpdateSerializer)
    def patch(self, request, post_id):
        s = PostUpdateSerializer(data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        post = services.update_post(request.user, post_id, s.validated_data)
        return api_success(services.serialize_posts([post], request.user)[0], "Đã cập nhật bài viết")

    def delete(self, request, post_id):
        services.delete_post(request.user, post_id)
        return api_success(message="Đã xóa bài viết")


class PinView(APIView):
    @extend_schema(request=None)
    def post(self, request, post_id):
        post = services.toggle_pin(request.user, post_id)
        return api_success({"is_pinned": post.is_pinned}, "Đã ghim bài viết" if post.is_pinned else "Đã bỏ ghim")


class UserPostsView(APIView):
    """Dòng thời gian trang cá nhân. Trang đầu kèm danh sách bài đã ghim."""

    def get(self, request, user_id):
        qs = services.profile_queryset(request.user, user_id)
        extra = None
        if "cursor" not in request.query_params:
            extra = {"pinned": services.serialize_posts(qs.filter(is_pinned=True)[:3], request.user)}
        return paginate(request, qs, _serializer_for(request.user), extra=extra)


class GroupPostsView(APIView):
    """UC-21: bài viết trong nhóm."""

    def get(self, request, group_id):
        return paginate(request, services.group_queryset(request.user, group_id), _serializer_for(request.user))


class LikeView(APIView):
    """UC-14: thích / bỏ thích (toggle, idempotent nhờ UNIQUE(post,user))."""

    @extend_schema(request=None)
    def post(self, request, post_id):
        liked, count = services.toggle_like(request.user, post_id)
        return api_success({"is_liked": liked, "likes_count": count})

    def get(self, request, post_id):
        return api_success(services.list_likers(request.user, post_id))


class CommentListCreateView(APIView):
    """UC-15: cây bình luận / thêm bình luận hoặc trả lời (parent_id)."""

    def get(self, request, post_id):
        return api_success(services.list_comments(request.user, post_id))

    @extend_schema(request=CommentSerializer)
    def post(self, request, post_id):
        s = CommentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        c = services.create_comment(
            request.user, post_id, s.validated_data["content"], s.validated_data.get("parent_id")
        )
        return api_success({"id": str(c.id), "content": c.content}, "Đã bình luận", status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    @extend_schema(request=CommentSerializer)
    def patch(self, request, comment_id):
        s = CommentSerializer(data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        c = services.update_comment(request.user, comment_id, s.validated_data.get("content", ""))
        return api_success({"id": str(c.id), "content": c.content}, "Đã sửa bình luận")

    def delete(self, request, comment_id):
        removed = services.delete_comment_by_user(request.user, comment_id)
        return api_success({"removed": removed}, "Đã xóa bình luận")


class ShareView(APIView):
    """UC-16: chia sẻ bài viết công khai lên trang cá nhân."""

    @extend_schema(request=ShareSerializer)
    def post(self, request, post_id):
        s = ShareSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        share = services.share_post(request.user, post_id, s.validated_data.get("content", ""))
        return api_success({"id": str(share.id)}, "Đã chia sẻ bài viết", status.HTTP_201_CREATED)


class UserSharesView(APIView):
    def get(self, request, user_id):
        return api_success(services.list_shares_of_user(request.user, user_id))
