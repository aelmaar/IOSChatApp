from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model

Users = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):

    @database_sync_to_async
    def get_user(self, token):
        try:
            # Validate the token and extracts user id from it
            access_token = AccessToken(token)
            user_id = access_token.payload.get("user_id", None)

            # Get the user instance
            user = Users.objects.get(pk=user_id)

            return user

        except (TokenError, Users.DoesNotExist):
            return None

    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        access_token = None

        if b"authorization" in headers:
            try:
                # Get access token from headers
                auth_header = headers[b"authorization"].decode()
                if auth_header.startswith("Bearer"):
                    access_token = auth_header.split(" ")[1]

            except (UnicodeDecodeError, IndexError):
                pass

        scope["user"] = await self.get_user(access_token)

        return await super().__call__(scope, receive, send)
