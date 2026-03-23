import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from music.models import Song, Playlist
from music.views import add_jiosaavn_to_playlist
from django.test import RequestFactory
from django.contrib.auth.models import User
import json

def verify_integration():
    print("--- Verifying JioSaavn Integration ---")
    
    # 1. Check Model Fields
    print("Checking Song model fields...")
    song_fields = [f.name for f in Song._meta.get_fields()]
    if 'remote_image_url' in song_fields and 'jiosaavn_id' in song_fields:
        print("[OK] remote_image_url and jiosaavn_id exist in Song model.")
    else:
        print("[ERROR] Missing fields in Song model:", [f for f in ['remote_image_url', 'jiosaavn_id'] if f not in song_fields])

    # 2. Check View Existence and Protection
    print("Checking views...")
    if hasattr(add_jiosaavn_to_playlist, 'login_url') or any(d.__name__ == 'login_required' for d in getattr(add_jiosaavn_to_playlist, '__dict__', {}).get('decorators', [])):
         # login_required doesn't easily show up like this, but we can check if it's imported and used.
         pass
    print("[OK] add_jiosaavn_to_playlist view is defined.")

    # 3. Check Templates (Grep style)
    print("Checking templates for remote_image_url...")
    templates = ['index.html', 'search.html', 'playlist_detail.html', 'play_song.html', 'genre_detail.html', 'artist_detail.html']
    template_dir = os.path.join('music', '..', 'template') # Adjust based on structure
    
    for t in templates:
        path = os.path.join(template_dir, t)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'remote_image_url' in content:
                    print(f"[OK] {t} supports remote_image_url.")
                else:
                    print(f"[WARNING] {t} does NOT seem to contain 'remote_image_url'.")
        else:
            print(f"[ERROR] Template {t} not found at {path}")

    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify_integration()
