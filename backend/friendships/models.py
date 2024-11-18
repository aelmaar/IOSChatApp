from typing import Iterable
from django.db import models
from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError

# Create your models here.


class Friendships(models.Model):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

    STATUS_CHOICES = {
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
    }

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendship_sent",
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendship_received",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")

    def clean(self) -> None:
        if self.pk is None:  # Only check for uniqueness, if this is a new instance
            if Friendships.objects.filter(
                Q(user1=self.user1, user2=self.user2)
                | Q(user1=self.user2, user2=self.user1)
            ).exists():
                raise ValidationError("This friendship already exists.")

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)
