from django.core.exceptions import ValidationError
from .models import Users
import re

def validate_username(username):
    if len(username) < 5:
        raise ValidationError('Username must be at least 5 characters long.')
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError('Username must contain only alphanumeric characters and underscores.')
    return username


def validate_password_strength(password):
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one number.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"[^\w\s]", password):
        raise ValidationError("Password must contain at least one special character.")
    return password

def validate_name(name):
    if len(name) < 2:
        raise ValidationError('Name must be at least 2 characters long.')
    if not re.match(r'^[a-zA-Z\s]+$', name):
        raise ValidationError('Name must contain only alphabetic characters.')
    return name

def validate_birthdate(birthdate):
    
    if re.match(r'^\d{4}-\d{2}-\d{2}$', birthdate):
        if int(birthdate[:4]) < 1900:
            raise ValidationError('Year must be greater than 1900.')

    if not re.match(r'^\d{4}-\d{2}-\d{2}$', birthdate):
        raise ValidationError('Date has wrong format. Use one of these formats instead: YYYY-MM-DD.')
    return birthdate
