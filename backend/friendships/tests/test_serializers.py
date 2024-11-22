from django.test import TestCase
from friendships.serializers import FriendshipsSerializer
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from django.http import Http404
from friendships.models import Friendships
from chat_app.helpers import create_test_user

Users = get_user_model()


class FriendshipsSerializerTests(TestCase):

    def setUp(self) -> None:
        self.user = create_test_user(username="testuser", email="testuser@example.com")

        self.another_user = create_test_user(
            username="anotheruser", email="anotheruser@example.com"
        )

        self.mock_request = Mock()
        self.mock_request.user = self.user

    def test_friend_username_field_with_invalid_data(self):
        test_cases = [
            ("", "This field may not be blank."),
            (
                "anouarelmaaroufiejfdjkjldioafiejfajkdvnakjsdvijefij",
                "Ensure this field has no more than 30 characters.",
            ),
        ]

        for value, error in test_cases:
            with self.subTest():
                serializer = FriendshipsSerializer(data={"friend_username": value})
                self.assertFalse(serializer.is_valid(), msg=serializer.errors)
                self.assertEqual(serializer.errors["friend_username"][0], error)

    def test_cannot_create_self_friendships(self):
        serializer = FriendshipsSerializer(
            data={"friend_username": self.user.username},
            context={"request": self.mock_request},
        )

        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertEqual(
            serializer.errors["friend_username"][0],
            "You cannot be friends with yourself.",
        )

    def test_with_nonexisting_friend_username(self):

        with self.assertRaises(Http404):
            serializer = FriendshipsSerializer(
                data={"friend_username": "notexistinguser"},
                context={"request": self.mock_request},
            )

            self.assertFalse(serializer.is_valid(), msg=serializer.errors)

    def test_duplicate_friendship_creation_fails(self):

        # Create a friendship
        Friendships.objects.create(user1=self.user, user2=self.another_user)

        # Create another friendship to test against an existing friendship
        serializer = FriendshipsSerializer(
            data={"friend_username": self.another_user.username},
            context={"request": self.mock_request},
        )

        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertEqual(
            serializer.errors["non_field_errors"][0], "Friendship already exists."
        )

    def test_successful_friendship_creation(self):

        serializer = FriendshipsSerializer(
            data={"friend_username": self.another_user.username},
            context={"request": self.mock_request},
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        friendship = serializer.save()
        self.assertEqual(friendship.user1, self.user)
        self.assertEqual(friendship.user2, self.another_user)

        self.assertEqual(friendship.status, Friendships.PENDING)
        self.assertEqual(serializer.data["pending_action"], "waiting_for_response")

    def test_second_user_pending_action(self):
        # Create a friendship
        friendship = Friendships.objects.create(
            user1=self.another_user, user2=self.user
        )

        serializer = FriendshipsSerializer(
            friendship, context={"request": self.mock_request}
        )

        self.assertEqual(serializer.data["pending_action"], "accept_or_reject")
