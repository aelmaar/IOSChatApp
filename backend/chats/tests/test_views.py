from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from chats.models import Conversations, Messages
from chat_app.helpers import create_test_user, get_auth_headers


class ConversationsViewTests(TestCase):

    def setUp(self) -> None:
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        another_user = create_test_user(
            username="anotheruser", email="anotheruser@example.com"
        )
        third_user = create_test_user(
            username="thirduser", email="thirduser@example.com"
        )
        self.client = APIClient()
        self.url = "/api/conversations/"
        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

        # Create conversation
        Conversations.objects.create(user1=self.user, user2=another_user)
        Conversations.objects.create(user1=self.user, user2=third_user)

    def test_view_with_nonauthenticated_users(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user2_username_field_with_invalid_data(self):
        test_cases = [
            ("", "This field may not be blank."),
            (
                "anouarelmaaroufiejfdjkjldioafiejfajkdvnakjsdvijefij",
                "Ensure this field has no more than 30 characters.",
            ),
        ]

        for value, error in test_cases:
            with self.subTest():
                response = self.client.post(
                    self.url, {"user2_username": value}, headers=self.headers
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["user2_username"][0], error)

    def test_conversation_creation_with_nonexistent_user(self):
        response = self.client.post(
            self.url, {"user2_username": "nonexistentuser"}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_success_conversation_creation(self):
        new_user = create_test_user(username="newuser", email="newuser@example.com")

        response = self.client.post(
            self.url, {"user2_username": new_user.username}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        conversation = Conversations.objects.filter(pk=response.data["id"])

        self.assertTrue(conversation.exists())
        self.assertEqual(response.data["user"].get("username"), new_user.username)

    def test_conversation_visibility_update_for_existing_conversation(self):
        conversation = Conversations.objects.filter(
            user1=self.user, user2__username="anotheruser"
        ).first()

        conversation.IsVisibleToUser1 = False
        conversation.save()

        response = self.client.post(
            self.url, {"user2_username": "anotheruser"}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], conversation.id)

    def test_list_conversations(self):
        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 2)
        self.assertEqual(response.data[0]["user"].get("username"), "anotheruser")
        self.assertEqual(response.data[1]["user"].get("username"), "thirduser")

    def test_list_unvisible_conversations(self):
        # Make all conversations invisible to user1
        self.user.conversation_user1.all().update(IsVisibleToUser1=False)

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 0)

    def test_hide_conversation(self):
        # Make the conversation invisible from the user's view
        conversation = self.user.conversation_user1.all().first()

        Messages.objects.create(
            conversation=conversation, sender=self.user, content="Message 1"
        )
        Messages.objects.create(
            conversation=conversation, sender=self.user, content="Message 2"
        )

        response = self.client.patch(
            f"{self.url}{conversation.id}/hide/", headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conversation.refresh_from_db()
        self.assertFalse(conversation.IsVisibleToUser1)
        self.assertFalse(Messages.objects.filter(IsVisibleToUser1=True).exists())

    def test_hide_conversation_from_unauthorized_user(self):
        conversation = self.user.conversation_user1.all().first()

        create_test_user(
            username="unauthorized_user", email="unauthorized_user@example.com"
        )

        unauthorized_user_headers = get_auth_headers(
            self.client, "unauthorized_user", "Swift-1234"
        )

        response = self.client.patch(
            f"{self.url}{conversation.id}/hide/", headers=unauthorized_user_headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
