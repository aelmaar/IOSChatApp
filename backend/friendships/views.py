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
from notifications.consumers import NotificationConsumer
import logging

logger = logging.getLogger(__name__)


class FriendshipsView(APIView):
    """
    View for managing friendship relationships between users.

    Methods:
        get(request, pk=None):
            - Without pk: Lists all friendships for authenticated user
            - With pk: Retrieves specific friendship details

        post(request): Creates a new friendship request

        patch(request, pk):
            Handles friendship request responses (accept/reject)
            - Only recipient can accept/reject
            - Can only act on PENDING requests

        delete(request, pk):
            Handles friendship deletions
            - Cancels pending requests with 'cancel_pending' action
            - Removes existing friendships

    Permissions:
        - Requires authentication
        - User must be participant in friendship for specific friendship actions
    """

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
            user = request.user
            friendship = serializer.save()
            # Get receiver ID to send a friend request notification
            receiver_id = (
                friendship.user1.id if friendship.user1 != user else friendship.user2.id
            )
            NotificationConsumer.sendFriendRequest(receiver_id)
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
                {"detail": "The friendship has already been accepted."},
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
