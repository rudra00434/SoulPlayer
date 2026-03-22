import os
import sys
import django

# Setup Django environment
sys.path.append(r'c:\Users\tatai\pyproject\spotify\SPOTIFY')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from music import jiosavan

def test_jiosaavn():
    print("--- Testing JioSaavn Search ---")
    results = jiosavan.search_songs("Arijit Singh", limit=2)
    for r in results:
        print(f"Found: {r['title']} by {r['artist']} (ID: {r['id']})")
        if r['stream_url']:
            print(f"  Stream URL: {r['stream_url'][:50]}...")
        else:
            print("  NO STREAM URL FOUND")

    if results:
        song_id = results[0]['id']
        print(f"\n--- Testing Song Details for {song_id} ---")
        details = jiosavan.get_song_details(song_id)
        if details:
            print(f"Details Title: {details['title']}")
            print(f"Stream: {details['stream_url'][:50]}...")
        else:
            print("DETAILS TEST FAILED")

        print("\n--- Testing Trending ---")
        trending = jiosavan.get_trending(limit=3)
        for t in trending:
            print(f"Trending: {t['title']} (ID: {t['id']})")

if __name__ == "__main__":
    test_jiosaavn()
