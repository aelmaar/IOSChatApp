from rest_framework.test import APIClient
from users.models import Users

def get_auth_headers(client, username, password):
    response = client.post(
        "/api/login/", {"username_or_email": username, "password": password}
    )
    return {"Authorization": f"Bearer {response.data.get('access')}"}


def create_test_user(username, email, first_name="Test", last_name="User"):
    """Helper function to create test users"""
    return Users.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        birthdate="1990-01-01",
        password="Swift-1234",
    )
