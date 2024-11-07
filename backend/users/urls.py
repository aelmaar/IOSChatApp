from .views import RegisterView, LoginView, OAuthGoogleCallbackView, OAuthGoogleLoginView
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('oauth/google/callback/', OAuthGoogleCallbackView.as_view(), name='oauth-google-callback'),
]
