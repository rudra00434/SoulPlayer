import random
from collections import Counter
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse 
import requests
from .models import Song,Artist,Playlist,LikedSong
from django.core.paginator import Paginator 
from .forms import SongForm, ArtistForm, PlaylistForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import spacy
from django.db.models import Q
from django.conf import settings
from .models import UserProfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . import jiosavan
from .jiosavan import get_trending_today, get_artist_songs, search_albums, get_album_details
# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('user_login')

def index(request):
    paginator = Paginator(Song.objects.all().order_by('id'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    artists = Artist.objects.all()
    playlists = Playlist.objects.all()
    sidebar_playlists = Playlist.objects.all()[:5]
    sidebar_recent_songs = Song.objects.all().order_by('-id')[:5]

    
    trending_songs = jiosavan.get_trending(limit=20)
    trending_today_songs = get_trending_today(limit=20)
    arijit_songs = get_artist_songs('Arijit Singh', limit=20)
    armaan_songs = get_artist_songs('Armaan Malik', limit=20)
    kk_songs = get_artist_songs('KK', limit=20)
    nostalgia_songs = jiosavan.get_nostalgia_songs(limit=20)
    top_albums = search_albums('bollywood hits', limit=10)

    # Curated: Best of Hindi Songs (Local Database)
    hindi_ids = [97, 96, 95, 92, 11, 98,94]
    best_of_hindi_songs_unsorted = Song.objects.filter(id__in=hindi_ids)
    # Sort to maintain the user's requested order
    best_of_hindi_songs = sorted(
        best_of_hindi_songs_unsorted, 
        key=lambda s: hindi_ids.index(s.id)
    )

    # Curated: Best of Punjabi Songs (Local Database)
    punjabi_ids = [100, 101, 102, 103, 104, 105,106]
    best_of_punjabi_songs_unsorted = Song.objects.filter(id__in=punjabi_ids)
    # Sort to maintain the user's requested order
    best_of_punjabi_songs = sorted(
        best_of_punjabi_songs_unsorted, 
        key=lambda s: punjabi_ids.index(s.id)
    )


    genres = [

        {'id': 'romance', 'name': 'Romance', 'icon': 'fa-heart', 'color': 'from-pink-500 to-fuchsia-600'},
        {'id': 'indie', 'name': 'Indie', 'icon': 'fa-headphones', 'color': 'from-blue-600 to-indigo-800'},
        {'id': 'pop', 'name': 'Pop', 'icon': 'fa-bolt', 'color': 'from-purple-600 to-indigo-700'},
        {'id': 'rock', 'name': 'Rock', 'icon': 'fa-drum', 'color': 'from-red-600 to-rose-700'},
        {'id': 'hip-hop', 'name': 'Hip-Hop', 'icon': 'fa-microphone-alt', 'color': 'from-emerald-500 to-teal-600'},
    ]

    context = {
        "page_obj": page_obj,
        "artists": artists,
        "playlists": playlists,
        "trending_songs": trending_songs,
        "trending_today_songs": trending_today_songs,
        "arijit_songs": arijit_songs,
        "armaan_songs": armaan_songs,
        "kk_songs": kk_songs,
        "nostalgia_songs": nostalgia_songs,
        "top_albums": top_albums,
        "best_of_hindi_songs": best_of_hindi_songs,
        "best_of_punjabi_songs": best_of_punjabi_songs,
        "genres": genres,
        "sidebar_playlists": sidebar_playlists,
        "sidebar_recent_songs": sidebar_recent_songs,
    }
    return render(request, 'index.html', context)


@login_required(login_url='user_login')
def add_song(request):
    if request.method=='POST':
        form=SongForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form=SongForm()
    
    context={"form":form}
    return render(request,'add_song.html',context)


def play_song(request, pk):
    song = get_object_or_404(Song, id=pk)
    
    # Logic for Next/Previous
    songs = list(Song.objects.all().order_by('id'))
    current_index = songs.index(song)
    
    previous_song = songs[current_index - 1] if current_index > 0 else None
    next_song = songs[current_index + 1] if current_index < len(songs) - 1 else None

    context = {
        "song": song,
        "previous_song": previous_song,
        "next_song": next_song,
    }
    return render(request, 'play_song.html', context)

@login_required(login_url='user_login')
def delete_song(request, pk):
    if request.method == 'POST':
        song = get_object_or_404(Song, id=pk)
        song.delete()
        return redirect('index')
    return redirect('index')

@login_required(login_url='user_login')
def update_song(request,pk):
    song=get_object_or_404(Song,id=pk)
    if request.method=='POST':
        form=SongForm(request.POST,request.FILES,instance=song)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form=SongForm(instance=song)
        
    context={"form":form}
    return render(request,'add_song.html',context)



# Load NLP model globally so it's only loaded once when server starts
try:
    nlp = spacy.load("en_core_web_sm")
except (OSError, ImportError):
    nlp = None

def search(request):
    query=request.GET.get('query')
    if query:
        query_lower = query.lower().strip()
        
        
        is_play_command = False
        target_name = query_lower
        
        if nlp:
            doc = nlp(query_lower)
            
            is_play_command = any(token.lemma_ in ["play", "stream", "listen", "start", "hear"] for token in doc)
            
            # Words to strip out so the search is cleaner
            stop_words = {"to", "some", "a", "an", "the", "song", "songs", "music", "track", "tracks", "play", "playing", "listen", "listening", "hear"}
            
            target_tokens = [
                token.text for token in doc 
                if token.pos_ not in ["VERB", "AUX"] and token.text.lower() not in stop_words
            ]
            
            if target_tokens:
                target_name = " ".join(target_tokens).strip()

        # If NLP is not available, do a basic strip
        if not nlp:
            is_play_command = query_lower.startswith("play ")
            if is_play_command:
                target_name = query_lower.replace("play ", "", 1).strip()
            
            # Simple word removal fallback
            for word in [" some ", " songs", " song", " music", " tracks", " track", " the "]:
                target_name = target_name.replace(word, " ")
            target_name = target_name.strip()

        # Ensure target_name is not empty
        if not target_name:
            target_name = query_lower
            
        # --- SMART ROUTING LOGIC ---
        # 1. Broadly search for Songs matching title, artist, or genre
        songs = Song.objects.filter(Q(title__icontains=target_name) | Q(artist__icontains=target_name) | Q(song_type__icontains=target_name))
        
        # 2. Broadly search for Artists matching name or band
        artists = Artist.objects.filter(Q(name__icontains=target_name) | Q(music_band__icontains=target_name))

        if is_play_command and songs.count() == 1:
            return redirect('play_song', pk=songs.first().id)
            
        if artists.exists() and not songs.exists():
            # Redirect to artist if they said "play [artist]" and no such song, or just searched an artist
            return redirect(f"{reverse('artists')}?query={target_name}")

        # Regular search fallback (Not playing immediately, or multiple songs found)
        query = target_name

        # --- JIOSAAVN SEARCH ---
        jiosaavn_songs = jiosavan.search_songs(target_name, limit=20)

        # If voice command "play X" resulted in no local song but one JioSaavn song, play it
        if is_play_command and not songs.exists() and len(jiosaavn_songs) > 0:
            return redirect('play_jiosaavn_song', song_id=jiosaavn_songs[0]['id'])

    else:
        songs = []
        jiosaavn_songs = []
        
    # Common genres for UI cards
    genres = [
        {'id': 'romance', 'name': 'Romance', 'icon': 'fa-heart', 'color': 'from-pink-500 to-fuchsia-600'},
        {'id': 'indie', 'name': 'Indie', 'icon': 'fa-headphones', 'color': 'from-blue-600 to-indigo-800'},
        {'id': 'pop', 'name': 'Pop', 'icon': 'fa-bolt', 'color': 'from-purple-600 to-indigo-700'},
        {'id': 'rock', 'name': 'Rock', 'icon': 'fa-drum', 'color': 'from-red-600 to-rose-700'},
        {'id': 'hip-hop', 'name': 'Hip-Hop', 'icon': 'fa-microphone-alt', 'color': 'from-emerald-500 to-teal-600'},
    ]

    # Fetch artists for the "Popular Artists" section (newest first)
    artists = Artist.objects.all()
    
    playlists = Playlist.objects.filter(user=request.user) if request.user.is_authenticated else []
    sidebar_playlists = Playlist.objects.all()[:5]
    sidebar_recent_songs = Song.objects.all().order_by('-id')[:3]
    context = {
        "songs": songs, 
        "query": query, 
        "jiosaavn_songs": jiosaavn_songs, 
        "playlists": playlists, 
        "genres": genres,
        "artists": artists,
        "sidebar_playlists": sidebar_playlists,
        "sidebar_recent_songs": sidebar_recent_songs,
    }
    return render(request, 'search.html', context)

@login_required(login_url='user_login')
def add_artist(request):
    if request.method=='POST':
        form=ArtistForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form=ArtistForm()
        
    context={"form":form}
    return render(request,'add_artist.html',context)

def artist_list(request):
    query=request.GET.get('query')
    if query:
        artists=Artist.objects.filter(name__icontains=query)
    else:
        artists=Artist.objects.all()
    context={"artists":artists, "query":query}
    return render(request,'artists.html',context) 

    

def artist_detail(request,pk):
    artist=get_object_or_404(Artist,id=pk)
    songs=Song.objects.filter(artist__icontains=artist.name)
    
    # Also fetch JioSaavn songs by this artist
    jiosaavn_songs = jiosavan.search_songs(artist.name, limit=10)
    
    context={"artist":artist,
             "songs":songs,
             "jiosaavn_songs": jiosaavn_songs}
    return render(request,'artist_detail.html',context)

@login_required(login_url='user_login')
def create_playlist(request):
    if request.method=='POST':
        form=PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.user = request.user
            playlist.save()
            form.save_m2m() # Required to save ManyToMany fields like artists and songs
            return redirect('index')
    else:
        form=PlaylistForm()
         
    context={"form":form}
    return render(request,'create_playlist.html',context)

@login_required(login_url='user_login')
def playlists(request):
    playlists=Playlist.objects.filter(user=request.user)
    context={"playlists":playlists}
    return render(request,'playlists.html',context)

def playlist_detail(request,pk):
    playlist=get_object_or_404(Playlist,id=pk)
    songs=playlist.songs.all()
    context={
             "playlist":playlist,
             "songs":songs
             }
    return render(request,'playlist_detail.html',context)

def add_to_playlist(request,pk):
    playlist=get_object_or_404(Playlist,id=pk)
    
    if request.method == 'POST':
        selected_song_ids = request.POST.getlist('selected_songs')
        if selected_song_ids:
            # Get the actual Song objects
            songs_to_add = Song.objects.filter(id__in=selected_song_ids)
            # Add them to the ManyToMany field (avoids duplicates automatically)
            playlist.songs.add(*songs_to_add)
        return redirect('playlist_detail', pk=playlist.id)

    songs=Song.objects.all()
    context={
          "playlist":playlist,
          "songs":songs
    }
    return render(request,'add_to_playlist.html',context)
        
def genre_detail(request,genre):
    # Use icontains for flexible matching (e.g. 'Romance' matches 'romance')
    songs=Song.objects.filter(song_type__icontains=genre)
    
    # Also fetch JioSaavn songs for this genre
    jiosaavn_songs = jiosavan.search_songs(f"{genre} songs", limit=10)
    
    context={
        "songs":songs,
        "genre":genre,
        "jiosaavn_songs": jiosaavn_songs,
    }
    return render(request,'genre_detail.html',context)

def voice_search(request):
    return render(request, 'voice_search.html')

def podcasts(request):

    youtube_api_key = getattr(settings, 'YOUTUBE_API_KEY', '')
    query = "music podcast full episode"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=12&q={query}&type=video&key={youtube_api_key}"
    
    videos = []
    error_message = None
    
    if not youtube_api_key:
        error_message = "YouTube API Key is missing. Please set YOUTUBE_API_KEY in your environment or settings.py."
    else:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if 'items' in data:
                for item in data['items']:
                    video = {
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails']['high']['url'],
                        'video_id': item['id']['videoId'],
                        'channel_title': item['snippet']['channelTitle']
                    }
                    videos.append(video)
            elif 'error' in data:
                error_message = f"YouTube API Error: {data['error'].get('message', 'Unknown error')}"
        except Exception as e:
            error_message = f"Connection Error: Could not reach YouTube API. {str(e)}"
            print(f"Error fetching data from YouTube API: {e}")

    context = {
        'videos': videos,
        'error_message': error_message
    }
    return render(request, 'podcasts.html', context)

@login_required(login_url="user_login")
def profile(request):
    # Ensure UserProfile exists (for users created before the signal was added)
    if not hasattr(request.user, 'userprofile'):
        
        UserProfile.objects.create(user=request.user)
        
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.userprofile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f"Your profile has been updated!")
            return redirect("profile")
            
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.userprofile)
        
    context = {
        "u_form": u_form,
        "p_form": p_form,
        "played_songs": request.user.userprofile.played_songs.all().order_by("-id"),
        "favorite_artists": request.user.userprofile.favorite_artists.all()
    }
    return render(request, "profile.html", context)

