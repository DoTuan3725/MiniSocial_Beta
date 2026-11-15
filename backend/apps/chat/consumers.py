"""
Một kết nối WebSocket cho mỗi tab trình duyệt: wss://domain/ws/chat/?token=...
Client -> Server:
  {"type": "message.send", "conversation_id", "content", "file_url"?, "client_id"?}
  {"type": "typing", "conversation_id", "is_typing"}
  {"type": "read", "conversation_id"}
  {"type": "ping"}
Server -> Client:
  message.new | message.read | typing | presence | notification.new | conversation.new | pong | error
"""

import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from common.exceptions import ServiceError
from common.realtime import user_group

from . import presence, services

logger = logging.getLogger(__name__)


class RealtimeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        self.uid = str(self.user.id)
        await self.channel_layer.group_add(user_group(self.uid), self.channel_name)
        await self.accept()
        became_online = await database_sync_to_async(presence.connect)(self.uid)
        if became_online:
            await database_sync_to_async(services.notify_presence)(self.uid, True)

    async def disconnect(self, code):
        if not getattr(self, "uid", None):
            return
        await self.channel_layer.group_discard(user_group(self.uid), self.channel_name)
        went_offline = await database_sync_to_async(presence.disconnect)(self.uid)
        if went_offline:
            await database_sync_to_async(services.notify_presence)(self.uid, False)

    async def receive_json(self, content, **kwargs):
        kind = content.get("type")
        try:
            if kind == "ping":
                await database_sync_to_async(presence.heartbeat)(self.uid)
                await self.send_json({"type": "pong"})
            elif kind == "message.send":
                await database_sync_to_async(services.send_message)(
                    self.user,
                    content.get("conversation_id"),
                    content.get("content", ""),
                    content.get("file_url", ""),
                    content.get("file_type", ""),
                    content.get("client_id"),
                )
            elif kind == "typing":
                await database_sync_to_async(services.broadcast_typing)(
                    self.user, content.get("conversation_id"), content.get("is_typing", True)
                )
            elif kind == "read":
                await database_sync_to_async(services.mark_read)(self.user, content.get("conversation_id"))
            else:
                await self.send_json({"type": "error", "data": {"message": "Loại sự kiện không hỗ trợ"}})
        except ServiceError as exc:
            await self.send_json(
                {"type": "error", "data": {"message": exc.message, "client_id": content.get("client_id")}}
            )
        except Exception:  # noqa: BLE001
            logger.exception("Lỗi xử lý WebSocket")
            await self.send_json(
                {"type": "error", "data": {"message": "Lỗi máy chủ", "client_id": content.get("client_id")}}
            )

    async def push(self, event):
        await self.send_json({"type": event["event"], "data": event["data"]})
