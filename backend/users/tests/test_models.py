from django.test import TestCase
from users.models import Users

class UsersModelTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'birthdate': '1990-01-01',
            'picture': 'https://example.com/picture.jpg',
        }
        
    def test_create_user(self):
        user = Users.objects.create_user(**self.user_data, password='testpassword')
        self.assertEqual(user.username, self.user_data['username'])
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertEqual(user.birthdate, self.user_data['birthdate'])
        self.assertEqual(user.picture, self.user_data['picture'])
        self.assertTrue(user.check_password('testpassword'))
    
    def test_user_str_representation(self):
        user = Users.objects.create_user(**self.user_data, password='testpassword')
        self.assertEqual(str(user), self.user_data['username'])
