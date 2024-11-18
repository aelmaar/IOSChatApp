from django.test import TestCase
from friendships.serializers import FriendshipsSerializer
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from django.http import Http404
from friendships.models import Friendships

Users = get_user_model()


class FriendshipsSerializerTests(TestCase):

    def setUp(self) -> None:
        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
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

    def test_invalidate_self_friendship(self):
        serializer = FriendshipsSerializer(
            data={"friend_username": self.user.username},
            context={"request": self.mock_request},
        )

        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertEqual(
            serializer.errors["friend_username"][0],
            "You cannot be friends with yourself.",
        )

    def test_not_existing_friend_username(self):

        with self.assertRaises(Http404):
            serializer = FriendshipsSerializer(
                data={"friend_username": "notexistinguser"},
                context={"request": self.mock_request},
            )

            self.assertFalse(serializer.is_valid(), msg=serializer.errors)

    def test_with_existing_friendship(self):
        another_user = Users.objects.create_user(
            username="anotheruser",
            email="anotheruser@example.com",
            first_name="Another",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        # Create a friendship
        Friendships.objects.create(user1=self.user, user2=another_user)

        # Create another friendship to test against an existing friendship
        serializer = FriendshipsSerializer(
            data={"friend_username": another_user.username},
            context={"request": self.mock_request},
        )

        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertEqual(
            serializer.errors["non_field_errors"][0], "Friendship already exists."
        )

    def test_successful_friendship_creation(self):
        another_user = Users.objects.create_user(
            username="anotheruser",
            email="anotheruser@example.com",
            first_name="Another",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        serializer = FriendshipsSerializer(
            data={"friend_username": another_user.username},
            context={"request": self.mock_request},
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        # Assert that the friend is the other user and the status is pending and the pending action is waiting for response
        friendship = serializer.save()
        self.assertEqual(friendship.user1, self.user)
        self.assertEqual(friendship.user2, another_user)

        self.assertEqual(friendship.status, Friendships.PENDING)
        self.assertEqual(serializer.data["pending_action"], "waiting_for_response")

    # Test the pending action when the user is the second user
    def test_pending_action_when_user_is_second_user(self):
        another_user = Users.objects.create_user(
            username="anotheruser",
            email="anotheruser@example.com",
            first_name="Another",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        # Create a friendship
        friendship = Friendships.objects.create(user1=another_user, user2=self.user)

        serializer = FriendshipsSerializer(friendship, context={"request": self.mock_request})

        self.assertEqual(serializer.data["pending_action"], "accept_or_reject")
