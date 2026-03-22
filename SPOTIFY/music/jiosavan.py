"""
JioSaavn API Service Module
Wraps the unofficial JioSaavn API (saavn.sumit.co) for song search, details, and streaming.
No API key required.
"""
import requests
from django.conf import settings

API_BASE = getattr(settings, 'JIOSAAVN_API_BASE', 'https://saavn.sumit.co')
REQUEST_TIMEOUT = 8  # seconds


def _get_best_quality(items, fallback=''):
    """Extract the highest quality URL from an array of {quality, url} dicts."""
    if not items:
        return fallback
    # Priority order: 320kbps > 160kbps > 96kbps > 48kbps > 12kbps
    quality_order = ['320kbps', '160kbps', '96kbps', '48kbps', '12kbps']
    url_map = {item.get('quality', ''): item.get('url', '') for item in items}
    for q in quality_order:
        if q in url_map and url_map[q]:
            return url_map[q]
    # Fallback: return the last item (usually highest quality)
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

    # Get primary artist names
    artists = song_data.get('artists', {})
    primary_artists = artists.get('primary', [])
    artist_name = ', '.join(a.get('name', '') for a in primary_artists) if primary_artists else ''

    # If no primary artists, try the 'all' list
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
            return [_normalize_song(s) for s in data['data']['results'] if _normalize_song(s)]
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
            return [_normalize_song(s) for s in data['data'] if _normalize_song(s)]
    except Exception as e:
        print(f"[JioSaavn] Suggestions error: {e}")
    return []


def get_trending(limit=10):
    """
    Get trending songs by searching for a popular/trending query.
    Returns a list of normalized song dicts.
    """
    try:
        # Search for trending/popular content
        response = requests.get(
            f"{API_BASE}/api/search/songs",
            params={'query': 'trending hindi songs 2026', 'page': 0, 'limit': limit},
            timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get('success') and data.get('data', {}).get('results'):
            return [_normalize_song(s) for s in data['data']['results'] if _normalize_song(s)]
    except Exception as e:
        print(f"[JioSaavn] Trending error: {e}")
    return []
