from .views import (
    RegisterView,
    LoginView,
    OAuthGoogleCallbackView,
    OAuth42CallbackView,
    UpdateProfileView,
    UpdatePasswordView,
    UpdatePictureView,
    DeletePictureView,
    BlacklistView,
    UsersSearchView,
    UserProfileView,
    DeleteAccountView,
)
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh_token"),
    path(
        "oauth/google/callback/",
        OAuthGoogleCallbackView.as_view(),
        name="oauth-google-callback",
    ),
    path("oauth/42/callback/", OAuth42CallbackView.as_view(), name="oauth-42-callback"),
    path("update-profile/", UpdateProfileView.as_view(), name="update-profile"),
    path("update-password/", UpdatePasswordView.as_view(), name="update-password"),
    path("update-picture/", UpdatePictureView.as_view(), name="update-picture"),
    path("delete-picture/", DeletePictureView.as_view(), name="delete-picture"),
    path("blacklist/", BlacklistView.as_view(), name="blacklist"),
    path("users/search/", UsersSearchView.as_view(), name="search-users"),
    path("users/<str:username>/", UserProfileView.as_view(), name="user-profile"),
    path("delete-account/", DeleteAccountView.as_view(), name="delete-account"),
]
