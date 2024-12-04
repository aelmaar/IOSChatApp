from django.shortcuts import render
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UpdateProfileSerializer,
    UpdatePasswordSerializer,
    UpdatePictureSerializer,
    BlacklistSerializer,
    UsersSerializer,
)
from .models import Users
from chat_app.permissions import IsUnauthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from rest_framework.serializers import ValidationError
from users.models import Users, Blacklist
from friendships.models import Friendships
from chats.models import Conversations
from django.utils.crypto import get_random_string
from django.core.files.storage import default_storage
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import Http404
import requests
import logging
import random
import string

logger = logging.getLogger(__name__)


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    queryset = Users.objects.all()
    permission_classes = [IsUnauthenticated]


class LoginView(APIView):
    """
    LoginView handles user login requests.

    Attributes:
        serializer_class (LoginSerializer): The serializer class used for validating login data.
        permission_classes (list): A list of permission classes that the view requires.

    Methods:
        post(request, *args, **kwargs):
            Handles POST requests to authenticate a user.
            Validates the provided data using the serializer.
            If valid, generates and returns JWT tokens (access and refresh).
            If invalid, returns validation errors.
    """

    serializer_class = LoginSerializer
    permission_classes = [IsUnauthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Login successful",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OAuthGoogleCallbackView(APIView):
    """
    View to handle the OAuth Google callback.

    This view processes the authorization code received from the OAuth Google
    provider, exchanges it for an access token, retrieves user information,
    and logs the user in or creates a new user if necessary.

    Methods
    -------
    post(request):
        Handles the POST request to process the authorization code and log the user in.

    get_or_create_user(userinfo):
        Retrieves or creates a user based on the user information from the OAuth Google provider.

    exchange_code_with_access_token(authorization_code):
        Exchanges the authorization code for an access token.

    request_42_userinfo(access_token):
        Retrieves user information from the OAuth Google provider using the access token.
    """

    permission_classes = [IsUnauthenticated]

    def post(self, request):
        authorization_code = request.data.get("code")

        if not authorization_code:
            raise ValidationError(
                {
                    "error_message": "Authorization code is missing. Please try logging in again."
                }
            )

        access_token = self.exchange_code_with_access_token(authorization_code)
        if access_token is None:
            raise ValidationError(
                {
                    "error_message": "The authorization code is invalid or expired. Please try logging in again."
                }
            )

        userinfo = self.request_google_userinfo(access_token)
        if userinfo is None:
            raise ValidationError(
                {
                    "error_message": "Authentication failed. Please ensure you are logged in and try again."
                }
            )

        user = self.get_or_create_user(userinfo)
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )

    def get_or_create_user(self, userinfo):
        email = userinfo.get("email")
        user = Users.objects.filter(email=email).first()
        username = f"{userinfo.get('given_name').lower()}_{userinfo.get('id')[:5]}"

        if not user:
            base_username = username
            while Users.objects.filter(username=username).exists():
                random_id = "".join(
                    random.choices(string.ascii_lowercase + string.digits, k=6)
                )
                username = f"{base_username}_{random_id}"

            password = get_random_string(30)
            user = Users.objects.create_user(
                username=username,
                email=email,
                first_name=userinfo.get("given_name"),
                last_name=userinfo.get("family_name"),
                password=password,
                picture=userinfo.get("picture"),
                IsOAuth=True,
            )
        return user

    def exchange_code_with_access_token(self, authorization_code):
        data = {
            "code": authorization_code,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "authorization_code",
        }

        response = requests.post(settings.GOOGLE_TOKEN_URI, data)
        response_data = response.json()

        return response_data.get("access_token", None)

    def request_google_userinfo(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo", headers=headers
        )
        if not response.ok:
            return None
        return response.json()


