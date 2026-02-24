from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse 
import requests
from .models import Song,Artist,Playlist
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
    context = {"page_obj": page_obj, "artists": artists, "playlists": playlists}
    return render(request, 'index.html', context)


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

def delete_song(request,pk):
    song=get_object_or_404(Song,id=pk)
    song.delete()
    return redirect('index')

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
        
        # --- NLP PROCESSING ---
        is_play_command = False
        target_name = query_lower
        
        if nlp:
            doc = nlp(query_lower)
            # Detect play command by checking for verbs like "play", "stream", "listen"
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

        if is_play_command and songs.exists():
            # Play the first matching song immediately
            return redirect('play_song', pk=songs.first().id)
            
        if artists.exists() and not songs.exists():
            # Redirect to artist if they said "play [artist]" and no such song, or just searched an artist
            return redirect(f"{reverse('artists')}?query={target_name}")

        # Regular search fallback (Not playing immediately, or multiple songs found)
        query = target_name

    else:
        songs = []
        
    context={"songs":songs, "query": query}
    return render(request,'search.html',context)

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
    context={"artist":artist,
             "songs":songs}
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
    songs=Song.objects.filter(song_type=genre)
    context={
        "songs":songs,
        "genre":genre
    }
    return render(request,'genre_detail.html',context)

def voice_search(request):
    return render(request, 'voice_search.html')

def podcasts(request):

    youtube_api_key = getattr(settings, 'YOUTUBE_API_KEY', '')
    query = "music podcast full episode"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=12&q={query}&type=video&key={youtube_api_key}"
    
    videos = []
    try:
        response = requests.get(url)
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
    except Exception as e:
        print(f"Error fetching data from YouTube API: {e}")

    context = {
        'videos': videos
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
        "played_songs": request.user.userprofile.played_songs.all().order_by("-id")[:10], # Last 10 played
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
        
        # Ensure UserProfile exists
        if not hasattr(request.user, 'userprofile'):
            UserProfile.objects.create(user=request.user)
            
        request.user.userprofile.played_songs.add(song)
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)
