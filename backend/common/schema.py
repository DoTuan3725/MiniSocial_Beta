"""Schema OpenAPI cho APIView: response mặc định là object {success, message, data}."""

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes


class ApiAutoSchema(AutoSchema):
    def get_request_serializer(self):
        if getattr(self.view, "serializer_class", None):
            return super().get_request_serializer()
        return None

    def get_response_serializers(self):
        return OpenApiTypes.OBJECT