@login_required(login_url="user_login")
def toggle_favorite_artist(request, pk):
    artist = get_object_or_404(Artist, id=pk)
    user_profile = request.user.userprofile
    if artist in user_profile.favorite_artists.all():
        user_profile.favorite_artists.remove(artist)
    else:
        user_profile.favorite_artists.add(artist)
    return redirect("artist_detail", pk=pk)


@csrf_exempt
def record_play(request, pk):
    if request.method == "POST" and request.user.is_authenticated:
        
        song = get_object_or_404(Song, id=pk)
        
        # Ensure UserProfile exists and add song
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.played_songs.add(song)
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)

@login_required(login_url='user_login')
def last_listening(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    played_songs = profile.played_songs.all().order_by("-id")
    return render(request, 'last_listening.html', {'played_songs': played_songs})

import random, string
from .models import ListeningRoom
from .jiosavan import search_songs

@login_required(login_url='user_login')
def api_search_songs(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'status': 'success', 'results': []})
        
    results = []
    
    # 1. Search Local Database first
    from django.db.models import Q
    from .models import Song
    local_songs = Song.objects.filter(Q(title__icontains=query) | Q(artist__icontains=query), jiosaavn_id__isnull=True)[:5]
    for ls in local_songs:
        img_url = ls.image.url if ls.image else (ls.remote_image_url if ls.remote_image_url else 'https://placehold.co/40x40/1e293b/ffffff?text=M')
        results.append({
            'id': ls.id,
            'title': ls.title,
            'artist': ls.artist,
            'image_url': img_url,
            'source': 'local'
        })
        
    # 2. Search JioSaavn API and neatly merge them
    from .jiosavan import search_songs
    jio_results = search_songs(query, limit=10)
    if jio_results:
        results.extend(jio_results)
        
    return JsonResponse({'status': 'success', 'results': results})

