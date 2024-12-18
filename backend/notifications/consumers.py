# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from friendships.models import Friendships
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class BaseConsumer(AsyncWebsocketConsumer):
    """Base consumer for handling common functionalities for chat and notification consumers"""
    async def connect(self):
        self.user = self.scope.get("user", None)

        if self.user is None:
            await self.close(code=4001)
            return

        self.group_room_name = f"chat_{self.user.id}"

        # Join room group
        await self.channel_layer.group_add(self.group_room_name, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        # Check if group_room_name exists before trying to use it
        if hasattr(self, "group_room_name"):
            # Leave room group
            await self.channel_layer.group_discard(
                self.group_room_name, self.channel_name
            )
        return await super().disconnect(code)

    async def receive(self, text_data):
        return await super().receive(text_data)

    async def chat_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps(message))


class ChatConsumer(BaseConsumer):
    """Consumer for handling user's online status and chat notifications"""

    @database_sync_to_async
    def get_friend_notifications(self, status):
        # Query user's friends
        friendships = Friendships.objects.filter(
            Q(user1=self.user, status=Friendships.ACCEPTED)
            | Q(user2=self.user, status=Friendships.ACCEPTED)
        )

        notifications = []

        for friend in friendships:
            friend_room_name = ""
            if friend.user1 == self.user:
                friend_room_name = f"chat_{friend.user2.id}"
            else:
                friend_room_name = f"chat_{friend.user1.id}"
            notifications.append(
                {
                    "room_name": friend_room_name,
                    "message": {
                        "type": "status_update",
                        "username": self.user.username,
                        "status": status,
                    },
                },
            )

        return notifications

    @database_sync_to_async
    def save_user_status(self, status):
        self.user.IsOnline = True if status == "Online" else False
        self.user.save()

    async def receive(self, text_data):
        """
        Receive message from WebSocket to update user's online status and send notifications to user's friends
        """
        text_data_json = json.loads(text_data)

        # Retrieve user's online status
        status = text_data_json["status"]

        # Update auth user's online status
        await self.save_user_status(status)

        # Get user's friends and create a list of notifications to send to them
        notifications = await self.get_friend_notifications(status)

        # Send notifications to user's friends
        for notification in notifications:
            await self.channel_layer.group_send(
                notification["room_name"],
                {
                    "type": "chat.message",
                    "message": notification["message"],
                },
            )

    @staticmethod
    def sendChatMessage(receiver_id, message_data):
        """Send chat message to the receiver"""
        channel_layer = get_channel_layer()

        if not channel_layer:
            print("Channel layer is not available")
            return

        async_to_sync(channel_layer.group_send)(
            f"chat_{receiver_id}",
            {
                "type": "chat_message",
                "message": {
                    "data": message_data,
                },
            },
        )


class NotificationConsumer(BaseConsumer):
    """Consumer for handling friend requests notifications"""

    @staticmethod
    def sendFriendRequest(receiver_id):
        """Send friend request notification to the receiver"""
        channel_layer = get_channel_layer()

        if not channel_layer:
            print("Channel layer is not available")
            return

        async_to_sync(channel_layer.group_send)(
            f"chat_{receiver_id}",
            {"type": "chat_message", "message": {"type": "friend_request"}},
        )
