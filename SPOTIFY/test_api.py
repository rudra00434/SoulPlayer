import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from music.jiosavan import search_songs, get_song_details

# Test search
results = search_songs('Arijit Singh', limit=3)
for s in results:
    print(f"ID: '{s['id']}' (type: {type(s['id']).__name__})")
    print(f"  title: {s['title']}")
    print(f"  stream_url present: {bool(s.get('stream_url'))}")
    print(f"  image_url present: {bool(s.get('image_url'))}")
    print()

if results:
    sid = results[0]['id']
    print(f"Testing get_song_details('{sid}')...")
    details = get_song_details(sid)
    if details:
        print(f"  Got details: {details['title']} by {details['artist']}")
        print(f"  duration: {details.get('duration')}")
        print(f"  stream_url: {bool(details.get('stream_url'))}")
    else:
        print("  FAILED - returned None!")
