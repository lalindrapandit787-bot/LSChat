import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","ludochat.settings")
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from chat.routing import websocket_urlpatterns
application=ProtocolTypeRouter({"http":get_asgi_application(),"websocket":AuthMiddlewareStack(URLRouter(websocket_urlpatterns))})
