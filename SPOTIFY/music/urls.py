from django.urls import path
from . import views 

urlpatterns =[
    path('',views.index,name='index'),
    path('add_song/',views.add_song,name='add_song'),
    path('play_song/<int:pk>/',views.play_song,name='play_song'),
    path('delete_song/<int:pk>/',views.delete_song,name='delete_song'),
    path('update_song/<int:pk>/',views.update_song,name='update_song'),
    path('add_artist/',views.add_artist,name='add_artist'),
    path('artist_list/',views.artist_list,name='artists'),
    path('artist_detail/<int:pk>/',views.artist_detail,name='artist_detail'),
    path('search/',views.search,name='search'),
    path('voice_search/',views.voice_search,name='voice_search'),
    path('podcasts/',views.podcasts,name='podcasts'),
    path('create_playlist/',views.create_playlist,name='create_playlist'),
    path('playlists/',views.playlists,name='playlists'),
    path('playlist_detail/<int:pk>/',views.playlist_detail,name='playlist_detail'),
    path('add_to_playlist/<int:pk>/',views.add_to_playlist,name='add_to_playlist'),
    path('genre_detail/<str:genre>/',views.genre_detail,name='genre_detail'),
    path('register/',views.register,name='register'),
    path('login/',views.user_login,name='user_login'),
    path('logout/',views.user_logout,name='user_logout'),
    path('profile/',views.profile,name='profile'),
    path('toggle_favorite_artist/<int:pk>/', views.toggle_favorite_artist, name='toggle_favorite_artist'),
    path('record_play/<int:pk>/', views.record_play, name='record_play'),
]