@csrf_exempt
@login_required(login_url='user_login')
def api_update_room_song(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
        
        room_code = data.get('room_code', '').upper()
        song_id = data.get('song_id', '')
        
        room = ListeningRoom.objects.filter(room_code=room_code, host=request.user).first()
        if room:
            room.current_song_id = str(song_id)
            room.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Not authorized or room not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required(login_url='user_login')
def jam_lobby(request):
    return render(request, 'jam_lobby.html')

@csrf_exempt
@login_required(login_url='user_login')
def create_room(request):
    if request.method == 'POST':
        import json
        
        # Parse logic differently because form data comes differently now
        try:
            data = json.loads(request.body)
            current_song_id = data.get('song_id', '')
        except:
            current_song_id = request.POST.get('song_id', '')
            
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        ListeningRoom.objects.create(
            host=request.user, 
            room_code=code, 
            current_song_id=str(current_song_id)
        )
        return JsonResponse({'status': 'success', 'room_code': code})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required(login_url='user_login')
def jam_room(request, room_code):
    room = get_object_or_404(ListeningRoom, room_code=room_code.upper())
    
    # We must fetch the song information to pass to the template
    song = None
    is_jiosaavn = False
    if room.current_song_id:
        if room.current_song_id.isdigit():
            from .models import Song
            song = Song.objects.filter(id=int(room.current_song_id)).first()
        else:
            # It's a jiosaavn ID. We need to fetch it from the API if it's not cached locally.
            # Local cache check
            from .models import Song
            song = Song.objects.filter(jiosaavn_id=room.current_song_id).first()
            if not song:
                from .jiosavan import get_song_details
                song_details = get_song_details(room.current_song_id)
                if song_details:
                    # Mock a temporary object for the template to parse
                    class TempSong:
                        def __init__(self, d):
                            self.id = d.get('id', '')
                            self.title = d.get('title', '')
                            self.artist = d.get('artist', '')
                            self.stream_url = d.get('stream_url', '')
                            self.remote_image_url = d.get('image_url', '')
                    song = TempSong(song_details)
            is_jiosaavn = True
            
    is_host = request.user == room.host
    context = {
        'room': room,
        'song': song,
        'is_jiosaavn': is_jiosaavn,
        'is_host': is_host,
    }
    return render(request, 'jam_room.html', context)


@csrf_exempt
def record_play_jiosaavn(request, song_id):
    """Record a JioSaavn song play in user's listening history.
    Syncs the song to local DB first if it doesn't exist."""
    
    if request.method == "POST" and request.user.is_authenticated:
        # Check if this JioSaavn song already exists in local DB
        song = Song.objects.filter(jiosaavn_id=song_id).first()
        
        if not song:
            # Fetch details from JioSaavn and create local Song entry
            details = jiosavan.get_song_details(song_id)
            if details:
                try:
                    song = Song.objects.create(
                        title=details['title'],
                        artist=details['artist'],
                        duration=details.get('duration', '0:00'),
                        song_type=details.get('language', 'hindi').capitalize(),
                        language=details.get('language', ''),
                        album=details.get('album', ''),
                        audio_link=details['stream_url'],
                        remote_image_url=details['image_url'],
                        jiosaavn_id=song_id
                    )
                except Exception as e:
                    print(f"Error syncing JioSaavn song: {e}")
                    return JsonResponse({"status": "error", "message": str(e)}, status=500)
            else:
                return JsonResponse({"status": "error", "message": "Song not found on JioSaavn"}, status=404)
        
        # Ensure UserProfile exists and add song
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.played_songs.add(song)
        return JsonResponse({"status": "success"})
    
    return JsonResponse({"status": "error"}, status=400)

def play_jiosaavn_song(request, song_id):
    """Full-screen player for a JioSaavn song (fetched via API)."""
    song = jiosavan.get_song_details(song_id)
    
    # Ensure db_song is available for unregistered users too
    db_song = Song.objects.filter(jiosaavn_id=song_id).first()

    # Fallback to local DB cache if API fails
    if not song:
        if db_song:
            song = {
                'id': db_song.jiosaavn_id,
                'title': db_song.title,
                'artist': db_song.artist,
                'image_url': db_song.remote_image_url,
                'stream_url': db_song.audio_link,
                'duration': db_song.duration,
                'duration_seconds': 0,
                'album': db_song.album,
                'language': db_song.language,
            }
        else:
            return render(request, 'play_song.html', {'error': 'Song not found on JioSaavn and no local cache exists.'})

    # Record play history if authenticated
    if request.user.is_authenticated:
        # Sync to DB if not exists
        if not db_song:
            try:
                db_song = Song.objects.create(
                    title=song['title'],
                    artist=song['artist'],
                    duration=song.get('duration', '0:00'),
                    song_type=song.get('language', 'hindi').capitalize(),
                    language=song.get('language', ''),
                    album=song.get('album', ''),
                    audio_link=song['stream_url'],
                    remote_image_url=song['image_url'],
                    jiosaavn_id=song_id
                )
            except Exception as e:
                print(f"Error syncing JioSaavn song in view: {e}")
        
        if db_song:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.played_songs.add(db_song)

    # Get similar song suggestions for "up next"
    suggestions = jiosavan.get_song_suggestions(song_id, limit=8)

    # Build previous/next dynamically from suggestions instead of purely local DB 
    # to guarantee the left/right buttons always function for streaming
    previous_song = None
    next_song = None

    if suggestions:
        candidates = [s for s in suggestions if str(s.get('id')) != str(song_id)]
        if len(candidates) >= 2:
            next_song = candidates[0]
            previous_song = candidates[-1] # use the last suggestion as previous
        elif len(candidates) == 1:
            next_song = candidates[0]
            previous_song = None

    context = {
        "song": song,
        "is_jiosaavn": True,
        "suggestions": suggestions,
        "previous_song": previous_song,
        "next_song": next_song,
    }
    return render(request, 'play_song.html', context)


def jiosaavn_search_api(request):
    """JSON API endpoint for AJAX JioSaavn search (used by voice search etc)."""
    query = request.GET.get('query', '')
    if not query:
        return JsonResponse({'results': []})
    results = jiosavan.search_songs(query, limit=10)
    return JsonResponse({'results': results})

@login_required(login_url='user_login')
def add_jiosaavn_to_playlist(request):
    if request.method == 'POST':
        song_id = request.POST.get('song_id')
        playlist_id = request.POST.get('playlist_id')
        
        if not song_id or not playlist_id:
            return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)
            
        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        
        # Check if song already exists in local DB
        song = Song.objects.filter(jiosaavn_id=song_id).first()
        
        if not song:
            # Sync from JioSaavn
            details = jiosavan.get_song_details(song_id)
            if details:
                song = Song.objects.create(
                    title=details['title'],
                    artist=details['artist'],
                    duration=details.get('duration', '3:00'),
                    song_type=details.get('language', 'hindi').capitalize(),
                    language=details.get('language', ''),
                    album=details.get('album', ''),
                    audio_link=details['stream_url'],
                    remote_image_url=details['image_url'],
                    jiosaavn_id=song_id
                )
        
        if song:
            playlist.songs.add(song)
            return JsonResponse({'status': 'success', 'message': f'"{song.title}" added to {playlist.name}'})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        messages.success(request, "Your message has been sent successfully!")
        return redirect('contact')
    return render(request, 'contact.html')

