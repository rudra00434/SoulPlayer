from django.forms import ModelForm, TextInput, FileInput, CheckboxSelectMultiple
from .models import Song, Artist, Playlist, UserProfile
from django.contrib.auth.models import User

class SongForm(ModelForm):
    class Meta:
        model=Song
        fields=["title","artist","image","audio_file","duration","song_type"]
        widgets={
            "title":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#3be2c8] focus:ring-1 focus:ring-[#3be2c8] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Enter song title"}),
            "artist":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#3be2c8] focus:ring-1 focus:ring-[#3be2c8] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Enter artist name"}),
            "duration":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#3be2c8] focus:ring-1 focus:ring-[#3be2c8] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "e.g., 3:45"}),
            "song_type":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#3be2c8] focus:ring-1 focus:ring-[#3be2c8] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "e.g., Pop"}),
            "image":FileInput(attrs={"class":"w-full bg-white/5 text-gray-400 file:mr-4 file:py-2.5 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-[#3be2c8] file:to-[#2cdbbd] file:text-[#0b0f19] hover:file:shadow-[0_0_15px_rgba(59,226,200,0.4)] cursor-pointer transition-all rounded-xl"}),
            "audio_file":FileInput(attrs={"class":"w-full bg-white/5 text-gray-400 file:mr-4 file:py-2.5 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-[#3be2c8] file:to-[#2cdbbd] file:text-[#0b0f19] hover:file:shadow-[0_0_15px_rgba(59,226,200,0.4)] cursor-pointer transition-all rounded-xl"}),
        }

class ArtistForm(ModelForm):
    class Meta:
        model=Artist
        fields="__all__"
        widgets={
            "name":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#f472b6] focus:ring-1 focus:ring-[#f472b6] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Enter artist name"}),
            "bio":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#f472b6] focus:ring-1 focus:ring-[#f472b6] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Enter artist bio"}),
            "music_band":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#f472b6] focus:ring-1 focus:ring-[#f472b6] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Enter music band name"}),
            "image":FileInput(attrs={"class":"w-full bg-white/5 text-gray-400 file:mr-4 file:py-2.5 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-fuchsia-500 file:to-purple-500 file:text-white hover:file:shadow-[0_0_15px_rgba(217,70,239,0.4)] cursor-pointer transition-all rounded-xl"}),
        }
class PlaylistForm(ModelForm):
    class Meta:
        model=Playlist
        fields="__all__"
        widgets={
            "name":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#3be2c8] focus:ring-1 focus:ring-[#3be2c8] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Enter playlist name"}),
            "artists":CheckboxSelectMultiple(attrs={"class":"text-[#3be2c8] focus:ring-[#3be2c8] bg-white/5 border-white/10 rounded"}),
            "songs":CheckboxSelectMultiple(attrs={"class":"text-[#3be2c8] focus:ring-[#3be2c8] bg-white/5 border-white/10 rounded"}),
        }
        
class ProfileUpdateForm(ModelForm):
    class Meta:
        model=UserProfile
        fields=["bio"]
        widgets={
            "bio":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#3be2c8] focus:ring-1 focus:ring-[#3be2c8] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Tell us about yourself..."}),
        }
class UserUpdateForm(ModelForm):
    class Meta:
        model=User
        fields=["username", "email"]
        widgets={
            "username":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#3be2c8] focus:ring-1 focus:ring-[#3be2c8] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Username"}),
            "email":TextInput(attrs={"class":"w-full bg-white/5 border border-white/10 focus:border-[#3be2c8] focus:ring-1 focus:ring-[#3be2c8] rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-all backdrop-blur-md", "placeholder": "Email Address"}),
        }
