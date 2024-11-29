from django.urls import path
from .views import ConversationsView

urlpatterns = [
    path(
        "conversations/", ConversationsView.as_view(), name="list-create-conversation"
    ),
    path(
        "conversations/<int:pk>/hide/",
        ConversationsView.as_view(),
        name="delete-conversation",
    ),
]
