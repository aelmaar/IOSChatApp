from django.core.management.base import BaseCommand
from chats.models import Conversations
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deletes conversations that are invisible to both users"

    def handle(self, *args, **options):
        # Find conversation invisible to both users

        invisible_conversations = Conversations.objects.filter(
            IsVisibleToUser1=False, IsVisibleToUser2=False
        )

        count = invisible_conversations.count()
        # Deletes them
        invisible_conversations.delete()

        logger.info(f"Deleted {count} invisible conversations")
