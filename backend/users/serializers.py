from .models import Users
from rest_framework import serializers
from .validators import (
    validate_username,
    validate_password_strength,
    validate_name,
    validate_birthdate,
    validate_image_size,
)
from django.core.validators import validate_email
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        max_length=30,
        required=True,
        validators=[
            validate_username,
            UniqueValidator(
                queryset=Users.objects.all(), message="This username is already taken."
            ),
        ],
    )
    email = serializers.EmailField(
        max_length=100,
        required=True,
        validators=[
            validate_email,
            UniqueValidator(
                queryset=Users.objects.all(), message="This email is already taken."
            ),
        ],
    )
    first_name = serializers.CharField(
        max_length=30, required=True, validators=[validate_name]
    )
    last_name = serializers.CharField(
        max_length=30, required=True, validators=[validate_name]
    )
    birthdate = serializers.CharField(required=False, validators=[validate_birthdate])
    picture = serializers.ImageField(
        required=False, validators=[validate_image_size], use_url=True
    )
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

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        user = Users(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            birthdate=validated_data.get("birthdate"),
        )
        user.set_password(validated_data["password"])
        user.picture = validated_data.get("picture")

        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, style={"input_type": "password"})

    def validate(self, attrs):
        username_or_email = attrs.get("username_or_email")
        password = attrs.get("password")

        if username_or_email and password:
            user = authenticate(
                request=self.context.get("request"),
                username=username_or_email,
                password=password,
            )
            if not user:
                raise serializers.ValidationError(
                    "username/email or password is incorrect"
                )

        attrs["user"] = user
        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        max_length=30,
        required=True,
        validators=[validate_username],
    )
    email = serializers.EmailField(
        max_length=100,
        required=True,
        validators=[validate_email],
    )
    first_name = serializers.CharField(
        max_length=30, required=True, validators=[validate_name]
    )
    last_name = serializers.CharField(
        max_length=30, required=True, validators=[validate_name]
    )
    birthdate = serializers.CharField(required=False, validators=[validate_birthdate])

    class Meta:

        model = Users
        fields = ["username", "email", "first_name", "last_name", "birthdate"]

    def save(self):
        request = self.context.get("request")
        email = request.user.email
        user = Users.objects.get(email=email)
        if not user.IsOAuth:
            user.username = self.validated_data.get("username")
            user.email = self.validated_data.get("email")
        user.first_name = self.validated_data.get("first_name")
        user.last_name = self.validated_data.get("last_name")
        user.birthdate = self.validated_data.get("birthdate")

        user.save()

        return user


class UpdatePasswordSerializer(serializers.Serializer):

    new_password = serializers.CharField(
        required=True,
        style={"input_type": "password"},
        validators=[validate_password_strength],
        write_only=True,
    )

    confirm_password = serializers.CharField(
        required=True, style={"input_type": "password"}, write_only=True
    )

    def validate(self, attrs):
        user = self.context.get("request").user
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        if user.check_password(attrs["new_password"]):
            raise serializers.ValidationError(
                {"password": "New password must be different from the old one."}
            )
        return attrs
    
    def save(self, **kwargs):
        user = self.context.get('request').user
        user.set_password(self.validated_data["new_password"])

        user.save()
        return user
