from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from .serializers import RegisterSerializer
from .models import Users
from chat_app.permissions import IsUnauthenticated


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    queryset = Users.objects.all()
    permission_classes = [IsUnauthenticated]
