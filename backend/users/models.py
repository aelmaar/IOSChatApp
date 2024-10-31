from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group, Permission

# Create your models here.
class Users(AbstractUser):
    email = models.EmailField(unique=True, null=False)
    first_name = models.CharField(max_length=30, null=False)
    last_name = models.CharField(max_length=30, null=False)
    birthdate = models.DateField(null=False)
    picture = models.URLField(blank=True, null=True)

    # Avoid clashes with the 'groups' and 'user_permissions' fields in the Django AbstractUser class
    groups = models.ManyToManyField(
        Group,
        related_name='custom_group_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_permission_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username
