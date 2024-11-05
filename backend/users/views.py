from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, LoginSerializer
from .models import Users
from chat_app.permissions import IsUnauthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

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
