from django.test import TestCase
from unittest.mock import Mock
from chat_app.helpers import create_test_user
from chats.serializers import ConversationsSerializer
from django.http import Http404
from chats.models import Conversations, Messages


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
