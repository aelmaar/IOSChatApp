from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Users
from unittest.mock import patch
from django.urls import reverse


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/register/"
        self.user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "birthdate": "1990-01-01",
            "picture": "https://example.com/picture.jpg",
            "password": "Swift-1234",
            "confirm_password": "Swift-1234",
        }

        Users.objects.create_user(
            username="differentuser",
            email="differentuser@example.com",
            first_name="differentuser",
            last_name="differentuser",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

    def test_register_view_with_valid_data(self):
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_view_with_multiple_invalid_data(self):
        test_cases = {
            "username": [
                ("a", "Username must be at least 5 characters long."),
                (
                    "testuser!",
                    "Username must contain only alphanumeric characters, underscores, and hyphens.",
                ),
                ("differentuser", "This username is already taken."),
            ],
            "email": [
                ("test", "Enter a valid email address."),
                ("differentuser@example.com", "This email is already taken."),
            ],
            "first_name": [
                ("a", "Name must be at least 2 characters long."),
                ("Test1", "Name must contain only alphabetic characters."),
            ],
            "last_name": [
                ("l", "Name must be at least 2 characters long."),
                ("Test2", "Name must contain only alphabetic characters."),
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
            ],
            "confirm_password": [("password", "Passwords must match.")],
        }

        for field, cases in test_cases.items():
            for value, error in cases:
                with self.subTest(field=field, value=value):
                    user_data_copy = self.user_data.copy()
                    user_data_copy[field] = value
                    response = self.client.post(self.url, user_data_copy)
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    field = "password" if field == "confirm_password" else field
                    self.assertEqual(response.data[field][0], error)


class LoginViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/login/"

        Users.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="testuser",
            last_name="testuser",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

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

    def test_view_accessible_by_unauthenticated_users_only(self):
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

    def test_oauth_42_invalid_authorization_code(self):

        for callback_url in self.callback_urls:
            with self.subTest():
                self.post_and_assert(callback_url, {"code": "invalid_code"})

    @patch("requests.post")
    def test_oauth_42_with_invalid_access_token(self, mock_post):
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
