from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Users, Blacklist
from unittest.mock import patch
from django.urls import reverse
from .test_helpers import create_test_image, delete_test_images
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from users.serializers import UsersSerializer
from chat_app.helpers import get_auth_headers, create_test_user
from friendships.models import Friendships
from chats.models import Conversations
import os


class RegisterViewTests(TestCase):
    """
    Test suite for the RegisterView.

    Test cases:
    - `test_register_view_with_authenticated_user`: Tests the view with an authenticated user.
    - `test_register_view_with_valid_data`: Tests the view with valid user data.
    - `test_register_view_with_invalid_data`: Tests the view with various invalid user data scenarios.
    - `test_register_view_with_valid_picture`: Tests the view with a valid picture field.
    - `test_register_view_with_invalid_picture`: Tests the view with various invalid picture field scenarios.

    Methods:
    - `setUp`: Initializes common test data and creates a user in the database to test for unique constraints.
    - `tearDown`: Cleans up any test images created during the tests.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/register/"
        self.user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "birthdate": "1990-01-01",
            "password": "Swift-1234",
            "confirm_password": "Swift-1234",
        }

        create_test_user(username="differentuser", email="differentuser@example.com")

        self.test_images = []

    def tearDown(self) -> None:
        # Delete test images
        delete_test_images(self.test_images)

    def test_register_view_with_authenticated_user(self):
        user = create_test_user("testuser", "testuser@example.com")

        headers = get_auth_headers(self.client, "testuser", "Swift-1234")

        response = self.client.post(self.url, self.user_data, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )

    def test_register_view_with_valid_data(self):
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_view_with_invalid_data(self):
        test_cases = {
            "username": [
                ("", "This field may not be blank."),
                ("a", "Username must be at least 5 characters long."),
                (
                    "testuser!",
                    "Username must contain only alphanumeric characters, underscores, and hyphens.",
                ),
                ("differentuser", "This username is already taken."),
                (
                    "anouarelmaaroufiejfdjkjldioafiejfajkdvnakjsdvijefij",
                    "Ensure this field has no more than 30 characters.",
                ),
            ],
            "email": [
                ("", "This field may not be blank."),
                ("test", "Enter a valid email address."),
                ("differentuser@example.com", "This email is already taken."),
                (
                    "anouarelmaaroufiejfdjkjldioafiejfajkdvnakjsdvijefijarenvjfnrviaunreuhfairuehfuireafraefnrd@gmail.comm",
                    "Ensure this field has no more than 100 characters.",
                ),
            ],
            "first_name": [
                ("", "This field may not be blank."),
                ("a", "Name must be at least 2 characters long."),
                ("Test1", "Name must contain only alphabetic characters."),
                (
                    "Anouarefjaiofjdijfiaoejfiojaeiojfioaeajwfiojeoifaewf",
                    "Ensure this field has no more than 30 characters.",
                ),
            ],
            "last_name": [
                ("", "This field may not be blank."),
                ("l", "Name must be at least 2 characters long."),
                ("Test2", "Name must contain only alphabetic characters."),
                (
                    "El Maaroufifeajfoiejafdsafeuaifhuerhafuorhfuihraeuihgriahah",
                    "Ensure this field has no more than 30 characters.",
                ),
            ],
            "birthdate": [
                (
                    "1990-01-01T00:00:00",
                    "Date has wrong format. Use one of these formats instead: YYYY-MM-DD.",
                ),
                ("1899-01-01", "Year must be greater than 1900."),
            ],
            "password": [
                ("Swift-1", "Password must be at least 8 characters long."),
                ("Swift-Test", "Password must contain at least one number."),
                ("swift-1234", "Password must contain at least one uppercase letter."),
                ("SWIFT-1234", "Password must contain at least one lowercase letter."),
                ("Swift1234", "Password must contain at least one special character."),
                ("Swift-12345", "Passwords must match."),
            ],
        }

        for field, cases in test_cases.items():
            for value, error in cases:
                with self.subTest(field=field, value=value):
                    user_data_copy = self.user_data.copy()
                    user_data_copy[field] = value
                    response = self.client.post(self.url, user_data_copy)
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertEqual(response.data[field][0], error)

    def test_register_view_with_valid_picture(self):
        picture = create_test_image(1)
        self.user_data["picture"] = picture

        response = self.client.post(self.url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("picture", response.data)
        self.assertTrue(response.data["picture"].startswith("http"))

        self.test_images.append(picture.name)

    def test_register_view_with_invalid_picture(self):
        buffer = BytesIO()
        buffer.write(os.urandom(1024))
        buffer.seek(0)

        test_cases = [
            (create_test_image(2), "The image size should not exceed 2MB."),
            (
                SimpleUploadedFile(
                    "test_text.txt", content=buffer.read(), content_type="text/plain"
                ),
                "Upload a valid image. The file you uploaded was either not an image or a corrupted image.",
            ),
            (
                SimpleUploadedFile(
                    "test_text.jpeg", content=None, content_type="image/jpeg"
                ),
                "The submitted file is empty.",
            ),
        ]

        for value, error in test_cases:
            with self.subTest():
                user_data_copy = self.user_data.copy()
                user_data_copy["picture"] = value

                response = self.client.post(self.url, user_data_copy)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["picture"][0], error)

                self.test_images.append(value.name)


class LoginViewTests(TestCase):
    """
    Test suite for the LoginView.

    Test cases:
    - `test_view_with_valid_credentials`: Tests the view with valid login credentials.
    - `test_view_with_invalid_credentials`: Tests the view with invalid login credentials.
    - `test_view_for_unauthenticated_users_only`: Tests that the view is accessible only by unauthenticated users.

    Methods:
    - `setUp`: Sets up a test user and credentials for the tests.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/login/"

        create_test_user("testuser", "testuser@example.com")

        self.credentials = {"username_or_email": "testuser", "password": "Swift-1234"}

    def test_view_with_valid_credentials(self):
        response = self.client.post(self.url, self.credentials)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login successful")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_view_with_invalid_credentials(self):
        self.credentials["username_or_email"] = "differentuser"
        response = self.client.post(self.url, self.credentials)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0],
            "username/email or password is incorrect",
        )

    def test_view_for_unauthenticated_users_only(self):
        authenticate = self.client.post(self.url, self.credentials)

        response = self.client.post(
            self.url,
            self.credentials,
            headers={"Authorization": f"Bearer {authenticate.data['access']}"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )


class OAuthCallbackViewTests(TestCase):
    """
    Test suite for the OAuthCallbackView.

    Test cases:
    - `test_oauth_callback_success`: Tests the OAuth callback with valid authorization code. Mocks the requests to exchange the authorization code for an access token and to retrieve user info.
    - `test_oauth_callback_with_empty_authorization_code`: Tests the OAuth callback with empty authorization code.
    - `test_oauth_42_invalid_authorization_code`: Tests the OAuth callback with invalid authorization code.
    - `test_oauth_42_with_invalid_access_token`: Tests the OAuth callback with invalid access token. Mocks the request to exchange the authorization code for an invalid access token.

    Methods:
    - `setUp`: Sets up the initial data for the tests.
    - `post_and_assert`: Helper method to post data to the callback URL and assert the response.
    """

    def setUp(self):

        self.client = APIClient()
        self.google_callback_url = reverse("oauth-google-callback")
        self.callback_42_url = reverse("oauth-42-callback")
        self.callback_urls = [
            reverse("oauth-google-callback"),
            reverse("oauth-42-callback"),
        ]

        self.userinfos = [
            {
                "id": "815456",
                "email": "test@example.com",
                "given_name": "Test",
                "family_name": "User",
                "picture": "https://example.com/test.png",
            },
            {
                "id": "815456",
                "email": "test@example.com",
                "login": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "image": {"versions": {"medium": "https://example.com/test.png"}},
            },
        ]

    @patch("requests.post")
    @patch("requests.get")
    def test_oauth_callback_success(self, mock_get, mock_post):
        # Pretend Exchanging authorization code for an access token
        mock_post.return_value.json.return_value = {"access_token": "mock_access_token"}

        for index, userinfo in enumerate(self.userinfos):
            with self.subTest():
                # Pretend retrieving the actual 42 user info and GET response is successful
                mock_get.return_value.ok = True
                mock_get.return_value.json.return_value = userinfo

                response = self.client.post(
                    self.callback_urls[index], {"code": "valid_code"}
                )

                user = Users.objects.filter(email=userinfo.get("email")).first()
                self.assertIsNotNone(user)

                response_data = response.json()
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn("access", response_data)
                self.assertIn("refresh", response_data)

    def test_oauth_callback_with_empty_authorization_code(self):

        for callback_url in self.callback_urls:
            with self.subTest():
                self.post_and_assert(callback_url, {})

    def test_oauth_callback_with_invalid_authorization_code(self):

        for callback_url in self.callback_urls:
            with self.subTest():
                self.post_and_assert(callback_url, {"code": "invalid_code"})

    @patch("requests.post")
    def test_oauth_callback_with_invalid_access_token(self, mock_post):
        mock_post.return_value.json.return_value = {
            "access_token": "mock_invalid_access_token"
        }

        for callback_url in self.callback_urls:
            with self.subTest():
                self.post_and_assert(callback_url, {"code": "valid_code"})

    def post_and_assert(self, callback_url, data):
        response = self.client.post(callback_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_message", response.json())


class UpdateProfileViewTests(TestCase):
    """
    Test suite for the UpdateProfileView.

    Test cases:
    - `test_view_with_invalid_data`: Tests the view with various invalid data inputs.
    - `test_view_for_unauthorized_users`: Tests that the view is not accessible by unauthorized users.
    - `test_update_non_oauth_profile`: Tests updating a non-OAuth user profile.
    - `test_update_oauth_profile`: Tests updating an OAuth user profile.

    Methods:
    - `setUp`: Sets up the initial user data and authentication for the tests.
    """

    def setUp(self) -> None:
        self.url = "/api/update-profile/"
        self.client = APIClient()
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "birthdate": "1990-01-01",
        }

        self.user_data["password"] = "Swift-1234"
        self.user = Users.objects.create_user(**self.user_data)
        self.user_data.pop("password")

        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

    def test_view_with_invalid_data(self):
        test_cases = {
            "username": [
                ("", "This field may not be blank."),
                ("a", "Username must be at least 5 characters long."),
                (
                    "testuser!",
                    "Username must contain only alphanumeric characters, underscores, and hyphens.",
                ),
                (
                    "anouarelmaaroufiejfdjkjldioafiejfajkdvnakjsdvijefij",
                    "Ensure this field has no more than 30 characters.",
                ),
            ],
            "email": [
                ("", "This field may not be blank."),
                ("test", "Enter a valid email address."),
                (
                    "anouarelmaaroufiejfdjkjldioafiejfajkdvnakjsdvijefijarenvjfnrviaunreuhfairuehfuireafraefnrd@gmail.comm",
                    "Ensure this field has no more than 100 characters.",
                ),
            ],
            "first_name": [
                ("", "This field may not be blank."),
                ("a", "Name must be at least 2 characters long."),
                ("Test1", "Name must contain only alphabetic characters."),
                (
                    "Anouarefjaiofjdijfiaoejfiojaeiojfioaeajwfiojeoifaewf",
                    "Ensure this field has no more than 30 characters.",
                ),
            ],
            "last_name": [
                ("", "This field may not be blank."),
                ("l", "Name must be at least 2 characters long."),
                ("Test2", "Name must contain only alphabetic characters."),
                (
                    "El Maaroufifeajfoiejafdsafeuaifhuerhafuorhfuihraeuihgriahah",
                    "Ensure this field has no more than 30 characters.",
                ),
            ],
            "birthdate": [
                (
                    "1990-01-01T00:00:00",
                    "Date has wrong format. Use one of these formats instead: YYYY-MM-DD.",
                ),
                ("1899-01-01", "Year must be greater than 1900."),
            ],
        }

        for field, cases in test_cases.items():
            for value, error in cases:
                with self.subTest(field=field, value=value):
                    user_data_copy = self.user_data.copy()
                    user_data_copy[field] = value

                    response = self.client.patch(
                        self.url, user_data_copy, headers=self.headers
                    )
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertEqual(response.data[field][0], error)

    def test_view_for_unauthorized_users(self):
        response = self.client.patch(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_update_non_oauth_profile(self):
        # Update the user data
        self.user_data["username"] = "differentuser"
        self.user_data["email"] = "differentuser@example.com"
        # Update the request with the new data
        response = self.client.patch(self.url, self.user_data, headers=self.headers)
        # Assert the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.user_data)

    def test_update_oauth_profile(self):
        self.user.IsOAuth = True
        self.user.save()

        # Update the user data
        self.user_data["first_name"] = "Different"
        self.user_data["last_name"] = "User"
        self.user_data["birthdate"] = "2000-02-06"

        # Update the request with the new data
        response = self.client.patch(self.url, self.user_data, headers=self.headers)
        # Assert the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.user_data)

        # Assert the user data in the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, self.user_data["first_name"])
        self.assertEqual(self.user.last_name, self.user_data["last_name"])
        self.assertEqual(str(self.user.birthdate), self.user_data["birthdate"])


class UpdatePasswordViewTests(TestCase):
    """
    Test suite for the UpdatePasswordView.

    Test cases:
    - `test_view_for_unauthorized_users`: Tests that the view is not accessible by unauthorized users.
    - `test_view_with_invalid_password_credentials`: Tests the view with various invalid password scenarios.
    - `test_successful_password_change`: Tests a successful password change scenario.

    Methods:
    - `setUp`: Sets up the initial data for the tests, including creating a user and mock request.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/update-password/"

        self.new_password_credentials = {
            "new_password": "Swift-1234",
            "confirm_password": "Swift-1234",
        }

        self.user = create_test_user("testuser", "testuser@example.com")

        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

    def test_view_for_unauthorized_users(self):
        self.new_password_credentials["new_password"] = "Anouar-1234"
        self.new_password_credentials["confirm_password"] = "Anouar-1234"

        response = self.client.patch(self.url, self.new_password_credentials)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_view_with_invalid_password_credentials(self):
        test_cases = [
            ("Swift-1", "Password must be at least 8 characters long."),
            ("Swift-Test", "Password must contain at least one number."),
            ("swift-1234", "Password must contain at least one uppercase letter."),
            ("SWIFT-1234", "Password must contain at least one lowercase letter."),
            ("Swift1234", "Password must contain at least one special character."),
            ("Swift-12345", "Passwords must match."),
            ("Swift-1234", "New password must be different from the old one."),
        ]

        for value, error in test_cases:
            with self.subTest(value=value):
                new_password_credentials_copy = self.new_password_credentials.copy()
                new_password_credentials_copy["new_password"] = value

                response = self.client.patch(
                    self.url, new_password_credentials_copy, headers=self.headers
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["new_password"][0], error)

    def test_successful_password_change(self):
        self.new_password_credentials["new_password"] = "Anouar-1234"
        self.new_password_credentials["confirm_password"] = "Anouar-1234"

        response = self.client.patch(
            self.url, self.new_password_credentials, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)


class UpdatePictureViewTests(TestCase):
    """
    Test suite for the UpdatePictureView.

    Test cases:
    - `test_view_for_unauthorized_users`: Tests that the view is not accessible by unauthorized users.
    - `test_view_with_invalid_image_data`: Tests the view with various invalid image data scenarios.
    - `test_view_with_valid_new_picture`: Tests the view with valid new picture data.

    Methods:
    - `setUp`: Sets up the test environment by creating a test user and initializing test data.
    - `tearDown`: Cleans up the test environment by deleting test images after each test.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/update-picture/"

        self.user = create_test_user("testuser", "testuser@example.com")

        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

        self.new_picture_data = {}
        self.test_images = []

    def tearDown(self) -> None:
        # Delete test images
        delete_test_images(self.test_images)

    def test_view_for_unauthorized_users(self):
        new_picture = create_test_image(1)

        response = self.client.patch(self.url, {"new_picture": new_picture})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

        self.test_images.append(new_picture.name)

    def test_view_with_invalid_image_data(self):
        buffer = BytesIO()
        buffer.write(os.urandom(1024))
        buffer.seek(0)

        test_cases = [
            (create_test_image(2), "The image size should not exceed 2MB."),
            (
                SimpleUploadedFile(
                    "test_text.txt", content=buffer.read(), content_type="text/plain"
                ),
                "Upload a valid image. The file you uploaded was either not an image or a corrupted image.",
            ),
            (
                SimpleUploadedFile(
                    "test_text.jpeg", content=None, content_type="image/jpeg"
                ),
                "The submitted file is empty.",
            ),
        ]

        for value, error in test_cases:
            with self.subTest():
                response = self.client.patch(
                    self.url, {"new_picture": value}, headers=self.headers
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["new_picture"][0], error)

                self.test_images.append(value.name)

    def test_view_with_valid_new_picture(self):
        new_picture = create_test_image(1)

        response = self.client.patch(
            self.url, {"new_picture": new_picture}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("new_picture", response.data)
        self.assertTrue(response.data["new_picture"].startswith("http"))

        self.test_images.append(new_picture.name)


class DeletePictureViewTests(TestCase):
    """
    Test suite for the DeletePictureView.

    Test cases:
    - `test_view_for_unauthenticated_users`: Tests that the view is not accessible by unauthenticated users.
    - `test_view_with_no_picture_to_delete`: Tests the view when there is no picture to delete.
    - `test_view_with_picture_to_delete`: Tests the view when there is a picture to delete.

    Methods:
    - `setUp`: Sets up the test environment by creating a test user and initializing test data.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/delete-picture/"

        self.user = create_test_user("testuser", "testuser@example.com")

        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

    def test_view_for_unauthenticated_users(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_view_with_no_picture_to_delete(self):
        response = self.client.delete(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_view_with_picture_to_delete(self):
        self.user.picture = create_test_image(1)
        self.user.save()

        response = self.client.delete(self.url, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertEqual(self.user.picture.name, "")


class BlacklistViewTests(TestCase):
    """
    Test suite for the BlacklistView.

    Test cases:
    - `test_view_for_unauthenticated_users`: Tests that the view is not accessible by unauthenticated users.
    - `test_blocked_username_with_invalid_data`: Tests the view with various invalid blocked username scenarios.
    - `test_cannot_block_or_unblock_oneself`: Tests that a user cannot block or unblock oneself.
    - `test_with_nonexisting_blocked_username`: Tests the view with a not existing blocked username.
    - `test_with_an_already_blocked_user`: Tests the view with an already blocked user.
    - `test_blocking_a_user`: Tests blocking a user.
    - `test_listing_nonexisting_blocked_users`: Tests listing not existing blocked users.
    - `test_listing_blocked_users`: Tests listing blocked users.
    - `test_unblock_none_blocked_user`: Tests unblocking a none blocked user.
    - `test_unblock_nonexisting_blocked_user`: Tests unblocking a not existing blocked user.
    - `test_unblock_a_blocked_user`: Tests unblocking a blocked user.

    Methods:
    - `setUp`: Sets up the test environment by creating a test user and initializing test data.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/blacklist/"

        self.user = create_test_user("testuser", "testuser@example.com")
        self.second_user = create_test_user("seconduser", "seconduser@example.com")
        self.third_user = create_test_user("thirduser", "thirduser@example.com")
        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

    def test_view_for_unauthenticated_users(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_block_usernames(self):
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
                    self.url, {"blocked_username": value}, headers=self.headers
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["blocked_username"][0], error)

    def test_block_self_forbidden(self):
        response = self.client.post(
            self.url, {"blocked_username": self.user.username}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["blocked_username"][0],
            "You cannot block or unblock yourself.",
        )

    def test_block_nonexistent_user(self):
        response = self.client.post(
            self.url, {"blocked_username": "notexistinguser"}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "No Users matches the given query.")

    def test_block_already_blocked_user(self):
        Blacklist.objects.create(user=self.user, blocked_user=self.second_user)

        response = self.client.post(
            self.url,
            {"blocked_username": self.second_user.username},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0], "User is already blocked."
        )

    def test_block_user_success(self):
        conversation = Conversations.objects.create(
            user1=self.user, user2=self.second_user
        )

        friendship = Friendships.objects.create(user1=self.user, user2=self.second_user)

        response = self.client.post(
            self.url,
            {"blocked_username": self.second_user.username},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["blocked_user"].get("username"), self.second_user.username
        )
        # Check that Friendship does not exist after blocking a user
        # and conversation is blocked for the auth user
        conversation.refresh_from_db()
        with self.assertRaises(Friendships.DoesNotExist):
            Friendships.objects.get(pk=friendship.id)
        self.assertTrue(conversation.IsBlockedByUser1)

    def test_list_empty_blocks(self):

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 0)

    def test_list_blocked_users(self):

        Blacklist.objects.create(user=self.user, blocked_user=self.second_user)
        Blacklist.objects.create(user=self.user, blocked_user=self.third_user)

        response = self.client.get(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 2)
        self.assertEqual(response.data[0]["blocked_user"].get("username"), "seconduser")
        self.assertEqual(response.data[1]["blocked_user"].get("username"), "thirduser")

    def test_unblock_without_username(self):
        response = self.client.delete(self.url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unblock_nonexistent_user(self):
        response = self.client.delete(
            self.url, {"blocked_username": "notexistinguser"}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unblock_user_success(self):
        conversation = Conversations.objects.create(
            user1=self.user, user2=self.second_user
        )

        Blacklist.objects.create(user=self.user, blocked_user=self.second_user)

        response = self.client.delete(
            self.url, {"blocked_username": "seconduser"}, headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Blacklist.DoesNotExist):
            Blacklist.objects.get(user=self.user, blocked_user=self.second_user)

        conversation.refresh_from_db()
        self.assertFalse(conversation.IsBlockedByUser1)


class UsersSearchViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/users/search/"
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

        # Create multiple users
        create_test_user(
            username="seconduser", email="seconduser@example.com", first_name="Second"
        )
        create_test_user(
            username="thirduser", email="thirduser@example.com", first_name="Third"
        )

    def test_view_with_nonauthenticated_users(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_nonexistent_user(self):
        response = self.client.get(
            f"{self.url}?q=nonexistentuser", headers=self.headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 0)

    def test_success_users_search(self):

        response = self.client.get(f"{self.url}?q=user", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 3)

    def test_search_blocked_users(self):
        second_user = Users.objects.get(username="seconduser")
        third_user = Users.objects.get(username="thirduser")

        # Create some blocked user
        Blacklist.objects.create(user=self.user, blocked_user=second_user)
        Blacklist.objects.create(user=self.user, blocked_user=third_user)

        response = self.client.get(f"{self.url}?q=user", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only the user auth is included
        self.assertTrue(len(response.data) == 1)
        self.assertEqual(response.data[0]["username"], self.user.username)

    def test_search_users_with_limit_10(self):
        # Create 10 more users
        for i in range(10):
            create_test_user(username=f"testuser{i}", email=f"testuser{i}@example.com")

        response = self.client.get(f"{self.url}?q=user", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 10)


class UserProfileViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/users/"
        self.user = create_test_user(username="testuser", email="testuser@example.com")
        self.headers = get_auth_headers(self.client, "testuser", "Swift-1234")

    def test_view_with_nonauthenticated_users(self):
        response = self.client.get(f"{self.url}testuser/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_nonexistent_profile_user(self):

        response = self.client.get(f"{self.url}nonexistentuser/", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_success_retrieve_profile_user(self):
        response = self.client.get(f"{self.url}testuser/", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_retrieve_blocked_profile_user(self):
        second_user = create_test_user(
            username="seconduser", email="seconduser@example.com", first_name="Second"
        )

        Blacklist.objects.create(user=self.user, blocked_user=second_user)

        response = self.client.get(f"{self.url}seconduser/", headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "User not found.")


class DeleteAccountViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/delete-account/"

    def test_view_for_non_authenticated_users(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_user_account(self):
        user = create_test_user(username="testuser", email="testuser@example.com")
        headers = get_auth_headers(self.client, "testuser", "Swift-1234")

        response = self.client.delete(self.url, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Users.DoesNotExist):
            Users.objects.get(pk=user.id)
