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
)
from .models import Users
from chat_app.permissions import IsUnauthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from rest_framework.serializers import ValidationError
from users.models import Users
from django.utils.crypto import get_random_string
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

    def patch(self, request, *args, **kwargs):
        serializer = UpdateProfileSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdatePasswordView(APIView):

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
