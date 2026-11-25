from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from common.exceptions import ServiceError
from common.responses import api_success

from . import services


class UploadView(APIView):
    """Tải 1 tệp (avatar | cover | chat). Trả về URL đích; ảnh sẵn sàng sau khi Celery nén xong (~1-2s)."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"file": {"type": "string", "format": "binary"}, "purpose": {"type": "string"}},
            }
        },
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            raise ServiceError("Thiếu tệp tải lên (field 'file')")
        data = services.upload_single(uploaded, request.data.get("purpose", "chat"))
        return api_success(data, "Đã nhận tệp, đang xử lý", status.HTTP_201_CREATED)