@login_required(login_url='user_login')
def recommendations(request):
    """Personalized 'Made For You' recommendations page powered by ML pipeline."""
    from .recommendation import get_recommendations_for_user

    rec_data = get_recommendations_for_user(request.user, n=30)
    
    # Separate local songs and JioSaavn songs for template rendering
    local_songs = []
    jiosaavn_songs = []
    for song in rec_data['songs']:
        if song.jiosaavn_id:
            jiosaavn_songs.append(song)
        else:
            local_songs.append(song)

    playlists = Playlist.objects.filter(user=request.user) if request.user.is_authenticated else []

    context = {
        'recommended_songs': rec_data['songs'],
        'local_songs': local_songs,
        'jiosaavn_songs': jiosaavn_songs,
        'algorithm': rec_data['algorithm'],
        'updated_at': rec_data['updated_at'],
        'source': rec_data['source'],
        'total_count': len(rec_data['songs']),
        'playlists': playlists,
    }
    return render(request, 'recommendations.html', context)

def immersive_player(request):
    """Immersive 3D audio-reactive music visualizer with optional WebXR VR mode."""
    trending_songs = jiosavan.get_trending(limit=20)
    trending_today = get_trending_today(limit=10)

    # Combine and deduplicate
    seen_ids = set()
    all_songs = []
    for song in trending_songs + trending_today:
        if song['id'] not in seen_ids:
            seen_ids.add(song['id'])
            all_songs.append(song)

    context = {
        'immersive_songs': all_songs[:30],
    }
    return render(request, 'immersive_player.html', context)

