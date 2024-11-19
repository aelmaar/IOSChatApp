from django.urls import path
from .views import FriendshipsView

urlpatterns = [
    path(
        "friendships/",
        FriendshipsView.as_view(),
        name="create-list-reject-accept-friendships",
    ),
    path("friendships/<int:pk>/", FriendshipsView.as_view(), name="retrieve-friendship"),
]
