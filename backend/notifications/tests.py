from django.test import TestCase, TransactionTestCase
from channels.testing import WebsocketCommunicator
from unittest.mock import MagicMock, patch
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from notifications.consumers import ChatConsumer, NotificationConsumer
from friendships.models import Friendships
from rest_framework.test import APIClient
from chats.models import Conversations
from rest_framework import status

# Create your tests here.

Users = get_user_model()


class BaseConsumerTests(TransactionTestCase):

    async def create_user(self, username="testuser", email="testuser@example.com"):

        @database_sync_to_async
        def create():
            return Users.objects.create_user(
                username=username,
                email=email,
                first_name="Test",
                last_name="User",
                birthdate="1990-01-01",
                password="Swift-1234",
            )

        return await create()

    async def create_friendship(self, user1, user2):

        @database_sync_to_async
        def create():
            return Friendships.objects.create(
                user1=user1, user2=user2, status=Friendships.ACCEPTED
            )

        return await create()

    async def get_communicator(self, consumer_class, path, user=None):
        communicator = WebsocketCommunicator(
            consumer_class.as_asgi(),
            path=path,
        )

        communicator.scope["user"] = user

        return communicator

    @database_sync_to_async
    def authenticate_user(self, username, password):
        client = APIClient()
        response = client.post(
            "/api/login/", {"username_or_email": username, "password": password}
        )
        return response.data.get("access")

    @database_sync_to_async
    def send_message(self, url, data, access_token):
        client = APIClient()
        headers = {"Authorization": f"Bearer {access_token}"}
        return client.post(
            url,
            data=data,
            headers=headers,
        )


class TestChatConsumer(BaseConsumerTests):

    async def test_connection_success(self):
        """Test Websocket successful connection"""
        user = await self.create_user()

        communicator = await self.get_communicator(ChatConsumer, "/ws/chat/", user)

        try:
            connected, _ = await communicator.connect()

            self.assertTrue(connected)
        finally:
            await communicator.disconnect()

    async def test_connection_failure(self):
        """Test Websocket failure connection"""

        communicator = await self.get_communicator(ChatConsumer, "/ws/chat/")

        try:
            connected, _ = await communicator.connect()

            self.assertFalse(connected)
        finally:
            await communicator.disconnect()

    async def test_status_update(self):
        """Test status update notification to friends"""
        # Create two users
        user1 = await self.create_user(username="user1", email="user1@example.com")
        user2 = await self.create_user(username="user2", email="user2@example.com")

        # Setup Websocket communicators
        communicator1 = await self.get_communicator(ChatConsumer, "/ws/chat/", user1)
        communicator2 = await self.get_communicator(ChatConsumer, "/ws/chat/", user2)

        # Establish the Websocket connection
        await communicator1.connect()
        await communicator2.connect()

        # Create friendship
        await self.create_friendship(user1, user2)

        # Send status update to user 2
        await communicator1.send_json_to({"status": "Online"})

        # Retrieve status update from user 1
        response = await communicator2.receive_json_from(timeout=2)

        # Check if user 2 receives the update from user 1
        self.assertEqual(
            response,
            {"type": "status_update", "username": user1.username, "status": "Online"},
        )

        # Close the connections
        await communicator1.disconnect()
        await communicator2.disconnect()

    @database_sync_to_async
    def create_conversation(self, user1, user2):
        return Conversations.objects.create(user1=user1, user2=user2)

    async def test_send_chat_message(self):
        """Test send chat message over Websocket"""
        # Create two users
        user1 = await self.create_user(username="user1", email="user1@example.com")
        user2 = await self.create_user(username="user2", email="user2@example.com")

        # Setup Websocket communicators
        communicator1 = await self.get_communicator(ChatConsumer, "/ws/chat/", user1)
        communicator2 = await self.get_communicator(ChatConsumer, "/ws/chat/", user2)

        try:

            # Connect Websockets
            await communicator1.connect()
            await communicator2.connect()

            # Create a conversation
            conversation = await self.create_conversation(user1, user2)

            # Authenticate user1 and get access token
            access_token = await self.authenticate_user(user1.username, "Swift-1234")

            # Send a new chat message to user2
            response = await self.send_message(
                f"/api/conversations/{conversation.id}/messages/",
                {"content": "Message received from user1"},
                access_token,
            )

            # Check the request is made successfuly
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Retrieve message from Websocket
            data_received = await communicator2.receive_json_from(timeout=2)

            # Check if the chat message is received from user1
            self.assertEqual(
                data_received["data"].get("content"), "Message received from user1"
            )
        finally:
            # Close connections
            await communicator1.disconnect()
            await communicator2.disconnect()


class TestNotificationConsumer(BaseConsumerTests):

    async def test_connection_success(self):
        """Test Websocket successful connection"""
        user = await self.create_user()

        communicator = await self.get_communicator(ChatConsumer, "/ws/chat/", user)

        try:
            connected, _ = await communicator.connect()

            self.assertTrue(connected)
        finally:
            await communicator.disconnect()

    async def test_connection_failure(self):
        """Test Websocket failure connection"""

        communicator = await self.get_communicator(ChatConsumer, "/ws/chat/")

        try:
            connected, _ = await communicator.connect()

            self.assertFalse(connected)
        finally:
            await communicator.disconnect()

    async def test_send_friend_request(self):
        """Test friend request over Websocket"""
        # Create two users
        user1 = await self.create_user(username="user1", email="user1@example.com")
        user2 = await self.create_user(username="user2", email="user2@example.com")

        # Setup Websocket communicators
        communicator1 = await self.get_communicator(ChatConsumer, "/ws/chat/", user1)
        communicator2 = await self.get_communicator(ChatConsumer, "/ws/chat/", user2)

        try:
            # Connect Websockets
            await communicator1.connect()
            await communicator2.connect()

            # Authenticate user1 and get access token
            access_token = await self.authenticate_user(user1.username, "Swift-1234")

            # Send a new friend request to user2
            response = await self.send_message(
                f"/api/friendships/",
                {"friend_username": "user2"},
                access_token,
            )

            # Check the request is made successfuly
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Retrieve message from Websocket
            data_received = await communicator2.receive_json_from(timeout=2)

            # Check if the friend request is received from user1
            self.assertEqual(data_received["type"], "friend_request")
        finally:
            # Close connections
            await communicator1.disconnect()
            await communicator2.disconnect()
