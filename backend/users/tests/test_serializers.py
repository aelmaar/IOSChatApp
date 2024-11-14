from users.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UpdateProfileSerializer,
    UpdatePasswordSerializer,
)
from django.test import TestCase
from users.models import Users
import os
from .test_helpers import create_test_image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import Mock


class RegisterSerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
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

    def test_serializer_with_valid_data(self):
        serializer = RegisterSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_validation_data(self):
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
                ("Swift-12345", "Passwords must match.")
            ],
        }

        for field, cases in test_cases.items():
            for value, error in cases:
                with self.subTest(field=field, value=value):
                    user_data_copy = self.user_data.copy()
                    user_data_copy[field] = value
                    serializer = RegisterSerializer(data=user_data_copy)
                    self.assertFalse(serializer.is_valid())
                    field = "password" if field == "confirm_password" else field
                    self.assertEqual(serializer.errors[field][0], error)

    def test_picture_field_with_valid_image_size(self):
        self.user_data["picture"] = create_test_image(1)

        serializer = RegisterSerializer(data=self.user_data)

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        user = serializer.save()
        self.assertIsNotNone(user.picture)
        self.assertIn("picture", serializer.data)

    def test_picture_field_with_invalid_image_size(self):
        self.user_data["picture"] = create_test_image(2)

        serializer = RegisterSerializer(data=self.user_data)

        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertEqual(
            serializer.errors["picture"][0], "The image size should not exceed 2MB."
        )

    def test_picture_field_with_invalid_image_format(self):
        buffer = BytesIO()
        buffer.write(os.urandom(1024))
        buffer.seek(0)

        self.user_data["picture"] = SimpleUploadedFile(
            "test_text.txt", content=buffer.read(), content_type="text/plain"
        )

        serializer = RegisterSerializer(data=self.user_data)

        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertEqual(
            serializer.errors["picture"][0],
            "Upload a valid image. The file you uploaded was either not an image or a corrupted image.",
        )

    def test_picture_field_with_empty_image_file(self):
        self.user_data["picture"] = SimpleUploadedFile(
            "test_text.jpeg", content=None, content_type="image/jpeg"
        )

        serializer = RegisterSerializer(data=self.user_data)

        self.assertFalse(serializer.is_valid(), msg=serializer.errors)
        self.assertEqual(
            serializer.errors["picture"][0],
            "The submitted file is empty.",
        )


class LoginSerializerTests(TestCase):

    def setUp(self):
        Users.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            first_name="testuser",
            last_name="testuser",
            birthdate="1990-01-01",
            password="Swift-1234",
        )

        self.credentials = {"username_or_email": "testuser", "password": "Swift-1234"}

    def test_serializer_with_valid_credentials(self):
        serializer = LoginSerializer(data=self.credentials)
        self.assertTrue(serializer.is_valid())

    def test_serializer_with_invalid_credentials(self):
        self.credentials["username_or_email"] = "differentuser"
        serializer = LoginSerializer(data=self.credentials)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["non_field_errors"][0],
            "username/email or password is incorrect",
        )


class UpdateProfileSerializerTests(TestCase):

    def setUp(self) -> None:
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "birthdate": "1990-01-01",
        }

    def test_serializer_validation_data(self):
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

                    serializer = UpdateProfileSerializer(data=user_data_copy)
                    self.assertFalse(serializer.is_valid())
                    self.assertEqual(serializer.errors[field][0], error)

    def test_serializer_with_not_oauth_profile(self):
        self.user_data["password"] = "Swift-1234"
        user = Users.objects.create_user(**self.user_data)
        self.user_data.pop("password")
        self.user_data["username"] = "differentuser"
        self.user_data["email"] = "differentuser@gmail.com"

        mock_request = Mock()
        mock_request.user = user

        serializer = UpdateProfileSerializer(
            data=self.user_data, context={"request": mock_request}
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        user = serializer.save()
        self.assertIsNotNone(user)
        self.assertEqual(serializer.data, self.user_data)

    def test_serializer_with_oauth_profile(self):
        self.user_data["password"] = "Swift-1234"
        self.user_data["IsOAuth"] = True
        user = Users.objects.create_user(**self.user_data)
        self.user_data.pop("password")
        self.user_data.pop("IsOAuth")
        self.user_data["first_name"] = "Different"
        self.user_data["last_name"] = "User"
        self.user_data["birthdate"] = "2000-02-06"

        mock_request = Mock()
        mock_request.user = user

        serializer = UpdateProfileSerializer(
            data=self.user_data, context={"request": mock_request}
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        user = serializer.save()
        self.assertIsNotNone(user)
        self.assertEqual(serializer.data, self.user_data)


class UpdatePasswordSerializerTests(TestCase):
    def setUp(self) -> None:
        self.new_password_credentials = {
            "new_password": "Swift-1234",
            "confirm_password": "Swift-1234"
        }

        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@gmail.com",
            first_name="Test",
            last_name="User",
            password="Swift-1234"
        )

        self.mock_request = Mock()
        self.mock_request.user = self.user

    def test_password_validation_data(self):
        test_cases = [
            ("Swift-1", "Password must be at least 8 characters long."),
            ("Swift-Test", "Password must contain at least one number."),
            ("swift-1234", "Password must contain at least one uppercase letter."),
            ("SWIFT-1234", "Password must contain at least one lowercase letter."),
            ("Swift1234", "Password must contain at least one special character."),
            ("Swift-12345", "Passwords must match."),
            ("Swift-1234", "New password must be different from the old one.")
        ]

        for value, error in test_cases:
            with self.subTest(value=value):
                new_password_credentials_copy = self.new_password_credentials.copy()
                new_password_credentials_copy["new_password"] = value

                serializer = UpdatePasswordSerializer(data=new_password_credentials_copy, context={'request': self.mock_request})
                self.assertFalse(serializer.is_valid())
                self.assertEqual(serializer.errors["new_password"][0], error)

    def test_valid_password_credentials(self):
        self.new_password_credentials["new_password"] = "Anouar-1234"
        self.new_password_credentials["confirm_password"] = "Anouar-1234"

        serializer = UpdatePasswordSerializer(data=self.new_password_credentials, context={'request': self.mock_request})
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        user = serializer.save()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password("Anouar-1234"))
