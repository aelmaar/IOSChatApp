from users.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UpdateProfileSerializer,
    UpdatePasswordSerializer,
    UpdatePictureSerializer,
)
from django.test import TestCase
from users.models import Users
import os
from .test_helpers import create_test_image, delete_test_images
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import Mock


class RegisterSerializerTests(TestCase):
    """
    Test suite for the RegisterSerializer.

    Test cases:
    - `test_serializer_with_valid_data`: Tests the serializer with valid user data.
    - `test_serializer_with_invalid_data`: Tests the serializer with various invalid user data scenarios.
    - `test_valid_picture_field`: Tests the serializer with a valid picture field.
    - `test_invalid_picture_field`: Tests the serializer with various invalid picture field scenarios.

    Methods:
    - `setUp`: Initializes common test data and creates a user in the database to test for unique constraints.
    - `tearDown`: Cleans up any test images created during the tests.
    """
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

        self.test_images = []

    def tearDown(self) -> None:
        # Delete test images
        delete_test_images(self.test_images)

    def test_serializer_with_valid_data(self):
        serializer = RegisterSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_with_invalid_data(self):
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
                    serializer = RegisterSerializer(data=user_data_copy)
                    self.assertFalse(serializer.is_valid())
                    self.assertEqual(serializer.errors[field][0], error)

    def test_valid_picture_field(self):
        picture = create_test_image(1)
        self.user_data["picture"] = picture

        serializer = RegisterSerializer(data=self.user_data)


        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        user = serializer.save()
        self.assertIsNotNone(user.picture)
        self.assertIn("picture", serializer.data)

        self.test_images.append(picture.name)

    def test_invalid_picture_field(self):
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

                serializer = RegisterSerializer(data=user_data_copy)


                self.assertFalse(serializer.is_valid(), msg=serializer.errors)
                self.assertEqual(serializer.errors["picture"][0], error)

                self.test_images.append(value.name)

class LoginSerializerTests(TestCase):
    """
    Test suite for the LoginSerializer.

    Test cases:
    - `test_serializer_with_valid_credentials`: Tests that the serializer is valid with correct credentials.
    - `test_serializer_with_invalid_credentials`: Tests that the serializer is invalid with incorrect credentials.

    Methods:
    - `setUp`: Sets up a test user and credentials for the tests.
    """

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
    """
    Test suite for the UpdateProfileSerializer.

    Test cases:
    - `test_serializer_with_invalid_data`: Tests the serializer with various invalid data inputs.
    - `test_valid_non_oauth_profile`: Tests the serializer with valid non-OAuth user data.
    - `test_valid_oauth_profile`: Tests the serializer with valid OAuth user data.

    Methods:
    - `setUp`: Sets up the initial user data for the tests.
    """

    def setUp(self) -> None:
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "birthdate": "1990-01-01",
        }

    def test_serializer_with_invalid_data(self):
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

    def test_valid_non_oauth_profile(self):
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

    def test_valid_oauth_profile(self):
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
    """
    Test suite for the UpdatePasswordSerializer.

    Test cases:
    - `test_invalid_password_data`: Tests various invalid password scenarios.
    - `test_valid_password_credentials`: Tests a valid password change scenario.

    Methods:
    - `setUp`: Sets up the initial data for the tests, including creating a user and mock request.
    """
    def setUp(self) -> None:
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

        self.mock_request = Mock()
        self.mock_request.user = self.user

    def test_invalid_password_data(self):
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

                serializer = UpdatePasswordSerializer(
                    data=new_password_credentials_copy,
                    context={"request": self.mock_request},
                )
                self.assertFalse(serializer.is_valid())
                self.assertEqual(serializer.errors["new_password"][0], error)

    def test_valid_password_credentials(self):
        self.new_password_credentials["new_password"] = "Anouar-1234"
        self.new_password_credentials["confirm_password"] = "Anouar-1234"

        serializer = UpdatePasswordSerializer(
            data=self.new_password_credentials, context={"request": self.mock_request}
        )
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        user = serializer.save()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password("Anouar-1234"))


class UpdatePictureSerializerTests(TestCase):
    """
    Test suite for the UpdatePictureSerializer.

    Test cases:
    - `test_invalid_new_picture_field`: Tests the serializer with invalid new picture data.
    - `test_valid_new_picture_field`: Tests the serializer with valid new picture data.

    Methods:
    - `setUp`: Sets up the test environment by creating a test user and initializing test data.
    - `tearDown`: Cleans up the test environment by deleting test images after each test.
    """
    def setUp(self) -> None:
        picture = create_test_image(1)
        self.user = Users.objects.create_user(
            username="testuser",
            email="testuser@gmail.com",
            first_name="Test",
            last_name="User",
            picture=picture,
            password="Swift-1234",
        )

        self.mock_request = Mock()
        self.mock_request.user = self.user

        self.new_picture_data = {}

        self.test_images = [picture.name]

    def tearDown(self) -> None:
        # Delete the test images after each test
        delete_test_images(self.test_images)

    def test_invalid_new_picture_field(self):
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
                self.new_picture_data["new_picture"] = value

                serializer = UpdatePictureSerializer(data=self.new_picture_data)


                self.assertFalse(serializer.is_valid(), msg=serializer.errors)
                self.assertEqual(serializer.errors["new_picture"][0], error)

                self.test_images.append(value.name)

    def test_valid_new_picture_field(self):
        new_picture = create_test_image(1)
        self.new_picture_data["new_picture"] = new_picture

        serializer = UpdatePictureSerializer(
            data=self.new_picture_data, context={"request": self.mock_request}
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        user = serializer.save()
        self.assertIsNotNone(user)
        self.assertIn("new_picture", serializer.data)

        self.test_images.append(new_picture.name)