@login_required(login_url='user_login')
def liked_songs(request):
    liked = LikedSong.objects.filter(user=request.user).select_related('song')
    songs = [like.song for like in liked]
    
    recommended_songs = []
    recommendation_title = "More of what you like"
    
    if songs:
        # Find the most common artist in user's liked songs
        artists = [s.artist for s in songs if s.artist and s.artist != 'Unknown Artist']
        if artists:
            # Get the most common artist (or randomly pick one of the top 3)
            most_common = Counter(artists).most_common(3)
            chosen_artist_tuple = random.choice(most_common)
            chosen_artist = chosen_artist_tuple[0]
            
            # Use JioSaavn API to find more songs by this artist
            jiosavan_results = jiosavan.search_songs(chosen_artist, limit=12)
            
            # Filter out songs the user already liked
            liked_jiosaavn_ids = {s.jiosaavn_id for s in songs if s.jiosaavn_id}
            liked_local_titles = {s.title.lower() for s in songs if not s.jiosaavn_id}
            
            for s in jiosavan_results:
                if s['id'] not in liked_jiosaavn_ids and s['title'].lower() not in liked_local_titles:
                    recommended_songs.append(s)
                if len(recommended_songs) >= 5: # Limit to 5 for UI consistency
                    break
                    
            recommendation_title = f"More hits of {chosen_artist}"
            
    # Default fallback
    if not recommended_songs:
        recommended_songs = jiosavan.get_trending(limit=5)
        
    context = {
        'songs': songs,
        'recommended_songs': recommended_songs[:5],
        'recommendation_title': recommendation_title
    }
    return render(request, 'liked_songs.html', context)


