from django.db import models
class Song(models.Model):
    title= models.TextField()
    artist=models.TextField()
    image=models.ImageField()
    audio_file=models.FileField()
    audio_link=models.CharField(max_length=200,blank=True,null=True)
    lyrics=models.TextField(blank=True,null=True)
    duration=models.CharField(max_length=20)
    song_type=models.CharField(max_length=20)
    paginate_by=2
    
    def __str__(self):
        return self.title
class Artist(models.Model):
    name=models.CharField(max_length=200)
    image=models.ImageField(upload_to='artist_images/')
    bio=models.TextField()
    music_band=models.CharField(max_length=200)

    def __str__(self):
        return self.name
    
from django.contrib.auth.models import User

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name=models.CharField(max_length=200)
    artists=models.ManyToManyField(Artist,related_name='playlists',blank=True)
    songs=models.ManyToManyField(Song,related_name='playlists',blank=True)

    def __str__(self):
        return self.name