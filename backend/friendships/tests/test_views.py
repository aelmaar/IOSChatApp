from django.contrib.auth import get_user_model
from rest_framework import status
from chat_app.helpers import create_test_user, get_auth_headers
from users.serializers import UsersSerializer
from .test_helpers import FriendshipsTestsBase, Friendships

Users = get_user_model()


class CreateFriendshipsViewTests(FriendshipsTestsBase):

    def setUp(self) -> None:
        super().setUp()

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

    def test_with_nonexisting_friend_username(self):
        response = self.client.post(
            self.url, {"friend_username": "notexistinguser"}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "No Users matches the given query.")

    def test_with_existing_friend_username(self):

        # Create a friendship
        self.create_friendship()

        # Create another friendship to test against an existing friendship
        response = self.client.post(
            self.url,
            {"friend_username": self.another_user.username},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0], "Friendship already exists."
        )

    def test_successful_friendships_creation(self):

        response = self.client.post(
            self.url,
            {"friend_username": self.another_user.username},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["friend"],
            UsersSerializer(self.another_user).data,
        )

        self.assertEqual(response.data["status"], Friendships.PENDING)
        self.assertEqual(response.data["pending_action"], "waiting_for_response")


class ListRetrieveFriendshipsViewTests(FriendshipsTestsBase):

    def setUp(self) -> None:
        super().setUp()

        # Create friendships
        self.friendship = self.create_friendship()

    def test_view_for_unauthenticated_users(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_friendship_with_unauthorized_user(self):

        # create_test_user(
        #     username="unauthorizeduser", email="unauthorizeduser@example.com"
        # )

        headers = self.get_headers_for_unauthorized_user()

        response = self.client.get(f"{self.url}{self.friendship.id}/", headers=headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_retrieve_nonexisting_friendships(self):
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
            UsersSerializer(self.friendship.user2).data,
        )

        self.assertEqual(response.data["status"], self.friendship.status)
        self.assertEqual(response.data["pending_action"], "waiting_for_response")

    def test_list_friendships(self):
        # Create another friendship
        third_user = create_test_user(
            username="thirduser", email="thirduser@example.com"
        )

        self.create_friendship(user1=third_user, user2=self.user)
        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            response.data[0]["friend"],
            UsersSerializer(self.friendship.user2).data,
        )

        self.assertEqual(
            response.data[1]["friend"],
            UsersSerializer(third_user).data,
        )

        self.assertEqual(response.data[0]["pending_action"], "waiting_for_response")
        self.assertEqual(response.data[1]["pending_action"], "accept_or_reject")


class AcceptRejectFriendshipsViewTests(FriendshipsTestsBase):

    def setUp(self) -> None:
        super().setUp()
        # Create a friendship
        self.friendship = self.create_friendship()

        self.another_user_headers = get_auth_headers(
            self.client, "anotheruser", "Swift-1234"
        )

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

        headers = self.get_headers_for_unauthorized_user()

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

        response = self.client.patch(
            f"{self.url}{self.friendship.id}/",
            {"action": "invalid"},
            headers=self.another_user_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid action")

    def test_accept_friendships(self):

        response = self.client.patch(
            f"{self.url}{self.friendship.id}/",
            {"action": "accept"},
            headers=self.another_user_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Friendship accepted")
        self.assertEqual(
            Friendships.objects.get(id=self.friendship.id).status, Friendships.ACCEPTED
        )

    def test_reject_friendships(self):

        response = self.client.patch(
            f"{self.url}{self.friendship.id}/",
            {"action": "reject"},
            headers=self.another_user_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Friendships.DoesNotExist):
            Friendships.objects.get(id=self.friendship.id)

    def test_accept_friendships_with_nonexisting_friendships(self):

        response = self.client.patch(
            f"{self.url}100000/",
            {"action": "accept"},
            headers=self.another_user_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], "No Friendships matches the given query."
        )

    def test_accept_friendships_with_already_accepted_friendship(self):

        self.friendship.status = Friendships.ACCEPTED
        self.friendship.save()

        response = self.client.patch(
            f"{self.url}{self.friendship.id}/",
            {"action": "accept"},
            headers=self.another_user_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "The friendship has already been accepted.",
        )


class DeleteFriendshipsViewTests(FriendshipsTestsBase):

    def setUp(self) -> None:
        super().setUp()
        # Create a friendship
        self.friendship = self.create_friendship()

    def test_view_for_unauthenticated_users(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_friendships_with_nonexisting_friendships(self):
        response = self.client.delete(f"{self.url}100000/", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], "No Friendships matches the given query."
        )

    def test_delete_friendships_with_unauthorized_user(self):

        headers = self.get_headers_for_unauthorized_user()

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
