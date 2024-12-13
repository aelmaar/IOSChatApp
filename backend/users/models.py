from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group, Permission


# Create your models here.
class Users(AbstractUser):
    username = models.CharField(max_length=30, unique=True, null=False)
    email = models.EmailField(max_length=100, unique=True, null=False)
    first_name = models.CharField(max_length=30, null=False)
    last_name = models.CharField(max_length=30, null=False)
    birthdate = models.DateField(null=True, blank=True)
    picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    IsOAuth = models.BooleanField(default=False)
    IsOnline = models.BooleanField(default=False)

    # Avoid clashes with the 'groups' and 'user_permissions' fields in the Django AbstractUser class
    groups = models.ManyToManyField(
        Group,
        related_name="custom_group_set",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_permission_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def __str__(self):
        return self.username


class Blacklist(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="blacklist")
    blocked_user = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "blocked_user")

    def __str__(self):
        return f"{self.user} blocked {self.blocked_user}"
