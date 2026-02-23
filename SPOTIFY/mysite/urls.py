
from django.contrib import admin
from django.urls import path,include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.contrib.staticfiles.urls import static 
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    path("",include("music.urls")),
    path('admin/', admin.site.urls),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
urlpatterns+=staticfiles_urlpatterns()