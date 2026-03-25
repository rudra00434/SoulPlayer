"""
JioSaavn API Service Module
Wraps the unofficial JioSaavn API (saavn.sumit.co) for song search, details, and streaming.
No API key required.
"""
import requests
from django.conf import settings
from django.core.cache import cache

API_BASE = getattr(settings, 'JIOSAAVN_API_BASE', 'https://saavn.sumit.co')
REQUEST_TIMEOUT = 8  # seconds

# Official JioSaavn chart playlist IDs (stable, curated by JioSaavn)
CHART_PLAYLIST_IDS = [
    '159144718',  # Top 50 Hindi
    '158543369',  # Trending Today
    '92238273',   # Bollywood Hits
]

# Fallback queries used only if playlist endpoint fails
_FALLBACK_QUERIES = [
    'new bollywood hit songs 2026',
    'new hindi hits 2026',
    'top 50 songs 2026',
    'new punjabi songs 2026',
]


def _get_best_quality(items, fallback=''):

    if not items:
        return fallback
    quality_order = ['320kbps', '160kbps', '96kbps', '48kbps', '12kbps']
    url_map = {item.get('quality', ''): item.get('url', '') for item in items}
    for q in quality_order:
        if q in url_map and url_map[q]:
            return url_map[q]
    return items[-1].get('url', fallback)


def _get_best_image(items, fallback=''):
    """Extract the highest quality image URL from an array of {quality, url} dicts."""
    if not items:
        return fallback
    quality_order = ['500x500', '150x150', '50x50']
    url_map = {item.get('quality', ''): item.get('url', '') for item in items}
    for q in quality_order:
        if q in url_map and url_map[q]:
            return url_map[q]
    return items[-1].get('url', fallback)


def _format_duration(seconds):
    """Convert seconds (int) to 'M:SS' format string."""
    if not seconds:
        return '0:00'
    try:
        seconds = int(seconds)
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
    except (ValueError, TypeError):
        return '0:00'


def _normalize_song(song_data):
    """Convert raw JioSaavn API song data into a normalized dict."""
    if not song_data:
        return None

    artists = song_data.get('artists', {})
    primary_artists = artists.get('primary', [])
    artist_name = ', '.join(a.get('name', '') for a in primary_artists) if primary_artists else ''

    if not artist_name:
        all_artists = artists.get('all', [])
        artist_name = ', '.join(a.get('name', '') for a in all_artists[:3]) if all_artists else 'Unknown Artist'

    return {
        'id': song_data.get('id', ''),
        'title': song_data.get('name', 'Unknown Title'),
        'artist': artist_name,
        'image_url': _get_best_image(song_data.get('image', [])),
        'stream_url': _get_best_quality(song_data.get('downloadUrl', [])),
        'duration': _format_duration(song_data.get('duration')),
        'duration_seconds': song_data.get('duration', 0),
        'album': song_data.get('album', {}).get('name', ''),
        'year': song_data.get('year', ''),
        'language': song_data.get('language', ''),
        'play_count': song_data.get('playCount', 0),
        'has_lyrics': song_data.get('hasLyrics', False),
        'source': 'jiosaavn',
    }


def _normalize_songs_list(raw_list):
    """
    Safely normalize a list of raw song dicts.
    Avoids calling _normalize_song twice per item (was wasteful in old code).
    """
    results = []
    for s in raw_list:
        normalized = _normalize_song(s)
        if normalized:
            results.append(normalized)
    return results


