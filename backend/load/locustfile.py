"""
Kiểm thử tải 100 CCU (NFR-PERF-04):
    python manage.py seed_demo   # tạo tài khoản demo
    locust -f load/locustfile.py --host http://localhost -u 100 -r 10 -t 5m --headless
Tiêu chí: P95 < 500ms cho API thường, feed < 1s, 0% lỗi 5xx.
"""

import random

from locust import HttpUser, between, task

ACCOUNTS = [f"{s}@minisocial.local" for s in ("linh", "son", "ha", "duc", "mai", "khoa")]


class SocialUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        r = self.client.post("/api/v1/auth/login/", json={"email": random.choice(ACCOUNTS), "password": "Demo@123"})
        token = r.json()["data"]["access_token"]
        self.client.headers["Authorization"] = f"Bearer {token}"

    @task(5)
    def feed(self):
        self.client.get("/api/v1/posts/feed/", name="feed")

    @task(2)
    def notifications(self):
        self.client.get("/api/v1/notifications/", name="notifications")

    @task(2)
    def conversations(self):
        self.client.get("/api/v1/chat/conversations/", name="conversations")

    @task(1)
    def create_post(self):
        self.client.post(
            "/api/v1/posts/", data={"content": "Bài kiểm thử tải", "privacy": "FRIENDS"}, name="create_post"
        )
