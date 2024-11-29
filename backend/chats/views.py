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


class MessagesService:
    @staticmethod
    def mark_messages_as_read(receiver, conversation):
        """Read unread messages for the receiver"""
        conversation.messages_set.all().exclude(sender=receiver).update(
            IsReadByReceiver=True
        )

    @staticmethod
    def hide_messages_for_user(user, conversation):
        """Hide messages for a particular user in a conversation"""
        messages = conversation.messages_set.all()
        if user == conversation.user1:
            messages.update(IsVisibleToUser1=False)
        else:
            messages.update(IsVisibleToUser2=False)


class ConversationsView(APIView):
    permission_classes = [IsAuthenticated, IsParticipantInConversation]

    def get(self, request):
        user = request.user

        conversations = Conversations.objects.filter(
            Q(user1=user, IsVisibleToUser1=True) | Q(user2=user, IsVisibleToUser2=True)
        )
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

    def patch(self, request, pk):
        conversation = get_object_or_404(Conversations, pk=pk)
        user = request.user

        # Hide the conversation and hide too messages for the auth user
        if user == conversation.user1:
            conversation.IsVisibleToUser1 = False
            MessagesService.hide_messages_for_user(user, conversation)
        else:
            conversation.IsVisibleToUser2 = False
            MessagesService.hide_messages_for_user(user, conversation)

        conversation.save()

        return Response(status=status.HTTP_200_OK)
