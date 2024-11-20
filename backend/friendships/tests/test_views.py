from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework import status
from django.http import Http404
from friendships.models import Friendships

Users = get_user_model()


class CreateFriendshipsViewTests(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/friendships/"

        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        login_credentials = {"username_or_email": "testuser", "password": "Swift-1234"}
        login = self.client.post("/api/login/", login_credentials)
        self.headers = {"Authorization": f"Bearer {login.data.get('access')}"}

    def test_view_for_unauthenticated_users(self):
        response = self.client.post(self.url, {"friend_username": "something"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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
                response = self.client.post(
                    self.url, {"friend_username": value}, headers=self.headers
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["friend_username"][0], error)

    def test_cannot_create_self_friendships(self):
        response = self.client.post(
            self.url, {"friend_username": self.user.username}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["friend_username"][0], "You cannot be friends with yourself."
        )

    def test_with_not_existing_friend_username(self):
        response = self.client.post(
            self.url, {"friend_username": "notexistinguser"}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "No Users matches the given query.")

    def test_with_existing_friend_username(self):
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
        response = self.client.post(
            self.url, {"friend_username": another_user.username}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0], "Friendship already exists."
        )

    def test_successful_friendships_creation(self):
        another_user = Users.objects.create_user(
            username="anotheruser",
            email="anotheruser@example.com",
            first_name="Another",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        response = self.client.post(
            self.url, {"friend_username": another_user.username}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["friend"],
            {
                "username": another_user.username,
                "first_name": another_user.first_name,
                "last_name": another_user.last_name,
                "birthdate": another_user.birthdate,
                "picture": None,
            },
        )

        self.assertEqual(response.data["status"], Friendships.PENDING)
        self.assertEqual(response.data["pending_action"], "waiting_for_response")


class ListRetrieveFriendshipsViewTests(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/friendships/"

        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        # Create three users to test the friendships
        second_user = Users.objects.create_user(
            username="seconduser",
            email="seconduser@example.com",
            first_name="Second",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        third_user = Users.objects.create_user(
            username="thirduser",
            email="thirduser@example.com",
            first_name="Third",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        # Create friendships
        self.friendship = Friendships.objects.create(user1=self.user, user2=second_user)
        Friendships.objects.create(user1=third_user, user2=self.user)

        login_credentials = {"username_or_email": "testuser", "password": "Swift-1234"}
        login = self.client.post("/api/login/", login_credentials)
        self.headers = {"Authorization": f"Bearer {login.data.get('access')}"}

    def test_view_for_unauthenticated_users(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieving_friendship_with_unauthorized_user(self):
        Users.objects.create_user(
            username="unauthorizeduser",
            email="unauthorizeduser@example.com",
            first_name="Unauthorized",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        login_credentials = {
            "username_or_email": "unauthorizeduser",
            "password": "Swift-1234",
        }
        login = self.client.post("/api/login/", login_credentials)
        headers = {"Authorization": f"Bearer {login.data.get('access')}"}

        response = self.client.get(f"{self.url}{self.friendship.id}/", headers=headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_retrieving_not_existing_friendships(self):
        response = self.client.get(f"{self.url}100000/", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], "No Friendships matches the given query."
        )

    def test_retrieving_existing_friendships(self):
        response = self.client.get(
            f"{self.url}{self.friendship.id}/", headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["friend"],
            {
                "username": self.friendship.user2.username,
                "first_name": self.friendship.user2.first_name,
                "last_name": self.friendship.user2.last_name,
                "birthdate": self.friendship.user2.birthdate,
                "picture": None,
            },
        )

        self.assertEqual(response.data["status"], self.friendship.status)
        self.assertEqual(response.data["pending_action"], "waiting_for_response")

    def test_list_friendships(self):
        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            response.data[0]["friend"],
            {
                "username": self.friendship.user2.username,
                "first_name": self.friendship.user2.first_name,
                "last_name": self.friendship.user2.last_name,
                "birthdate": self.friendship.user2.birthdate,
                "picture": None,
            },
        )

        self.assertEqual(response.data[0]["pending_action"], "waiting_for_response")
        self.assertEqual(response.data[1]["pending_action"], "accept_or_reject")


class AcceptRejectFriendshipsViewTests(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/friendships/"

        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        another_user = Users.objects.create_user(
            username="anotheruser",
            email="anotheruser@example.com",
            first_name="Another",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        # Create a friendship
        self.friendship = Friendships.objects.create(
            user1=self.user, user2=another_user
        )

        login_credentials = {"username_or_email": "testuser", "password": "Swift-1234"}
        login = self.client.post("/api/login/", login_credentials)
        self.headers = {"Authorization": f"Bearer {login.data.get('access')}"}

    def test_view_for_unauthenticated_users(self):
        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_accept_reject_friendships(self):
        response = self.client.patch(
            f"{self.url}{self.friendship.id}/",
            {"action": "accept"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_accept_reject_friendships_with_unauthorized_user(self):
        Users.objects.create_user(
            username="unauthorizeduser",
            email="unauthorizeduser@example.com",
            first_name="Unauthorized",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        login_credentials = {
            "username_or_email": "unauthorizeduser",
            "password": "Swift-1234",
        }
        login = self.client.post("/api/login/", login_credentials)
        headers = {"Authorization": f"Bearer {login.data.get('access')}"}

        actions = ["accept", "reject"]

        for action in actions:
            with self.subTest():
                response = self.client.patch(
                    f"{self.url}{self.friendship.id}/",
                    {"action": action},
                    headers=headers,
                )

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(
                    response.data["detail"],
                    "You do not have permission to perform this action.",
                )

    def test_invalid_action(self):
        login_credentials = {
            "username_or_email": "anotheruser",
            "password": "Swift-1234",
        }
        login = self.client.post("/api/login/", login_credentials)
        headers = {"Authorization": f"Bearer {login.data.get('access')}"}

        response = self.client.patch(
            f"{self.url}{self.friendship.id}/", {"action": "invalid"}, headers=headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid action")

    def test_accept_friendships(self):
        login_credentials = {
            "username_or_email": "anotheruser",
            "password": "Swift-1234",
        }
        login = self.client.post("/api/login/", login_credentials)
        headers = {"Authorization": f"Bearer {login.data.get('access')}"}

        response = self.client.patch(
            f"{self.url}{self.friendship.id}/", {"action": "accept"}, headers=headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Friendship accepted")
        self.assertEqual(
            Friendships.objects.get(id=self.friendship.id).status, Friendships.ACCEPTED
        )

    def test_reject_friendships(self):
        login_credentials = {
            "username_or_email": "anotheruser",
            "password": "Swift-1234",
        }
        login = self.client.post("/api/login/", login_credentials)
        headers = {"Authorization": f"Bearer {login.data.get('access')}"}

        response = self.client.patch(
            f"{self.url}{self.friendship.id}/", {"action": "reject"}, headers=headers
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Friendships.DoesNotExist):
            Friendships.objects.get(id=self.friendship.id)

    def test_accept_friendships_with_not_existing_friendships(self):
        login_credentials = {
            "username_or_email": "anotheruser",
            "password": "Swift-1234",
        }
        login = self.client.post("/api/login/", login_credentials)
        headers = {"Authorization": f"Bearer {login.data.get('access')}"}

        response = self.client.patch(
            f"{self.url}100000/", {"action": "accept"}, headers=headers
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], "No Friendships matches the given query."
        )

    def test_accept_friendships_with_already_accepted_friendship(self):
        login_credentials = {
            "username_or_email": "anotheruser",
            "password": "Swift-1234",
        }
        login = self.client.post("/api/login/", login_credentials)
        headers = {"Authorization": f"Bearer {login.data.get('access')}"}

        self.friendship.status = Friendships.ACCEPTED
        self.friendship.save()

        response = self.client.patch(
            f"{self.url}{self.friendship.id}/", {"action": "accept"}, headers=headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "The friendship has already been accepted.",
        )


class DeleteFriendshipsViewTests(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/friendships/"

        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        another_user = Users.objects.create_user(
            username="anotheruser",
            email="anotheruser@example.com",
            first_name="Another",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        # Create a friendship
        self.friendship = Friendships.objects.create(
            user1=self.user, user2=another_user
        )

        login_credentials = {"username_or_email": "testuser", "password": "Swift-1234"}
        login = self.client.post("/api/login/", login_credentials)
        self.headers = {"Authorization": f"Bearer {login.data.get('access')}"}

    def test_view_for_unauthenticated_users(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_friendships_with_not_existing_friendships(self):
        response = self.client.delete(f"{self.url}100000/", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], "No Friendships matches the given query."
        )

    def test_delete_friendships_with_unauthorized_user(self):
        Users.objects.create_user(
            username="unauthorizeduser",
            email="unauthorizeduser@example.com",
            first_name="Unauthorized",
            last_name="User",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        login_credentials = {
            "username_or_email": "unauthorizeduser",
            "password": "Swift-1234",
        }
        login = self.client.post("/api/login/", login_credentials)
        headers = {"Authorization": f"Bearer {login.data.get('access')}"}

        response = self.client.delete(
            f"{self.url}{self.friendship.id}/", headers=headers
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_cancel_pending_with_already_accepted_friendship(self):
        self.friendship.status = Friendships.ACCEPTED
        self.friendship.save()

        response = self.client.delete(
            f"{self.url}{self.friendship.id}/",
            {"action": "cancel_pending"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "The friendship has already been accepted."
        )

    def test_cancel_pending_friendship(self):
        response = self.client.delete(
            f"{self.url}{self.friendship.id}/",
            {"action": "cancel_pending"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Friendships.DoesNotExist):
            Friendships.objects.get(id=self.friendship.id)

    def test_delete_friendship(self):
        response = self.client.delete(
            f"{self.url}{self.friendship.id}/", headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Friendships.DoesNotExist):
            Friendships.objects.get(id=self.friendship.id)
