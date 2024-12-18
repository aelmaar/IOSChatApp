"""
ASGI config for chat_app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Initialize Django settings and setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_app.settings")
django_asgi_application = get_asgi_application()

# Import routing/middleware after Django setup
from notifications.routing import websocket_urlpatterns
from chat_app.middlewares import JWTAuthMiddleware

# Configure protocol routing
application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
