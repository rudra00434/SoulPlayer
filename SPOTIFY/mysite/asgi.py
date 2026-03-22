import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import music.routing

application = ProtocolTypeRouter({
    "http" : django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(music.routing.websocket_urlpatterns)
    ),
})
