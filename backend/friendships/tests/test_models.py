from django.test import TestCase
from django.contrib.auth import get_user_model
from friendships.models import Friendships
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

Users = get_user_model()


class FriendshipModelTests(TestCase):
    def setUp(self) -> None:
        self.user1 = Users.objects.create_user(
            username="testuser",
            email="testuser@gmail.com",
            first_name="Test",
            last_name="User",
            password="Swift-1234",
        )
        self.user2 = Users.objects.create_user(
            username="anotheruser",
            email="anotheruser@gmail.com",
            first_name="Another",
            last_name="User",
            password="Swift-1234",
        )

    def test_basic_friendship_creation(self):
        friendship = Friendships.objects.create(user1=self.user1, user2=self.user2)

        self.assertIsNotNone(friendship)
        self.assertEqual(friendship.status, "PENDING")

    def test_friendships_unique_constraints(self):
        Friendships.objects.create(user1=self.user1, user2=self.user2)

        with self.assertRaises(ValidationError):
            Friendships.objects.create(user1=self.user2, user2=self.user1)

    def test_changing_friendships_status_to_accepted(self):
        friendship = Friendships.objects.create(user1=self.user1, user2=self.user2)

        friendship.status = Friendships.ACCEPTED
        friendship.save()

        self.assertEqual(friendship.status, Friendships.ACCEPTED)
