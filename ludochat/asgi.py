import os
import django
from django.core.asgi import get_asgi_application

# 1. Django Settings Modules Set गर्ने
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ludochat.settings')

# 2. AppRegistryNotReady Error हटाउन पहिले Django setup गर्ने
django.setup()

# 3. get_asgi_application() र Channels Routing Import गर्ने
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing  # तपाईंको routing file

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})