from django.urls import path
from .views import ConversationsView, MessagesView

urlpatterns = [
    path(
        "conversations/", ConversationsView.as_view(), name="list-create-conversation"
    ),
    path(
        "conversations/<int:pk>/hide/",
        ConversationsView.as_view(),
        name="delete-conversation",
    ),
    path("conversations/<int:pk>/messages/", MessagesView.as_view(), name="messages"),
]
