from .models import Users
from rest_framework import serializers
from .validators import (
    validate_username,
    validate_password_strength,
    validate_name,
    validate_birthdate,
)
from django.core.validators import validate_email
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate


class RegisterSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        required=True,
        validators=[
            validate_username,
            UniqueValidator(
                queryset=Users.objects.all(), message="This username is already taken."
            ),
        ],
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            validate_email,
            UniqueValidator(
                queryset=Users.objects.all(), message="This email is already taken."
            ),
        ],
    )
    first_name = serializers.CharField(required=True, validators=[validate_name])
    last_name = serializers.CharField(required=True, validators=[validate_name])
    birthdate = serializers.CharField(required=False, validators=[validate_birthdate])
    password = serializers.CharField(
        style={"input_type": "password"},
        write_only=True,
        validators=[validate_password_strength],
    )
    confirm_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = Users
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "birthdate",
            "picture",
            "password",
            "confirm_password",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def save(self):
        user = Users(
            email=self.validated_data["email"],
            username=self.validated_data["username"],
            first_name=self.validated_data["first_name"],
            last_name=self.validated_data["last_name"],
            birthdate=self.validated_data.get("birthdate"),
            picture=self.validated_data.get("picture"),
        )
        password = self.validated_data["password"]

        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, style={"input_type": "password"})

    def validate(self, attrs):
        username_or_email = attrs.get("username_or_email")
        password = attrs.get("password")

        if username_or_email and password:
            user = authenticate(request=self.context.get('request'), username=username_or_email, password=password)
            if not user:
                raise serializers.ValidationError(
                    "username/email or password is incorrect"
                )

        attrs["user"] = user
        return attrs
