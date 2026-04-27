from django.urls import re_path
from . import consumers

websocket_urlpatterns=[
    re_path(r'ws/room/(?P<room_code>\w+)/$', consumers.ListeningRoomConsumer.as_asgi()),
    re_path(r'ws/playlist/(?P<playlist_id>\d+)/$', consumers.PlaylistConsumer.as_asgi()),
]