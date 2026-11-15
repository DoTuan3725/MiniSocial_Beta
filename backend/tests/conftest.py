import io
import shutil

import fakeredis
import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.authentication.tokens import issue_tokens
from common import redis_client

from .factories import UserFactory


@pytest.fixture(autouse=True)
def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    redis_client.set_redis_client(client)
    yield client
    client.flushall()
    redis_client.set_redis_client(None)


@pytest.fixture(autouse=True)
def run_on_commit_immediately(monkeypatch):
    """Event Bus & Celery dùng transaction.on_commit; trong test cho chạy ngay để kiểm tra luồng end-to-end."""
    from django.db import transaction

    monkeypatch.setattr(transaction, "on_commit", lambda func, using=None, robust=False: func())


@pytest.fixture(autouse=True)
def clean_media():
    from django.core.cache import cache

    cache.clear()
    yield
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    shutil.rmtree(settings.TEMP_UPLOAD_DIR, ignore_errors=True)


@pytest.fixture
def api():
    return APIClient()


def auth_client(user):
    client = APIClient()
    access, _ = issue_tokens(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    client.user = user
    return client


@pytest.fixture
def make_client():
    return auth_client


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def other(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return UserFactory(role="ADMIN", is_staff=True)


@pytest.fixture
def client_a(user):
    return auth_client(user)


@pytest.fixture
def client_b(other):
    return auth_client(other)


def make_image(name="photo.png", size=(800, 600), fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", size, (30, 120, 200)).save(buf, fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@pytest.fixture
def image_file():
    return make_image()


def befriend(a, b):
    from apps.users import services

    f = services.send_friend_request(a, b.id)
    if f.status != "ACCEPTED":
        services.accept_friend_request(b, f.id)
