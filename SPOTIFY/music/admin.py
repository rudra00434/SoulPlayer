from django.contrib import admin
from .models import Song,Artist,Playlist,Recommendation,ListeningRoom
admin.site.register(Song)
admin.site.register(Artist)
admin.site.register(Playlist)
admin.site.register(Recommendation)
admin.site.register(ListeningRoom)

# Register your models here.
