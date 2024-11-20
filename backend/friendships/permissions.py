from rest_framework.permissions import BasePermission


class IsFriendshipParticipant(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        # Check if the user is either user1 or user2 in the friendship
        return obj.user1 == user or obj.user2 == user
