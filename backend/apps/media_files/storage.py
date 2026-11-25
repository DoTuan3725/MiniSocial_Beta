"""
Lớp trừu tượng lưu trữ đối tượng:
- S3Storage: Cloudflare R2 (production) hoặc MinIO (local) qua giao thức S3 (boto3).
- LocalStorage: lưu vào MEDIA_ROOT (dùng khi chạy test / không có object storage).
"""

import json
import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


class LocalStorage:
    def put(self, key, data, content_type):
        path = Path(settings.MEDIA_ROOT) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete(self, key):
        path = Path(settings.MEDIA_ROOT) / key
        if path.exists():
            path.unlink()


class S3Storage:
    def __init__(self):
        import boto3
        from botocore.config import Config

        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        self._bucket_checked = False

    def _ensure_bucket(self):
        if self._bucket_checked:
            return
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:  # noqa: BLE001
            self.client.create_bucket(Bucket=self.bucket)
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket}/*"],
                    }
                ],
            }
            try:  # MinIO hỗ trợ bucket policy; R2 thì bật public qua dashboard / custom domain
                self.client.put_bucket_policy(Bucket=self.bucket, Policy=json.dumps(policy))
            except Exception:  # noqa: BLE001
                logger.info("Bỏ qua đặt bucket policy (không hỗ trợ trên backend này)")
        self._bucket_checked = True

    def put(self, key, data, content_type):
        self._ensure_bucket()
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable",
        )

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)


_storage = None


def get_storage():
    global _storage
    if _storage is None:
        _storage = S3Storage() if settings.STORAGE_BACKEND == "s3" else LocalStorage()
    return _storage


def public_url(key):
    return f"{settings.MEDIA_PUBLIC_BASE_URL.rstrip('/')}/{key}"
