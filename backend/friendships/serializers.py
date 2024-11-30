from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Friendships
from users.models import Blacklist
from users.serializers import UsersSerializer
from django.shortcuts import get_object_or_404
from django.db.models import Q

Users = get_user_model()


class FriendshipsSerializer(serializers.ModelSerializer):

    friend_username = serializers.CharField(
        required=True, max_length=30, write_only=True
    )

    friend = serializers.SerializerMethodField()
    pending_action = serializers.SerializerMethodField()

    class Meta:
        model = Friendships
        fields = ["id", "friend", "friend_username", "status", "pending_action"]
        read_only_fields = ["id", "friend", "status", "pending_action"]

    def get_friend(self, obj):
        """Return the serialized data of the auth user's friend"""
        user = self.context.get("request").user
        if user == obj.user1:
            return UsersSerializer(obj.user2).data
        else:
            return UsersSerializer(obj.user1).data

    def get_pending_action(self, obj):
        """Return whether the auth user should accept/reject the friendship or is in pending"""
        user = self.context.get("request").user

        if obj.status == Friendships.PENDING:
            if user == obj.user2:
                return "accept_or_reject"
            else:
                return "waiting_for_response"
        return None

    def validate_friend_username(self, username):
        user = self.context.get("request").user
        if user.username == username:
            raise serializers.ValidationError("You cannot be friends with yourself.")
        return username

    def validate(self, attrs):
        user = self.context.get("request").user
        friend_user = get_object_or_404(Users, username=attrs["friend_username"])

        if Blacklist.objects.filter(
            Q(user=user, blocked_user=friend_user)
            | Q(user=friend_user, blocked_user=user)
        ).exists():
            raise serializers.ValidationError(
                "You cannot create a friendship with this user."
            )

        if Friendships.objects.filter(
            Q(user1=user, user2=friend_user) | Q(user1=friend_user, user2=user)
        ).exists():
            raise serializers.ValidationError("Friendship already exists.")

        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user
        friend_user = get_object_or_404(
            Users, username=validated_data["friend_username"]
        )

        friendship = Friendships.objects.create(user1=user, user2=friend_user)

        return friendship
