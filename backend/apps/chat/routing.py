from django.urls import re_path

from .consumers import RealtimeConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/$", RealtimeConsumer.as_asgi()),
    re_path(r"^ws/$", RealtimeConsumer.as_asgi()),
]