@csrf_exempt
@login_required(login_url='user_login')
def toggle_like_song(request, pk):
    """Toggle like/unlike for a local DB song. Returns JSON for AJAX."""
    if request.method == 'POST':
        song = get_object_or_404(Song, id=pk)
        liked, created = LikedSong.objects.get_or_create(user=request.user, song=song)
        if not created:
            # Already liked → unlike it
            liked.delete()
            return JsonResponse({'status': 'unliked', 'liked': False})
        return JsonResponse({'status': 'liked', 'liked': True})
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)


@csrf_exempt
@login_required(login_url='user_login')
def toggle_like_jiosaavn(request, song_id):
    """Toggle like/unlike for a JioSaavn song. Auto-syncs to local DB if needed."""
    if request.method == 'POST':
        # Check if JioSaavn song already exists in local DB
        song = Song.objects.filter(jiosaavn_id=song_id).first()

        if not song:
            # Sync from JioSaavn API first
            details = jiosavan.get_song_details(song_id)
            if details:
                try:
                    song = Song.objects.create(
                        title=details['title'],
                        artist=details['artist'],
                        duration=details.get('duration', '0:00'),
                        song_type=details.get('language', 'hindi').capitalize(),
                        language=details.get('language', ''),
                        album=details.get('album', ''),
                        audio_link=details['stream_url'],
                        remote_image_url=details['image_url'],
                        jiosaavn_id=song_id
                    )
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            else:
                return JsonResponse({'status': 'error', 'message': 'Song not found on JioSaavn'}, status=404)

        # Toggle like
        liked, created = LikedSong.objects.get_or_create(user=request.user, song=song)
        if not created:
            liked.delete()
            return JsonResponse({'status': 'unliked', 'liked': False})
        return JsonResponse({'status': 'liked', 'liked': True})
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)


