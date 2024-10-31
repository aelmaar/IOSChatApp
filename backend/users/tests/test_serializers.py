from django.test import TestCase
from users.serializers import RegisterSerializer
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

    def test_serializer_with_valid_data(self):
        serializer = RegisterSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_with_username_less_than_5_characters(self):
        self.user_data['username'] = 'a'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['username'][0], 'Username must be at least 5 characters long.')

    def test_serializer_with_invalid_username(self):
        self.user_data['username'] = 'testuser!'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['username'][0], 'Username must contain only alphanumeric characters and underscores.')
    
    def test_serializer_with_existing_username_or_email(self):
        Users.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            birthdate='1990-01-01',
            password='Swift-1234'
        )

        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['username'][0], 'This username is already taken.')
        self.assertEqual(serializer.errors['email'][0], 'This email is already taken.')

    def test_serializer_with_invalid_email(self):
        self.user_data['email'] = 'test'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['email'][0], 'Enter a valid email address.')
    
    def test_serializer_with_first_name_less_than_2_characters(self):
        self.user_data['first_name'] = 'a'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['first_name'][0], 'Name must be at least 2 characters long.')
    
    def test_serializer_with_invalid_first_name(self):
        self.user_data['first_name'] = 'Test1'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['first_name'][0], 'Name must contain only alphabetic characters.')

    def test_serializer_with_last_name_less_than_2_characters(self):
        self.user_data['last_name'] = 'a'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['last_name'][0], 'Name must be at least 2 characters long.')
    
    def test_serializer_with_invalid_last_name(self):
        self.user_data['last_name'] = 'User1'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['last_name'][0], 'Name must contain only alphabetic characters.')

    def test_serializer_with_password_less_than_8_characters(self):
        self.user_data['password'] = 'Swift-1'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['password'][0], 'Password must be at least 8 characters long.')
    
    def test_serializer_with_password_missing_number(self):
        self.user_data['password'] = 'Swift-Test'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['password'][0], 'Password must contain at least one number.')
    
    def test_serializer_with_password_missing_uppercase_letter(self):
        self.user_data['password'] = 'swift-1234'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['password'][0], 'Password must contain at least one uppercase letter.')
    
    def test_serializer_with_password_missing_lowercase_letter(self):
        self.user_data['password'] = 'SWIFT-1234'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['password'][0], 'Password must contain at least one lowercase letter.')
    
    def test_serializer_with_password_missing_special_character(self):
        self.user_data['password'] = 'Swift1234'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['password'][0], 'Password must contain at least one special character.')
    
    def test_serializer_with_passwords_not_matching(self):
        self.user_data['confirm_password'] = 'password'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['password'][0], 'Passwords must match.')

    def test_serializer_with_invalid_birthdate(self):
        self.user_data['birthdate'] = '02-01-1990'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['birthdate'][0], 'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.')
    
    def test_serializer_with_birthdate_year_less_than_1900(self):
        self.user_data['birthdate'] = '1899-01-01'
        serializer = RegisterSerializer(data=self.user_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['birthdate'][0], 'Year must be greater than 1900.')
