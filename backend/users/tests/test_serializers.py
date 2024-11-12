from users.serializers import RegisterSerializer, LoginSerializer
from django.test import TestCase
from users.models import Users
import os
from .test_helpers import create_test_image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile


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