@login_required(login_url='user_login')
def check_liked(request):
    """Check if a song is liked by the current user. Used by AJAX on page load."""
    song_id = request.GET.get('song_id', '')
    jiosaavn_id = request.GET.get('jiosaavn_id', '')

    if song_id:
        is_liked = LikedSong.objects.filter(user=request.user, song_id=song_id).exists()
    elif jiosaavn_id:
        song = Song.objects.filter(jiosaavn_id=jiosaavn_id).first()
        is_liked = LikedSong.objects.filter(user=request.user, song=song).exists() if song else False
    else:
        is_liked = False

    return JsonResponse({'liked': is_liked})

# ==========================================
# INTERNET RADIO VIEWS
# ==========================================
from . import radio_api

def radio_stations(request):
    """View to browse live internet radio stations."""
    stations = radio_api.get_top_indian_stations(limit=50)
    
    context = {
        'stations': stations,
        'total_stations': len(stations)
    }
    return render(request, 'radio_stations.html', context)

def play_radio(request, station_uuid):
    """View to play a live internet radio stream in the global player."""
    station = radio_api.get_station_by_uuid(station_uuid)
    
    if not station:
        return render(request, 'play_radio.html', {'error': 'Radio station stream could not be loaded or is offline.'})
        
    context = {
        'station': station,
    }
    return render(request, 'play_radio.html', context)


def album_detail(request, album_id):
    """View to show the details of an album and its tracklist."""
    album = get_album_details(album_id)
    if not album:
        from django.http import Http404
        raise Http404("Album not found or API error")
    
    context = {
        'album': album,
        'songs': album.get('songs', []),
    }
    return render(request, 'album_detail.html', context)