def search_songs(query, page=0, limit=10):
    """
    Search JioSaavn for songs.
    Returns a list of normalized song dicts.
    """
    try:
        response = requests.get(
            f"{API_BASE}/api/search/songs",
            params={'query': query, 'page': page, 'limit': limit},
            timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get('success') and data.get('data', {}).get('results'):
            return _normalize_songs_list(data['data']['results'])
    except Exception as e:
        print(f"[JioSaavn] Search error: {e}")
    return []


def search_all(query):
    """
    Global search on JioSaavn (songs, albums, artists, playlists).
    Returns a dict with keys: songs, albums, artists.
    """
    try:
        response = requests.get(
            f"{API_BASE}/api/search",
            params={'query': query},
            timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get('success') and data.get('data'):
            result_data = data['data']
            return {
                'songs': result_data.get('songs', {}).get('results', []),
                'albums': result_data.get('albums', {}).get('results', []),
                'artists': result_data.get('artists', {}).get('results', []),
            }
    except Exception as e:
        print(f"[JioSaavn] Global search error: {e}")
    return {'songs': [], 'albums': [], 'artists': []}


def get_song_details(song_id):
    """
    Get full details of a song by its JioSaavn ID.
    Returns a normalized song dict or None.
    """
    try:
        response = requests.get(
            f"{API_BASE}/api/songs/{song_id}",
            timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get('success') and data.get('data'):
            songs = data['data']
            if isinstance(songs, list) and len(songs) > 0:
                return _normalize_song(songs[0])
            elif isinstance(songs, dict):
                return _normalize_song(songs)
    except Exception as e:
        print(f"[JioSaavn] Song details error: {e}")
    return None


def get_song_suggestions(song_id, limit=10):
    """
    Get similar/suggested songs based on a song ID.
    Returns a list of normalized song dicts.
    """
    try:
        response = requests.get(
            f"{API_BASE}/api/songs/{song_id}/suggestions",
            params={'limit': limit},
            timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get('success') and data.get('data'):
            return _normalize_songs_list(data['data'])
    except Exception as e:
        print(f"[JioSaavn] Suggestions error: {e}")
    return []


def _fetch_trending_from_playlist(playlist_id, limit):
    """
    Try to fetch songs from a JioSaavn chart playlist by ID.
    Returns a list of normalized song dicts, or empty list on failure.
    """
    try:
        response = requests.get(
            f"{API_BASE}/api/playlists/{playlist_id}",
            params={'limit': limit},
            timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get('success') and data.get('data'):
            songs = data['data'].get('songs', [])
            if songs:
                return _normalize_songs_list(songs[:limit])
    except Exception as e:
        print(f"[JioSaavn] Playlist fetch error for {playlist_id}: {e}")
    return []


def _fetch_trending_from_search(limit):
    """
    Fallback: fetch trending songs via curated search queries.
    Deduplicates by ID and filters junk titles containing 'trending'.
    """
    seen_ids = set()
    results = []

    for query in _FALLBACK_QUERIES:
        if len(results) >= limit:
            break
        try:
            response = requests.get(
                f"{API_BASE}/api/search/songs",
                params={'query': query, 'page': 0, 'limit': limit},
                timeout=REQUEST_TIMEOUT
            )
            data = response.json()
            if data.get('success') and data.get('data', {}).get('results'):
                for s in data['data']['results']:
                    song = _normalize_song(s)
                    if not song:
                        continue
                    if song['id'] in seen_ids:
                        continue
                    if 'trending' in song['title'].lower():
                        continue
                    seen_ids.add(song['id'])
                    results.append(song)
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"[JioSaavn] Fallback search error for '{query}': {e}")

    return results


def get_trending(limit=10):  
    cache_key = f'jiosaavn_trending_{limit}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    results = []

    # Try each chart playlist until we get enough songs
    for playlist_id in CHART_PLAYLIST_IDS:
        if len(results) >= limit:
            break
        songs = _fetch_trending_from_playlist(playlist_id, limit)
        if songs:
            # Merge, deduplicating by ID
            existing_ids = {s['id'] for s in results}
            for song in songs:
                if song['id'] not in existing_ids:
                    results.append(song)
                    existing_ids.add(song['id'])
                    if len(results) >= limit:
                        break

    # Fallback to search if playlists returned nothing
    if not results:
        print("[JioSaavn] Playlist endpoints failed, falling back to search.")
        results = _fetch_trending_from_search(limit)

    if results:
        cache.set(cache_key, results, timeout=60 * 60)  # Cache for 1 hour

    return results[:limit]

def _get_trending_today_playlist_id():

    cache_key = 'jiosaavn_trending_today_playlist_id'
    cached_id = cache.get(cache_key)
    if cached_id:
        return cached_id

    try:
        response = requests.get(
            f"{API_BASE}/api/search/playlists",
            params={'query': 'Trending Today', 'limit': 5},
            timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get('success') and data.get('data', {}).get('results'):
            for playlist in data['data']['results']:
                name = playlist.get('name', '').lower()
                # Match the official JioSaavn trending playlist
                if 'trending today' in name:
                    playlist_id = playlist.get('id', '')
                    if playlist_id:
                        cache.set(cache_key, playlist_id, timeout=60 * 60 * 24)  # 24 hrs
                        return playlist_id
    except Exception as e:
        print(f"[JioSaavn] Trending Today playlist lookup error: {e}")
    return None


def get_trending_today(limit=20):
    
    cache_key = f'jiosaavn_trending_today_{limit}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    playlist_id = _get_trending_today_playlist_id()

    if playlist_id:
        try:
            response = requests.get(
                f"{API_BASE}/api/playlists/{playlist_id}",
                params={'limit': limit},
                timeout=REQUEST_TIMEOUT
            )
            data = response.json()
            if data.get('success') and data.get('data'):
                songs = data['data'].get('songs', [])
                results = _normalize_songs_list(songs[:limit])
                if results:
                    cache.set(cache_key, results, timeout=60 * 30)  # 30 min cache
                    return results
        except Exception as e:
            print(f"[JioSaavn] Trending Today fetch error: {e}")

    # Fallback
    print("[JioSaavn] Falling back to get_trending()")
    return get_trending(limit)