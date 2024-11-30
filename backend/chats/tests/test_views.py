from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from chats.models import Conversations, Messages
from chat_app.helpers import create_test_user, get_auth_headers


class ConversationsViewTests(TestCase):
    """
    Test suite for the ConversationsView.

    Test cases:
    - test_view_with_nonauthenticated_users: Tests authentication requirement
    - test_user2_username_field_with_invalid_data: Tests username validation
    - test_conversation_creation_with_nonexistent_user: Tests creation with invalid user
    - test_success_conversation_creation: Tests successful conversation creation
    - test_conversation_visibility_update: Tests visibility updates
    - test_list_conversations: Tests conversation listing
    - test_list_unvisible_conversations: Tests invisible conversation handling
    - test_hide_conversation: Tests conversation hiding
    - test_hide_conversation_from_unauthorized_user: Tests unauthorized access

    Methods:
    - setUp: Initializes test data and users
    """

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
        """Make the conversation invisible from the user's view and hide it's messages"""
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

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
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


class MessagesViewTests(TestCase):
    """
    Test suite for the MessagesView.

    Test cases:
    - test_invalidate_message_content: Tests message content validation
    - test_view_with_nonauthenticated_users: Tests authentication requirement
    - test_endpoints_for_nonexistent_conversation: Tests nonexistent conversation handling
    - test_endpoints_for_unauthorized_user: Tests unauthorized access
    - test_success_message_creation: Tests successful message creation
    - test_list_invisible_messages: Tests invisible message handling
    - test_success_list_messages: Tests message listing
    - test_success_clear_messages: Tests message clearing
    - test_mark_messages_as_read: Tests marking messages as read
    - test_clear_message_with_invalid_action: Tests invalid action handling

    Methods:
    - setUp: Initializes test conversation and messages
    """

    def setUp(self):
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        self.another_user = create_test_user(
            username="anotheruser", email="anotheruser@example.com"
        )
        self.client = APIClient()
        self.url = "/api/conversations/"
        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

        self.conversation = Conversations.objects.create(
            user1=self.user, user2=self.another_user
        )

        # Create two messages
        Messages.objects.create(
            conversation=self.conversation, sender=self.user, content="Test message 1"
        )
        Messages.objects.create(
            conversation=self.conversation, sender=self.user, content="Test message 2"
        )

    # Test cases when creating message
    def test_invalidate_message_content(self):
        test_cases = [
            {
                "input": None,
                "error": "This field may not be null.",
            },
            {
                "input": "",
                "error": "This field may not be blank.",
            },
            {
                "input": " ",
                "error": "This field may not be blank.",
            },
            {
                "input": {"key": "value"},
                "error": "Not a valid string.",
            },
        ]

        for case in test_cases:
            with self.subTest():
                response = self.client.post(
                    f"{self.url}{self.conversation.id}/messages/",
                    {"content": case["input"]},
                    headers=self.headers,
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["content"][0], case["error"])

    def test_view_with_nonauthenticated_users(self):
        response = self.client.post(
            f"{self.url}{self.conversation.id}/messages/",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoints_for_nonexistent_conversation(self):
        methods = [self.client.get, self.client.post, self.client.patch]

        for method in methods:
            with self.subTest():
                response = method(
                    f"{self.url}1000/messages/",
                    headers=self.headers,
                )

                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_endpoints_for_unauthorized_user(self):
        create_test_user(
            username="unauthrorizeduser", email="unauthrorizeduser@example.com"
        )

        unauthorized_user_headers = get_auth_headers(
            self.client, "unauthrorizeduser", "Swift-1234"
        )

        methods = [self.client.get, self.client.post, self.client.patch]

        for method in methods:
            with self.subTest():
                response = method(
                    f"{self.url}{self.conversation.id}/messages/",
                    headers=unauthorized_user_headers,
                )

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_message_creation_with_blocked_user_on_conversation(self):
        self.conversation.IsBlockedByUser1 = True
        self.conversation.save()

        response = self.client.post(
            f"{self.url}{self.conversation.id}/messages/",
            {"content": "Hello world"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0],
            "You cannot create a converation with this user.",
        )

    def test_success_message_creation(self):
        response = self.client.post(
            f"{self.url}{self.conversation.id}/messages/",
            {"content": "Hello world"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sender"], self.user.username)
        self.assertEqual(response.data["conversation"], self.conversation.id)

    def test_list_invisible_messages(self):
        self.conversation.messages_set.filter(IsVisibleToUser1=True).update(
            IsVisibleToUser1=False
        )

        response = self.client.get(
            f"{self.url}{self.conversation.id}/messages/",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 0)

    def test_success_list_messages(self):
        # Test creating other messages by anotheruser
        # To mark messages as read by testuser
        Messages.objects.create(
            conversation=self.conversation,
            sender=self.another_user,
            content="Test message 3",
        )
        Messages.objects.create(
            conversation=self.conversation,
            sender=self.another_user,
            content="Test message 4",
        )

        response = self.client.get(
            f"{self.url}{self.conversation.id}/messages/",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 4)
        self.assertTrue(
            self.conversation.messages_set.filter(IsReadByReceiver=True).count() == 2
        )

    def test_success_clear_messages(self):
        response = self.client.patch(
            f"{self.url}{self.conversation.id}/messages/",
            {"action": "clear_chat"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(
            self.conversation.messages_set.filter(IsVisibleToUser1=False).count() == 2
        )

    def test_mark_messages_as_read(self):
        another_user_headers = get_auth_headers(
            self.client, "anotheruser", "Swift-1234"
        )

        response = self.client.patch(
            f"{self.url}{self.conversation.id}/messages/",
            {"action": "read_messages"},
            headers=another_user_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(
            self.conversation.messages_set.filter(IsReadByReceiver=True).count() == 2
        )

    def test_clear_message_with_invalid_action(self):
        response = self.client.patch(
            f"{self.url}{self.conversation.id}/messages/",
            {"action": "invalid"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid action.")
