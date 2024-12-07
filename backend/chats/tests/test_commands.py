from django.test import TestCase
from chats.models import Conversations
from chat_app.helpers import create_test_user
from django.core.management import call_command


class CleanupConversationTests(TestCase):

    def test_command(self):
        user1 = create_test_user(username="user1", email="user1@example.com")
        user2 = create_test_user(username="user2", email="user2@example.com")

        conversation = Conversations.objects.create(user1=user1, user2=user2)

        # Make the conversation invisible to both users
        conversation.IsVisibleToUser1 = False
        conversation.IsVisibleToUser2 = False
        conversation.save()

        # Execute the command
        call_command("cleanup_conversations")

        # The conversation should not exist
        with self.assertRaises(Conversations.DoesNotExist):
            Conversations.objects.get(pk=conversation.id)
