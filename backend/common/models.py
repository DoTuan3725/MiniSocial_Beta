import uuid6
from django.db import models


class BaseModel(models.Model):
    """
    Lớp nền cho cả 16 bảng.
    - id: UUIDv7 (48 bit đầu là timestamp ms) -> ghi nối tiếp vào cuối B-Tree như số tự tăng,
      nhưng không đoán được (chống IDOR / dò quét ID).
    - created_at / updated_at tự động.
    """

    id = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
