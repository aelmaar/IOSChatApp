from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Users
from unittest.mock import patch
from django.urls import reverse
from .test_helpers import create_test_image, delete_test_images
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
import os


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

        self.test_images = []

    def tearDown(self) -> None:
        # Delete test images
        delete_test_images(self.test_images)

    def test_register_view_with_valid_data(self):
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_view_with_multiple_invalid_data(self):
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

    def test_register_view_with_valid_picture_image_size(self):
        picture = create_test_image(1)
        self.user_data["picture"] = picture

        response = self.client.post(self.url, self.user_data)


        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("picture", response.data)
        self.assertTrue(response.data["picture"].startswith("http"))

        self.test_images.append(picture.name)

    def test_register_view_with_invalid_image_data(self):
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


class UpdateProfileViewTests(TestCase):

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

        self.login_credentials = {
            "username_or_email": "testuser",
            "password": "Swift-1234",
        }

        self.user_data["password"] = "Swift-1234"
        self.user = Users.objects.create_user(**self.user_data)
        self.user_data.pop("password")
        # Authenticated the user
        login = self.client.post("/api/login/", self.login_credentials)
        self.headers = {"Authorization": f"Bearer {login.data.get("access")}"}

    def test_view_validation_data(self):
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
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/update-password/"

        self.new_password_credentials = {
            "new_password": "Swift-1234",
            "confirm_password": "Swift-1234",
        }

        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@gmail.com",
            first_name="Test",
            last_name="User",
            password="Swift-1234",
        )

        self.login = self.client.post(
            "/api/login/", {"username_or_email": "testuser", "password": "Swift-1234"}
        )
        self.headers = {"Authorization": f"Bearer {self.login.data.get("access")}"}

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

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/update-picture/"

        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@gmail.com",
            first_name="Test",
            last_name="User",
            password="Swift-1234",
        )

        self.login = self.client.post(
            "/api/login/", {"username_or_email": "testuser", "password": "Swift-1234"}
        )
        self.headers = {"Authorization": f"Bearer {self.login.data.get("access")}"}

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

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/delete-picture/"

        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            password="Swift-1234",
        )

        self.login = self.client.post(
            "/api/login/", {"username_or_email": "testuser", "password": "Swift-1234"}
        )
        self.headers = {"Authorization": f"Bearer {self.login.data.get('access')}"}
    
    def test_view_for_unauthorized_users(self):
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
        self.assertEqual(self.user.picture.name, '')
