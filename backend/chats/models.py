from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.exceptions import ValidationError

Users = get_user_model()


class Messages(models.Model):
    conversation = models.ForeignKey("Conversations", on_delete=models.CASCADE)
    sender = models.ForeignKey(Users, null=True, on_delete=models.SET_NULL)
    content = models.TextField(blank=False, null=False)
    IsReadByReceiver = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Conversations(models.Model):
    user1 = models.ForeignKey(
        Users,
        null=True,
        on_delete=models.SET_NULL,
        related_name="conversation_user1",
    )
    user2 = models.ForeignKey(
        Users,
        null=True,
        on_delete=models.SET_NULL,
        related_name="conversation_user2",
    )

    IsVisibleToUser1 = models.BooleanField(default=True)
    IsVisibleToUser2 = models.BooleanField(default=True)

    IsBlockedByUser1 = models.BooleanField(default=False)
    IsBlockedByUser2 = models.BooleanField(default=False)

    lastMessage = models.ForeignKey(Messages, null=True, on_delete=models.SET_NULL)
    lastMessageTimestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user1", "user2")

    def __str__(self) -> str:
        return f"Conversation between {self.user1} and {self.user2}"

    def clean(self) -> None:
        if self.pk is None:
            if Conversations.objects.filter(
                Q(user1=self.user1, user2=self.user2)
                | Q(user1=self.user2, user2=self.user1)
            ).exists():
                raise ValidationError("This conversation already exists.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
