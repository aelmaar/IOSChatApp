from rest_framework import serializers
from chats.models import Conversations, Messages
from users.serializers import UsersSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
import html

Users = get_user_model()


class ConversationsSerializer(serializers.ModelSerializer):

    user2_username = serializers.CharField(
        required=True, max_length=30, write_only=True
    )

    user = serializers.SerializerMethodField()
    IsBlockedByMe = serializers.SerializerMethodField()
    IsBlockedByOtherUser = serializers.SerializerMethodField()

    class Meta:
        model = Conversations
        fields = [
            "id",
            "user",
            "IsBlockedByMe",
            "IsBlockedByOtherUser",
            "lastMessage",
            "user2_username",
        ]
        read_only_fields = [
            "id",
            "user",
            "IsBlockedByMe",
            "IsBlockedByOtherUser",
            "lastMessage",
        ]

    def get_user(self, obj):
        user = self.context.get("request").user
        if user == obj.user1:
            return UsersSerializer(obj.user2).data
        else:
            return UsersSerializer(obj.user1).data

    def get_IsBlockedByMe(self, obj):
        user = self.context.get("request").user

        if user == obj.user1 and obj.IsBlockedByUser1:
            return True
        elif user == obj.user2 and obj.IsBlockedByUser2:
            return True
        return False

    def get_IsBlockedByOtherUser(self, obj):
        user = self.context.get("request").user

        if user == obj.user1 and obj.IsBlockedByUser2:
            return True
        elif user == obj.user2 and obj.IsBlockedByUser1:
            return True
        return False

    def validate(self, attrs):
        user = self.context.get("request").user
        user2 = get_object_or_404(Users, username=attrs["user2_username"])

        attrs["user2"] = user2

        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user

        user2 = validated_data["user2"]

        conversation = Conversations.objects.create(user1=user, user2=user2)

        return conversation


class MessagesSerializer(serializers.ModelSerializer):

    sender = serializers.SerializerMethodField()

    class Meta:
        model = Messages
        fields = ["id", "conversation", "sender", "content", "created_at"]
        read_only_fields = ["id", "conversation", "sender", "created_at"]

    def get_sender(self, obj):
        return obj.sender.username

    def validate_content(self, value):
        return html.escape(value)

    def validate(self, attrs):
        conversation_id = self.context.get("request").query_params.get(
            "conversation_id"
        )

        conversation = get_object_or_404(Conversations, pk=conversation_id)

        attrs["conversation"] = conversation

        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user
        conversation = validated_data["conversation"]
        content = validated_data["content"]

        messages = Messages.objects.create(
            conversation=conversation, sender=user, content=content
        )

        return messages
