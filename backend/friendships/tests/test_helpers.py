from chat_app.helpers import create_test_user, get_auth_headers
from django.test import TestCase
from rest_framework.test import APIClient
from friendships.models import Friendships

class FriendshipsTestsBase(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        self.url = "/api/friendships/"
        self.another_user = create_test_user(
            username="anotheruser", email="anotheruser@example.com"
        )
        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

    def create_friendship(self, user1=None, user2=None):
        user1 = user1 or self.user
        user2 = user2 or self.another_user
        return Friendships.objects.create(user1=user1, user2=user2)

    def get_headers_for_unauthorized_user(self):
        create_test_user(
            username="unauthorizeduser", email="unauthorizeduser@example.com"
        )

        headers = get_auth_headers(self.client, "unauthorizeduser", "Swift-1234")

        return headers