class OAuth42CallbackView(APIView):
    """
    View to handle the OAuth 42 callback.

    This view processes the authorization code received from the OAuth 42
    provider, exchanges it for an access token, retrieves user information,
    and logs the user in or creates a new user if necessary.

    Methods
    -------
    post(request):
        Handles the POST request to process the authorization code and log the user in.

    get_or_create_user(userinfo):
        Retrieves or creates a user based on the user information from the OAuth 42 provider.

    exchange_code_with_access_token(authorization_code):
        Exchanges the authorization code for an access token.

    request_42_userinfo(access_token):
        Retrieves user information from the OAuth 42 provider using the access token.
    """

    permission_classes = [IsUnauthenticated]

    def post(self, request):
        authorization_code = request.data.get("code")

        logger.info(f"Authorization code: {authorization_code}")
        if not authorization_code:
            raise ValidationError(
                {
                    "error_message": "Authorization code is missing. Please try logging in again."
                }
            )

        access_token = self.exchange_code_with_access_token(authorization_code)
        if access_token is None:
            raise ValidationError(
                {
                    "error_message": "The authorization code is invalid or expired. Please try logging in again."
                }
            )

        userinfo = self.request_42_userinfo(access_token)
        if userinfo is None:
            raise ValidationError(
                {
                    "error_message": "Authentication failed. Please ensure you are logged in and try again."
                }
            )

        user = self.get_or_create_user(userinfo)
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )

    def get_or_create_user(self, userinfo):
        email = userinfo.get("email")
        username = userinfo.get("login")
        user_id = userinfo.get("id")
        user = Users.objects.filter(email=email).first()

        if not user:
            base_username = username
            password = get_random_string(30)
            picture = userinfo.get("image").get("versions").get("medium")

            while Users.objects.filter(
                username=username
            ).exists() or Users.objects.filter(username=f"{username}_{user_id}"):
                random_id = "".join(
                    random.choices(string.ascii_lowercase + string.digits, k=6)
                )
                username = f"{base_username}_{random_id}"

            user = Users.objects.create_user(
                username=username,
                email=email,
                first_name=userinfo.get("first_name"),
                last_name=userinfo.get("last_name"),
                picture=picture,
                password=password,
                IsOAuth=True,
            )
        return user

    def exchange_code_with_access_token(self, authorization_code):
        data = {
            "code": authorization_code,
            "redirect_uri": settings.REDIRECT_42_URI,
            "client_id": settings.CLIENT_42_ID,
            "client_secret": settings.CLIENT_42_SECRET,
            "grant_type": "authorization_code",
        }

        response = requests.post(settings.TOKEN_42_URI, data)
        response_data = response.json()

        return response_data.get("access_token", None)

    def request_42_userinfo(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get("https://api.intra.42.fr/v2/me", headers=headers)

        if not response.ok:
            return None
        return response.json()


class UpdateProfileView(APIView):
    """
    UpdateProfileView handles user profile update requests.

    Methods:
        patch(request, *args, **kwargs):
            Handles PATCH requests to update the user profile.
            Validates the provided data using the serializer.
            If valid, updates the user profile and returns the updated data.
            If invalid, returns validation errors.
    """

    def patch(self, request, *args, **kwargs):
        serializer = UpdateProfileSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdatePasswordView(APIView):
    """
    UpdatePasswordView handles user password update requests.

    Methods:
        patch(request, *args, **kwargs):
            Handles PATCH requests to update the user password.
            Validates the provided data using the serializer.
            If valid, updates the user password and returns a success message.
            If invalid, returns validation errors.
    """

    def patch(self, request, *args, **kwargs):
        serializer = UpdatePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password updated successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdatePictureView(APIView):
    """
    UpdatePictureView handles user profile picture update requests.

    Methods:
        patch(request, *args, **kwargs):
            Handles PATCH requests to update the user profile picture.
            Validates the provided data using the serializer.
            If valid, updates the user profile picture and returns the updated data.
            If invalid, returns validation errors.
    """

    def patch(self, request, *args, **kwargs):
        serializer = UpdatePictureSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeletePictureView(APIView):
    """
    DeletePictureView handles user profile picture deletion requests.

    Methods:
        delete(request, *args, **kwargs):
            Handles DELETE requests to delete the user profile picture.
            If the user has a profile picture, deletes the picture and returns a success message.
            If the user does not have a profile picture, returns a success message.
    """

    def delete(self, request, *args, **kwargs):
        user = request.user
        if user.picture and default_storage.exists(user.picture.path):
            default_storage.delete(user.picture.path)
            user.picture = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BlacklistView(APIView):
    """
    BlacklistView handles user blacklist requests.

    Methods:
        get(request):
            Handles GET requests to retrieve the list of blocked users.
            Returns the list of blocked users.
        post(request):
            Handles POST requests to block a user.
            Validates the provided data using the serializer.
            If valid, blocks the user, removes the friendship if exists and blocks the conversation if exists.
            If invalid, returns validation errors.
        delete(request):
            Handles DELETE requests to unblock a user.
            If the user is blocked, unblocks the user and unblocks the conversation if exists.
            If the user is not blocked, returns a 404 response.
    """

    def get(self, request):
        blocked_users = Blacklist.objects.filter(user=request.user)
        serializer = BlacklistSerializer(
            blocked_users, many=True, context={"request", request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BlacklistSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            blacklisted_obj = serializer.save()
            self.remove_friendship_if_exists(blacklisted_obj)
            self.block_unblock_conversation_if_exists(blacklisted_obj)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        blocked_username = request.data.get("blocked_username")

        blacklisted_obj = Blacklist.objects.filter(
            user=request.user,
            blocked_user=Users.objects.filter(username=blocked_username).first(),
        ).first()

        if blacklisted_obj:
            self.block_unblock_conversation_if_exists(blacklisted_obj, value=False)
            blacklisted_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def remove_friendship_if_exists(self, blacklisted_obj: Blacklist) -> None:
        """Delete friendship if exists"""
        user = blacklisted_obj.user
        blocked_user = blacklisted_obj.blocked_user
        friendship = Friendships.objects.filter(
            Q(user1=user, user2=blocked_user) | Q(user1=blocked_user, user2=user)
        ).first()

        if friendship:
            friendship.delete()

    def block_unblock_conversation_if_exists(
        self, blacklisted_obj: Blacklist, value=True
    ) -> None:
        """Block or unblock a conversation if exists for the auth user"""
        user = blacklisted_obj.user
        blocked_user = blacklisted_obj.blocked_user

        conversation = Conversations.objects.filter(
            Q(user1=user, user2=blocked_user) | Q(user1=blocked_user, user2=user)
        ).first()

        if conversation:
            if user == conversation.user1:
                conversation.IsBlockedByUser1 = value
            else:
                conversation.IsBlockedByUser2 = value
            conversation.save()


class UsersSearchView(APIView):

    def get(self, request):
        """Filter by username or by full name"""
        value = request.query_params.get("q", "")
        user = request.user

        filtered_users = Users.objects.filter(
            Q(username__startswith=value)
            | Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
        )

        if filtered_users:
            # Get users blocked by auth user
            blocked_users = Blacklist.objects.filter(user=user).values_list(
                "blocked_user__username", flat=True
            )
            # Get users who block auth user
            blocking_users = Blacklist.objects.filter(blocked_user=user).values_list(
                "user__username", flat=True
            )

            # Exclude blocked/blocking users but not auth user
            filtered_users = filtered_users.exclude(
                username__in=list(blocked_users) + list(blocking_users)
            )[:10]

        serializer = UsersSerializer(filtered_users, many=True)

        return Response(serializer.data)


class UserProfileView(APIView):

    def get(self, request, username):

        user = get_object_or_404(Users, username=username)

        # Check whether the user's username is blocked or get blocked by the auth
        is_blocked = Blacklist.objects.filter(
            Q(user=request.user, blocked_user=user)
            | Q(user=user, blocked_user=request.user)
        ).exists()

        if is_blocked:
            raise Http404("User not found.")

        serializer = UsersSerializer(user)

        return Response(serializer.data)
