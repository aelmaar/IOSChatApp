from django.shortcuts import render
from .serializers import ConversationsSerializer, MessagesSerializer
from .models import Conversations, Messages
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .permissions import IsParticipantInConversation
from notifications.consumers import ChatConsumer


class MessagesService:
    @staticmethod
    def mark_messages_as_read(receiver, conversation):
        """Read unread messages for the receiver"""
        conversation.messages_set.exclude(sender=receiver).update(IsReadByReceiver=True)

    @staticmethod
    def hide_messages_for_user(user, conversation):
        """Hide messages for a particular user in a conversation"""
        messages = conversation.messages_set.all()
        if user == conversation.user1:
            messages.update(IsVisibleToUser1=False)
        else:
            messages.update(IsVisibleToUser2=False)


class ConversationsView(APIView):
    """
    View for managing conversations between users.

    Methods:
        get(request): Lists all visible conversations for authenticated user
        post(request): Creates a new conversation or activates an existing one
        patch(request, pk): Hides a conversation for the authenticated user

    Permissions:
        - Requires authentication
        - User must be a participant in the conversation
    """

    permission_classes = [IsAuthenticated, IsParticipantInConversation]

    def get(self, request, pk=None):

        if pk:
            # Retrieve a conversation
            conversation = get_object_or_404(Conversations, pk=pk)
            serializer = ConversationsSerializer(
                conversation, context={"request": request}
            )

            return Response(serializer.data)

        user = request.user

        conversations = Conversations.objects.filter(
            Q(user1=user, IsVisibleToUser1=True) | Q(user2=user, IsVisibleToUser2=True)
        ).order_by("lastMessageTimestamp")

        serializer = ConversationsSerializer(
            conversations, many=True, context={"request": request}
        )

        return Response(serializer.data)

    def post(self, request):

        # If a conversation already exists then activate
        # the visibility for the auth user
        user = request.user
        user2_username = request.data.get("user2_username")

        conversation = Conversations.objects.filter(
            Q(user1=user, user2__username=user2_username)
            | Q(user1__username=user2_username, user2=user),
        ).first()

        if conversation:
            # Update visibility
            if user == conversation.user1:
                conversation.IsVisibleToUser1 = True
            else:
                conversation.IsVisibleToUser2 = True

            conversation.save()
            serializer = ConversationsSerializer(
                conversation, context={"request": request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        # Create new conversation
        serializer = ConversationsSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        conversation = get_object_or_404(Conversations, pk=pk)
        user = request.user

        self.check_object_permissions(request, conversation)
        # Hide the conversation and hide too messages for the auth user
        if user == conversation.user1:
            conversation.IsVisibleToUser1 = False
            MessagesService.hide_messages_for_user(user, conversation)
        else:
            conversation.IsVisibleToUser2 = False
            MessagesService.hide_messages_for_user(user, conversation)

        conversation.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class MessagesView(APIView):
    """
    View for managing messages within conversations.

    Methods:
        get(request, pk): Lists all visible messages in a conversation
        post(request, pk): Creates a new message in a conversation
        patch(request, pk): Handles message actions (clear chat, mark as read)

    Permissions:
        - Requires authentication
        - User must be a participant in the conversation
    """

    permission_classes = [IsAuthenticated, IsParticipantInConversation]

    def get(self, request, pk=None):
        user = request.user
        conversation = get_object_or_404(Conversations, pk=pk)
        self.check_object_permissions(request, conversation)

        if user == conversation.user1:
            messages = conversation.messages_set.filter(IsVisibleToUser1=True)
        else:
            messages = conversation.messages_set.filter(IsVisibleToUser2=True)

        # Mark messages as read by the auth user
        MessagesService.mark_messages_as_read(user, conversation)

        serializer = MessagesSerializer(messages, many=True)

        return Response(serializer.data)

    def post(self, request, pk=None):
        conversation = get_object_or_404(Conversations, pk=pk)
        self.check_object_permissions(request, conversation)

        serializer = MessagesSerializer(
            data=request.data,
            context={"request": request, "conversation_id": conversation.id},
        )

        if serializer.is_valid():
            serializer.save()
            conversation.lastMessage = serializer.instance
            conversation.save()

            # Send chat message to the other user via websocket
            user = request.user
            receiver_id = (
                user.id if conversation.user1.id != user.id else conversation.user2.id
            )
            ChatConsumer.sendChatMessage(receiver_id, serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None):
        conversation = get_object_or_404(Conversations, pk=pk)
        self.check_object_permissions(request, conversation)
        action = request.data.get("action")
        user = request.user

        if action == "clear_chat":
            if user == conversation.user1:
                conversation.messages_set.all().update(IsVisibleToUser1=False)
            else:
                conversation.messages_set.all().update(IsVisibleToUser2=False)
            return Response(status=status.HTTP_204_NO_CONTENT)

        elif action == "read_messages":
            MessagesService.mark_messages_as_read(user, conversation)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST
        )
