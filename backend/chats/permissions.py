from rest_framework.permissions import BasePermission
from chats.models import Conversations, Messages

class IsParticipantInConversation(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        if isinstance(obj, Conversations):
            return user == obj.user1 or user == obj.user2