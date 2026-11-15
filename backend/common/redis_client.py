"""
Kết nối Redis dùng chung (OTP, blacklist token, presence, feed cache, khóa brute-force).
Khi chạy test, conftest.py thay thế client này bằng fakeredis.
"""

import redis
from django.conf import settings

_client = None


def get_redis():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def set_redis_client(client):
    """Dùng trong test để tiêm fakeredis."""
    global _client
    _client = client
