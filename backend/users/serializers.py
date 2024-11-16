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
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Fields:
        username (str): The username of the user. Must be unique. Max length 30.
        email (str): The email of the user. Must be unique. Max length 100.
        first_name (str): The first name of the user. Max length 30.
        last_name (str): The last name of the user. Max length 30.
        birthdate (str, optional): The birthdate of the user.
        picture (ImageField, optional): The profile picture of the user.
        password (str): The password of the user.
        confirm_password (str): Confirmation of the password.

    Methods:
        validate(data):
            Validates that the password and confirm_password fields match.

        create(validated_data):
            Creates and returns a new user instance with the validated data.
    """

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
    """
    LoginSerializer is used to validate user login credentials.

    Fields:
        username_or_email (str): The username or email of the user. This field is required.
        password (str): The password of the user. This field is required and will be styled as a password input.

    Methods:
        validate(attrs):
            Validates the provided username/email and password.
            If the credentials are correct, the user object is added to the validated data.
            Raises a ValidationError if the credentials are incorrect.
    """

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
    """
    Serializer for updating user profile information.

    Fields:
        username (str): The username of the user. Required. Max length 30.
        email (str): The email of the user. Required. Max length 100.
        first_name (str): The first name of the user. Required. Max length 30.
        last_name (str): The last name of the user. Required. Max length 30.
        birthdate (str): The birthdate of the user. Optional.

    Methods:
        save(): Saves the updated user profile information. If the user is not authenticated via OAuth, updates the username and email as well.
    """

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
    """
    Serializer for updating user password.

    Fields:
        new_password (CharField): The new password for the user. Must be provided and meet the password strength requirements.
        confirm_password (CharField): Confirmation of the new password. Must match the new_password field.

    Methods:
        validate(attrs):
            Validates that the new_password and confirm_password fields match and that the new password is different from the old password.
            Raises:
                serializers.ValidationError: If the passwords do not match or if the new password is the same as the old password.

        save(**kwargs): Sets the new password for the user and saves the user instance.
    """

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
            raise serializers.ValidationError({"new_password": "Passwords must match."})
        if user.check_password(attrs["new_password"]):
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the old one."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context.get("request").user
        user.set_password(self.validated_data["new_password"])

        user.save()
        return user


class UpdatePictureSerializer(serializers.Serializer):
    """
    Serializer for updating a user's profile picture.

    Fields:
        new_picture (ImageField): The new profile picture to be uploaded. This field is required and validated using the `validate_image_size` validator.

    Methods:
        save(**kwargs):
            Saves the new profile picture for the user. Deletes the old picture from storage if it exists.

        to_representation(instance):
            Returns a dictionary representation of the instance, including the absolute URL of the new profile picture if it exists.
    """

    new_picture = serializers.ImageField(
        required=True,
        validators=[validate_image_size],
        use_url=True,
    )

    def save(self, **kwargs):
        user = self.context.get("request").user
        old_picture = user.picture

        if old_picture and default_storage.exists(old_picture.path):
            default_storage.delete(old_picture.path)

        user.picture = self.validated_data["new_picture"]
        user.save()

        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")
        user = request.user
        representation["new_picture"] = (
            request.build_absolute_uri(user.picture.url) if user.picture else None
        )
        return representation
