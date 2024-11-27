from django.test import TestCase
from unittest.mock import Mock
from chat_app.helpers import create_test_user
from chats.serializers import ConversationsSerializer, MessagesSerializer
from django.http import Http404
from chats.models import Conversations, Messages
from rest_framework.serializers import ValidationError


class ConversationsSerializerTests(TestCase):

    def setUp(self) -> None:
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        self.another_user = create_test_user(
            username="anotheruser", email="anotheruser@example.com"
        )

        self.mock_request = Mock()
        self.mock_request.user = self.user

    def test_user2_username_field_with_invalid_data(self):
        test_cases = [
            ("", "This field may not be blank."),
            (
                "anouarelmaaroufiejfdjkjldioafiejfajkdvnakjsdvijefij",
                "Ensure this field has no more than 30 characters.",
            ),
        ]

        for value, error in test_cases:
            with self.subTest():
                serializer = ConversationsSerializer(data={"user2_username": value})
                self.assertFalse(serializer.is_valid(), msg=serializer.errors)
                self.assertEqual(serializer.errors["user2_username"][0], error)

    def test_nonexistent_user(self):

        with self.assertRaises(Http404):
            serializer = ConversationsSerializer(
                data={"user2_username": "nonexistentuser"},
                context={"request": self.mock_request},
            )

            self.assertFalse(serializer.is_valid(), msg=serializer.errors)

    def test_success_conversation_creation(self):

        serializer = ConversationsSerializer(
            data={"user2_username": self.another_user.username},
            context={"request": self.mock_request},
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        conversation = serializer.save()
        self.assertEqual(conversation.user2, self.another_user)
        self.assertEqual(conversation.user1, self.user)
        self.assertEqual(
            serializer.data["user"].get("username"), self.another_user.username
        )
        self.assertIn("id", serializer.data)
        self.assertFalse(serializer.data["IsBlockedByMe"])
        self.assertFalse(serializer.data["IsBlockedByOtherUser"])
        self.assertIsNone(serializer.data["lastMessage"])

    def test_duplicate_conversation_creation(self):
        Conversations.objects.create(user1=self.user, user2=self.another_user)

        serializer = ConversationsSerializer(
            data={"user2_username": self.another_user.username},
            context={"request": self.mock_request},
        )

        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertEqual(
            serializer.errors["non_field_errors"][0],
            "A conversation between these users already exists.",
        )

    def test_conversation_blocked_by_auth_and_other_user(self):
        conversation = Conversations.objects.create(
            user1=self.user, user2=self.another_user
        )

        conversation.IsBlockedByUser1 = True
        conversation.IsBlockedByUser2 = True
        conversation.save()

        serializer = ConversationsSerializer(
            conversation, context={"request": self.mock_request}
        )

        self.assertEqual(
            serializer.data["user"].get("username"), self.another_user.username
        )

        self.assertTrue(serializer.data["IsBlockedByMe"])
        self.assertTrue(serializer.data["IsBlockedByOtherUser"])


class MessagesSerializerTests(TestCase):

    def setUp(self) -> None:
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        another_user = create_test_user(
            username="anotheruser", email="anotheruser@example.com"
        )

        # Create a conversation
        self.conversation = Conversations.objects.create(
            user1=self.user, user2=another_user
        )

        self.mock_request = Mock()
        self.mock_request.user = self.user
        self.mock_request.query_params = {"conversation_id": self.conversation.id}

    def test_content_field_validation(self):
        test_cases = [
            {
                "input": "Hello, this is a normal message",
                "expected": "Hello, this is a normal message",
            },
            {
                "input": "Line 1\nLine 2",
                "expected": "Line 1\nLine 2",
            },
            {
                "input": "<script>alert('xss')</script>",
                "expected": "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;",
            },
            {
                "input": "<img src='malicious.jpg'/>",
                "expected": "&lt;img src=&#x27;malicious.jpg&#x27;/&gt;",
            },
            {
                "input": "Hello 世界 🎉",
                "expected": "Hello 世界 🎉",
            },
            {
                "input": "    ",
                "expected": "    ",
            },
            # Invalid cases
            {
                "input": None,
                "error": "This field may not be null.",
            },
            {
                "input": "",
                "error": "This field may not be blank.",
            },
            {
                "input": {"key": "value"},
                "error": "Not a valid string.",
            },
        ]

        for case in test_cases:
            with self.subTest():
                if "error" in case:
                    serializer = MessagesSerializer(
                        data={"content": case["input"]},
                        context={"request": self.mock_request},
                    )
                    with self.assertRaises(ValidationError) as cm:
                        serializer.is_valid(raise_exception=True)
                    self.assertEqual(
                        str(cm.exception.detail.get("content")[0]), case["error"]
                    )

                else:
                    serializer = MessagesSerializer()
                    result = serializer.validate_content(case["input"])
                    self.assertEqual(result, case["expected"])

    def test_nonexistent_conversation(self):

        self.mock_request.query_params = {"conversation_id": 1000}
        with self.assertRaises(Http404):
            serializer = MessagesSerializer(
                data={"content": "Hello Friends!"},
                context={"request": self.mock_request},
            )

            self.assertFalse(serializer.is_valid(), msg=serializer.errors)

    def test_success_message_creation(self):
        serializer = MessagesSerializer(
            data={"content": "Hello friends!"}, context={"request": self.mock_request}
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        message = serializer.save()
        self.assertIsNotNone(message)
        self.assertEqual(message.content, "Hello friends!")
        self.assertEqual(message.conversation.id, self.conversation.id)
        self.assertEqual(message.sender, self.user)
