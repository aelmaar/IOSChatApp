from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FriendshipsSerializer
from django.shortcuts import get_object_or_404
from .models import Friendships
from django.db.models import Q
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from .permissions import IsFriendshipParticipant
import logging

logger = logging.getLogger(__name__)


class FriendshipsView(APIView):
    permission_classes = [IsAuthenticated, IsFriendshipParticipant]

    def get(self, request, pk=None):
        if pk:
            friendship = get_object_or_404(Friendships, pk=pk)
            self.check_object_permissions(request, friendship)
            serializer = FriendshipsSerializer(friendship, context={"request": request})
            return Response(serializer.data)
        friendships = Friendships.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        )
        serializer = FriendshipsSerializer(
            friendships, context={"request": request}, many=True
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = FriendshipsSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        user = request.user
        friendship = get_object_or_404(Friendships, pk=pk)
        self.check_object_permissions(request, friendship)

        if friendship.user1 == user:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if friendship.status != Friendships.PENDING:
            return Response(
                {"detail": "You cannot perform this action on this friendship."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action = request.data.get("action")
        if action == "accept":
            friendship.status = Friendships.ACCEPTED
            friendship.save()
            return Response({"detail": "Friendship accepted"})
        elif action == "reject":
            friendship.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk=None):
        friendship = get_object_or_404(Friendships, pk=pk)
        self.check_object_permissions(request, friendship)

        action = request.data.get("action")

        if action == "cancel_pending":
            if friendship.status == Friendships.PENDING:
                friendship.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "The friendship has already been accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        friendship.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
