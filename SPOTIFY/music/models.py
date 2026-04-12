from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Song(models.Model):
    title= models.TextField()
    artist=models.TextField()
    image=models.ImageField(blank=True, null=True)
    audio_file=models.FileField(blank=True, null=True)
    audio_link=models.CharField(max_length=200,blank=True,null=True)
    lyrics=models.TextField(blank=True,null=True)
    duration=models.CharField(max_length=20)
    song_type=models.CharField(max_length=20)
    remote_image_url=models.URLField(blank=True,null=True)
    jiosaavn_id=models.CharField(max_length=50,blank=True,null=True,unique=True)
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

class LikedSong(models.Model):
    user = models.ForeignKey(User, related_name='liked_songs', on_delete=models.CASCADE)
    song = models.ForeignKey(Song, related_name='liked_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'song')  # Prevents duplicate likes
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} liked {self.song.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=200, blank=True, null=True)
    played_songs = models.ManyToManyField(Song, related_name='played_songs', blank=True)
    favorite_artists = models.ManyToManyField(Artist, related_name='favorite_artists', blank=True)
    personality = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Check if profile exists before saving to avoid RelatedObjectDoesNotExist errors
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
        else:
            UserProfile.objects.create(user=instance)

class ListeningRoom(models.Model):
    host=models.ForeignKey(User,related_name='listening_rooms',on_delete=models.CASCADE)
    room_code = models.CharField(max_length=10,unique=True,db_index=True)
    current_song_id = models.CharField(max_length=100,null=True , blank=True)
    is_playing = models.BooleanField(default=False)
    timestamp = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Room {self.room_code} hosted by {self.host.username}"


class Recommendation(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='recommendation_cache')
    recommended_songs=models.JSONField(default=list)
    algorithm_version = models.CharField(max_length=20,default='v1')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendations for {self.user.username}"