from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    


class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name=models.CharField(max_length=200)
    artists=models.ManyToManyField(Artist,related_name='playlists',blank=True)
    songs=models.ManyToManyField(Song,related_name='playlists',blank=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=200, blank=True, null=True)
    played_songs = models.ManyToManyField(Song, related_name='played_songs', blank=True)
    favorite_artists = models.ManyToManyField(Artist, related_name='favorite_artists', blank=True)
    personality = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()