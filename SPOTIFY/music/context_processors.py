from .models import Song, Playlist

def sidebar_context(request):
    """Provides common data for the shared sidebar across all templates."""
    # Get last 5 songs for the sidebar 'Last Listening' section
    recent_songs = Song.objects.all().order_by('-id')[:5]
    
    # Get user's playlists if logged in
    user_playlists = []
    if request.user.is_authenticated:
        user_playlists = Playlist.objects.filter(user=request.user)
    else:
        # Fallback to all playlists for public browsing if appropriate, 
        # or just empty
        user_playlists = Playlist.objects.all()[:10]

    return {
        'sidebar_recent_songs': recent_songs,
        'sidebar_playlists': user_playlists,
    }
