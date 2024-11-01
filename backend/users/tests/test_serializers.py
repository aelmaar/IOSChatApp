from users.serializers import RegisterSerializer
from django.test import TestCase
from users.models import Users

class RegisterSerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'birthdate': '1990-01-01',
            'picture': 'https://example.com/picture.jpg',
            'password': 'Swift-1234',
            'confirm_password': 'Swift-1234',
        }

        Users.objects.create_user(
            username='differentuser',
            email='differentuser@example.com',
            first_name='differentuser',
            last_name='differentuser',
            birthdate='1990-01-01',
            password='Swift-1234'
        )

    def test_serializer_with_valid_data(self):
        serializer = RegisterSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_validation_data(self):
        test_cases = {
            'username': [
                ('a', 'Username must be at least 5 characters long.'),
                ('testuser!', 'Username must contain only alphanumeric characters and underscores.'),
                ('differentuser', 'This username is already taken.')
            ],
            'email': [
                ('test', 'Enter a valid email address.'),
                ('differentuser@example.com', 'This email is already taken.')
            ],
            'first_name': [
                ('a', 'Name must be at least 2 characters long.'),
                ('Test1', 'Name must contain only alphabetic characters.')
            ],
            'last_name': [
                ('l', 'Name must be at least 2 characters long.'),
                ('Test2', 'Name must contain only alphabetic characters.')
            ],
            'birthdate': [
                ('1990-01-01T00:00:00', 'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'),
                ('1899-01-01', 'Year must be greater than 1900.')
            ],
            'password': [
                ('Swift-1', 'Password must be at least 8 characters long.'),
                ('Swift-Test', 'Password must contain at least one number.'),
                ('swift-1234', 'Password must contain at least one uppercase letter.'),
                ('SWIFT-1234', 'Password must contain at least one lowercase letter.'),
                ('Swift1234', 'Password must contain at least one special character.')
            ],
            'confirm_password': [
                ('password', 'Passwords must match.')
            ]
        }

        for field, cases in test_cases.items():
            for value, error in cases:
                with self.subTest(field=field, value=value):
                    user_data_copy = self.user_data.copy()
                    user_data_copy[field] = value
                    serializer = RegisterSerializer(data=user_data_copy)
                    self.assertFalse(serializer.is_valid())
                    field = 'password' if field == 'confirm_password' else field
                    self.assertEqual(serializer.errors[field][0], error)
