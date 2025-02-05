from .models import Users, Blacklist
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
from django.shortcuts import get_object_or_404
from friendships.models import Friendships
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class UsersSerializer(serializers.ModelSerializer):

    picture = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ["username", "first_name", "last_name", "birthdate", "picture"]
        read_only_fields = fields

    def get_picture(self, obj):
        request = self.context.get("request")

        return request.build_absolute_uri(obj.picture.url) if obj.picture else None

    def to_representation(self, instance):
        """
        Overrides the default to_representation method to add the IsOnline field to the representation.
        """
        user = self.context.get("request").user
        representation = super().to_representation(instance)

        # Check whether it's the auth user then display the online status
        if user.username == instance.username:
            representation["IsOnline"] = instance.IsOnline

        # Check whether the user is a friend then display it's online status
        if Friendships.objects.filter(
            Q(user1=user, user2=instance) | Q(user1=instance, user2=user),
            status=Friendships.ACCEPTED,
        ).exists():
            representation["IsOnline"] = instance.IsOnline

        return representation


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


class BlacklistSerializer(serializers.ModelSerializer):
    """
    Serializer for blocking and unblocking users.

    Fields:
        blocked_username (str): The username of the user to be blocked. Required. Max length 30.
        blocked_user (UsersSerializer): The user instance of the blocked user. Read-only.
        created_at (DateTimeField): The date and time when the user was blocked. Read-only.

    Methods:
        validate_blocked_username(value):
            Validates that the user is not trying to block themselves.

        validate(attrs):
            Validates that the user is not trying to block a user that is already blocked.
            Adds the user and blocked user instances to the validated data.

        save():
            Creates a new Blacklist instance and returns it.

    """

    blocked_username = serializers.CharField(
        required=True, max_length=30, write_only=True
    )

    class Meta:
        model = Blacklist
        fields = ["blocked_user", "created_at", "blocked_username"]
        read_only_fields = ["blocked_user", "created_at"]

    def validate_blocked_username(self, value):
        user = self.context.get("request").user
        if user.username == value:
            raise serializers.ValidationError("You cannot block or unblock yourself.")
        return value

    def validate(self, attrs):
        user = self.context.get("request").user

        blocked_user = get_object_or_404(Users, username=attrs["blocked_username"])

        if Blacklist.objects.filter(user=user, blocked_user=blocked_user).exists():
            raise serializers.ValidationError("User is already blocked.")

        attrs["blocked_user"] = blocked_user
        return attrs

    def save(self):
        user = self.context.get("request").user
        blocked_user = self.validated_data["blocked_user"]

        blacklist = Blacklist.objects.create(user=user, blocked_user=blocked_user)

        return blacklist

    def to_representation(self, instance):
        request = self.context.get("request")
        representation = super().to_representation(instance)

        # Handle both dict and model instance cases
        blocked_user = instance.get('blocked_user') if isinstance(instance, dict) else instance.blocked_user

        representation["blocked_user"] = UsersSerializer(
            blocked_user, context={"request": request}
        ).data

        return representation
