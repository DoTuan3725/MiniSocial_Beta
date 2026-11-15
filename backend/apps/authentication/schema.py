from drf_spectacular.extensions import OpenApiAuthenticationExtension


class RedisJWTScheme(OpenApiAuthenticationExtension):
    """Hiển thị nút 'Authorize' (Bearer JWT) trên Swagger UI."""

    target_class = "apps.authentication.authentication.RedisJWTAuthentication"
    name = "BearerJWT"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
