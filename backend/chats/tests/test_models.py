from django.test import TestCase
from chats.models import Conversations, Messages
from django.contrib.auth import get_user_model
from chat_app.helpers import create_test_user
from django.core.exceptions import ValidationError

Users = get_user_model()


class ConversationsModelTests(TestCase):

    def setUp(self) -> None:
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        self.another_user = create_test_user(
            username="anotheruser", email="anotheruser@example.com"
        )
        self.conversation = Conversations.objects.create(
            user1=self.user, user2=self.another_user
        )

    def test_success_conversation_creation(self):

        self.assertIsNotNone(self.conversation)
        self.assertEqual(self.conversation.user1, self.user)
        self.assertEqual(self.conversation.user2, self.another_user)
        self.assertIsNone(self.conversation.lastMessage)
        self.assertEqual(self.user.conversation_user1.all().first(), self.conversation)
        self.assertEqual(
            self.another_user.conversation_user2.all().first(), self.conversation
        )

    def test_duplicate_conversation_creation_fails(self):

        with self.assertRaises(ValidationError):
            Conversations.objects.create(user1=self.another_user, user2=self.user)

    def test_delete_user_after_conversation_creation(self):

        self.user.delete()

        self.conversation.refresh_from_db()
        self.assertIsNotNone(self.conversation)
        self.assertIsNone(self.conversation.user1)

    def test_assign_lastmessage_to_conversation(self):
        message = Messages.objects.create(
            conversation=self.conversation, sender=self.user, content="Last message!"
        )

        self.conversation.lastMessage = message
        prevLastMessageTimestamp = self.conversation.lastMessageTimestamp
        self.conversation.save()

        self.assertIsNotNone(self.conversation.lastMessage)
        self.assertNotEqual(
            self.conversation.lastMessageTimestamp, prevLastMessageTimestamp
        )


class MessageModelTests(TestCase):

    def setUp(self) -> None:
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        self.another_user = create_test_user(
            username="anotheruser", email="anotheruser@example.com"
        )
        self.conversation = Conversations.objects.create(
            user1=self.user, user2=self.another_user
        )
        self.message = Messages.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Test message content",
        )

    def test_success_message_creation(self):

        self.assertIsNotNone(self.message)
        self.assertEqual(self.message.conversation, self.conversation)
        self.assertEqual(self.message.sender, self.user)

    def test_message_deletion_after_delete_conversation(self):

        self.conversation.delete()

        with self.assertRaises(Messages.DoesNotExist):
            self.message.refresh_from_db()

    def test_required_message_content_field(self):

        with self.assertRaises(ValidationError):
            message = Messages.objects.create(
                conversation=self.conversation, sender=self.user
            )
            message.full_clean()
            message.save()
