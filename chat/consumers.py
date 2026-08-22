import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import User

from .models import Message

# This is process-local presence only. Message delivery itself uses the channel layer.
ONLINE_USERS = set()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        try:
            self.other_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        except (KeyError, TypeError, ValueError):
            await self.close(code=4000)
            return

        if not self.user or not self.user.is_authenticated or self.other_id == self.user.id:
            await self.close(code=4001)
            return

        # A websocket is accepted only for the account's registered device.
        if not await self.device_is_valid():
            await self.close(code=4003)
            return

        self.room_name = "chat_%s_%s" % tuple(sorted([self.user.id, self.other_id]))
        ONLINE_USERS.add(self.user.id)
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        ids = await self.mark_delivered_for_user()
        if ids:
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "delivered_event", "ids": ids, "user_id": self.user.id},
            )

        await self.send_json({
            "event": "presence",
            "user_id": self.other_id,
            "online": self.other_id in ONLINE_USERS,
        })
        await self.channel_layer.group_send(
            self.room_name,
            {"type": "presence_event", "user_id": self.user.id, "online": True},
        )

    async def disconnect(self, code):
        if hasattr(self, "room_name"):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
        if getattr(self, "user", None):
            ONLINE_USERS.discard(self.user.id)
            if hasattr(self, "room_name"):
                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "presence_event", "user_id": self.user.id, "online": False},
                )

    async def receive_json(self, content, **kwargs):
        action = content.get("action")

        if action == "typing":
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "typing_event", "user_id": self.user.id, "typing": bool(content.get("typing"))},
            )
            return

        if action == "seen":
            ids = content.get("ids") or []
            changed = await self.mark_seen(ids)
            if changed:
                await self.channel_layer.group_send(
                    self.room_name,
                    {"type": "seen_event", "ids": changed, "seen_by": self.user.id},
                )
            return

        if action == "text":
            text = (content.get("text") or "").strip()
            if text:
                msg = await self.create_message("text", text)
                await self.broadcast_new(msg)

    async def broadcast_new(self, msg):
        # Broadcast to both sender and receiver immediately. No refresh is needed.
        await self.channel_layer.group_send(
            self.room_name,
            {"type": "message_event", "message": msg.as_dict()},
        )

    async def message_event(self, event):
        await self.send_json({"event": "message", "message": event["message"]})

    async def typing_event(self, event):
        if event["user_id"] != self.user.id:
            await self.send_json({"event": "typing", "typing": event["typing"]})

    async def presence_event(self, event):
        if event["user_id"] != self.user.id:
            await self.send_json({
                "event": "presence",
                "user_id": event["user_id"],
                "online": event["online"],
            })

    async def delivered_event(self, event):
        await self.send_json({
            "event": "delivered",
            "ids": event["ids"],
            "user_id": event["user_id"],
        })

    async def seen_event(self, event):
        await self.send_json({
            "event": "seen",
            "ids": event["ids"],
            "seen_by": event["seen_by"],
        })

    @database_sync_to_async
    def device_is_valid(self):
        from .models import DeviceSession
        session = DeviceSession.objects.filter(user_id=self.user.id).first()
        if not session:
            return False
        token = self.scope.get("cookies", {}).get("lschat_device")
        return bool(token and token == session.device_token)

    @database_sync_to_async
    def create_message(self, kind, text=""):
        other = User.objects.get(pk=self.other_id)
        return Message.objects.create(
            sender=self.user,
            receiver=other,
            message_type=kind,
            text=text,
            delivered=self.other_id in ONLINE_USERS,
        )

    @database_sync_to_async
    def mark_seen(self, ids):
        qs = Message.objects.filter(
            id__in=ids,
            receiver=self.user,
            sender_id=self.other_id,
            seen=False,
        )
        changed = list(qs.values_list("id", flat=True))
        # Seen does NOT delete the message immediately. It remains visible
        # during the live session and is removed on the next room refresh.
        qs.update(seen=True)
        return changed

    @database_sync_to_async
    def mark_delivered_for_user(self):
        qs = Message.objects.filter(
            receiver=self.user,
            sender_id=self.other_id,
            delivered=False,
        )
        ids = list(qs.values_list("id", flat=True))
        qs.update(delivered=True)
        return ids
