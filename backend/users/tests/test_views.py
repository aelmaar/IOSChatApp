from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/register/'
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'birthdate': '1990-01-01',
            'picture': 'https://example.com/picture.jpg',
            'password': 'Swift-1234',
            'confirm_password': 'Swift-1234',
        }
    
    def test_register_view_with_valid_data(self):
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_register_view_with_username_less_than_5_characters(self):
        self.user_data['username'] = 'a'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0], 'Username must be at least 5 characters long.')
    
    def test_register_view_with_invalid_username(self):
        self.user_data['username'] = 'testuser!'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0], 'Username must contain only alphanumeric characters and underscores.')
    
    def test_register_view_with_existing_username_or_email(self):
        self.client.post(self.url, self.user_data)
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0], 'This username is already taken.')
        self.assertEqual(response.data['email'][0], 'This email is already taken.')
    
    def test_register_view_with_invalid_email(self):
        self.user_data['email'] = 'test'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], 'Enter a valid email address.')
    
    def test_register_view_with_first_name_less_than_2_characters(self):
        self.user_data['first_name'] = 'a'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['first_name'][0], 'Name must be at least 2 characters long.')
    
    def test_register_view_with_invalid_first_name(self):
        self.user_data['first_name'] = 'Test1'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['first_name'][0], 'Name must contain only alphabetic characters.')
    
    def test_register_view_with_invalid_birthdate(self):
        self.user_data['birthdate'] = '1990-01-01T00:00:00'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['birthdate'][0], 'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.')

    def test_register_view_with_birthdate_less_than_1900(self):
        self.user_data['birthdate'] = '1899-01-01'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['birthdate'][0], 'Year must be greater than 1900.')
    
    def test_register_view_with_password_less_than_8_characters(self):
        self.user_data['password'] = 'Swift-1'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Password must be at least 8 characters long.')
    
    def test_register_view_with_password_missing_number(self):
        self.user_data['password'] = 'Swift-Test'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Password must contain at least one number.')
    
    def test_register_view_with_password_missing_uppercase_letter(self):
        self.user_data['password'] = 'swift-1234'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Password must contain at least one uppercase letter.')
    
    def test_register_view_with_password_missing_lowercase_letter(self):
        self.user_data['password'] = 'SWIFT-1234'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Password must contain at least one lowercase letter.')
    
    def test_register_view_with_password_missing_special_character(self):
        self.user_data['password'] = 'Swift1234'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Password must contain at least one special character.')
    
    def test_register_view_with_passwords_not_matching(self):
        self.user_data['confirm_password'] = 'password'
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Passwords must match.')
