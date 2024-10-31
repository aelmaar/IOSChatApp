from .models import Users
from rest_framework import serializers
from .validators import validate_username, validate_password_strength, validate_name, validate_birthdate, validate_unique
from django.core.validators import validate_email

# register serializer
class RegisterSerializer(serializers.ModelSerializer):

    username = serializers.CharField(required=True, validators=[validate_username, validate_unique])
    email = serializers.EmailField(required=True, validators=[validate_email, validate_unique])
    first_name = serializers.CharField(required=True, validators=[validate_name])
    last_name = serializers.CharField(required=True, validators=[validate_name])
    birthdate = serializers.CharField(required=True, validators=[validate_birthdate])
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, validators=[validate_password_strength])
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = Users
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'birthdate', 'picture', 'password', 'confirm_password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        return data

    def save(self):
        user = Users(
            email=self.validated_data['email'],
            username=self.validated_data['username'],
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            birthdate=self.validated_data['birthdate'],
            picture=self.validated_data['picture']
        )
        password = self.validated_data['password']
    
        user.set_password(password)
        user.save()
        return user
