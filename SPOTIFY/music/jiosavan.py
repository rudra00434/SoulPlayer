"""
JioSaavn API Service Module
Wraps the unofficial JioSaavn API (saavn.sumit.co) for song search, details, and streaming.
No API key required.
"""
import requests
from django.conf import settings
from django.core.cache import cache

API_MIRRORS = [
    'https://jiosaavn-api-sage.vercel.app',
    'https://jiosaavn-api-one-rho.vercel.app',
    'https://jiosaavn-api-privatecvc2.vercel.app',
    'https://saavn.sumit.co', 
]

API_BASE = getattr(settings, 'JIOSAAVN_API_BASE', API_MIRRORS[0])
REQUEST_TIMEOUT = 10  # seconds
CACHE_VERSION = "v2" # Increment this to force-clear remote caches

def _get_api_response(endpoint, params=None):
    """
    Helper to fetch data from JioSaavn API mirrors with automatic fallback.
    STANDARD: Handles both v1/v2 and mirrors with/without /api prefix.
    """
    params = params or {}
    
    # Standardize mirrors list
    raw_mirrors = [API_BASE] + API_MIRRORS
    mirrors = []
    for m in raw_mirrors:
        m = m.rstrip('/')
        if m.endswith('/api'):
            m = m[:-4]
        if m not in mirrors:
            mirrors.append(m)
    
    for mirror in mirrors:
        # Determine resource details for v2 style fallback
        path_segments = endpoint.strip('/').split('/')
        resource_type = path_segments[0]
        resource_id = path_segments[1] if len(path_segments) > 1 else None
        
        # Build all possible URL variations for this mirror
        # Some mirrors use /api/ prefix, some don't. Some use v1 paths, some use v2 params.
        variations = []
        
        # Prefixes to try
        prefixes = ['/api', '']
        
        for prefix in prefixes:
            if resource_id and resource_type in ['songs', 'albums', 'playlists', 'artists']:
                # v1 style: prefix/resource/id
                variations.append((f"{mirror}{prefix}/{resource_type}/{resource_id}", params))
                # v2 style: prefix/resource?id=id
                v2_params = params.copy()
                v2_params['id'] = resource_id
                variations.append((f"{mirror}{prefix}/{resource_type}", v2_params))
            else:
                # Standard search/list: prefix/endpoint
                variations.append((f"{mirror}{prefix}/{endpoint.lstrip('/')}", params))

        for url, request_params in variations:
            try:
                response = requests.get(url, params=request_params, timeout=REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') or ('results' in data.get('data', {})) or ('songs' in data.get('data', {})):
                        return data
                elif response.status_code == 429:
                    print(f"[JioSaavn] Mirror {mirror} rate limited (429).")
                    break # Skip to next mirror
                    
            except Exception:
                continue # Try next variation or mirror
            
    return None





# Official JioSaavn chart playlist IDs (stable, curated by JioSaavn)
CHART_PLAYLIST_IDS = [
    '1134543272', # Hindi: India Superhits Top 50 (Verified Hindi)
    '1265126272', # Chartbusters 2025 - Hindi (Verified Hindi)
    '92238273',   # Bollywood Hits
    '73507021',   # Top JioTunes Hindi
    '108422329',  # Let's Play Arijit Singh
    '159124040',  # Top 50 Punjabi
]

_FALLBACK_QUERIES = [
    'Latest Bollywood Hits',
    'New Hindi Songs',
    'Trending Hindi',
    'New Releases Pop - Hindi',
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

    # FALLBACK: If nested artists are missing (common for English tracks), try flat strings
    if not artist_name:
        flat_primary = song_data.get('primaryArtists')
        if flat_primary and isinstance(flat_primary, str):
            artist_name = flat_primary
        elif song_data.get('singers'):
            artist_name = song_data.get('singers')

    if not artist_name:
        all_artists = artists.get('all', [])
        if all_artists:
            artist_name = ', '.join(a.get('name', '') for a in all_artists[:3])
        else:
            # Last resort: Parse from description if available
            desc = song_data.get('description', '')
            if ' · ' in desc:
                 artist_name = desc.split(' · ')[1]
            else:
                 artist_name = 'Unknown Artist'

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


def search_songs(query, page=0, limit=20):
    """
    Search JioSaavn for songs.
    Returns a list of normalized song dicts.
    """
    data = _get_api_response("search/songs", params={'query': query, 'page': page, 'limit': limit})
    if data and data.get('data', {}).get('results'):
        return _normalize_songs_list(data['data']['results'])
    return []



def search_all(query):
    """
    Global search on JioSaavn (songs, albums, artists, playlists).
    Returns a dict with keys: songs, albums, artists.
    """
    data = _get_api_response("search", params={'query': query})
    if data and data.get('data'):
        result_data = data['data']
        return {
            'songs': result_data.get('songs', {}).get('results', []),
            'albums': result_data.get('albums', {}).get('results', []),
            'artists': result_data.get('artists', {}).get('results', []),
        }
    return {'songs': [], 'albums': [], 'artists': []}



def get_song_details(song_id):
    """
    Get full details of a song by its JioSaavn ID.
    Returns a normalized song dict or None.
    """
    data = _get_api_response(f"songs/{song_id}")
    if data and data.get('data'):
        songs = data['data']
        if isinstance(songs, list) and len(songs) > 0:
            return _normalize_song(songs[0])
        elif isinstance(songs, dict):
            return _normalize_song(songs)
    return None



def get_song_suggestions(song_id, limit=20):
    """
    Get similar/suggested songs based on a song ID.
    Returns a list of normalized song dicts.
    """
    data = _get_api_response(f"songs/{song_id}/suggestions", params={'limit': limit})
    if data and data.get('data'):
        return _normalize_songs_list(data['data'])

    # FALLBACK: If suggestions endpoint is broken upstream or empty, return trending queue so prev/next buttons still work
    return get_trending(limit)


def _fetch_trending_from_playlist(playlist_id, limit):
    """
    Try to fetch songs from a JioSaavn chart playlist by ID.
    Returns a list of normalized song dicts, or empty list on failure.
    """
    data = _get_api_response(f"playlists/{playlist_id}", params={'limit': limit})
    if data and data.get('data'):
        songs = data['data'].get('songs', [])
        if songs:
            return _normalize_songs_list(songs[:limit])
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
        data = _get_api_response("search/songs", params={'query': query, 'page': 0, 'limit': limit})
        if data and data.get('data', {}).get('results'):
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


    return results


def get_trending(limit=20):  
    cache_key = f'jiosaavn_trending_{CACHE_VERSION}_{limit}'
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
    cache_key = f'jiosaavn_trending_today_playlist_id_{CACHE_VERSION}'
    cached_id = cache.get(cache_key)
    if cached_id:
        return cached_id

    data = _get_api_response("search/playlists", params={'query': 'India Superhits Top 50', 'limit': 5})
    if data and data.get('data', {}).get('results'):
        for playlist in data['data']['results']:
            name = playlist.get('name', '').lower()
            # Match the official JioSaavn trending playlist
            if 'trending today' in name:
                playlist_id = playlist.get('id', '')
                if playlist_id:
                    cache.set(cache_key, playlist_id, timeout=60 * 60 * 24)  # 24 hrs
                    return playlist_id
    return None



def get_trending_today(limit=20):
    cache_key = f'jiosaavn_trending_today_{CACHE_VERSION}_{limit}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    playlist_id = _get_trending_today_playlist_id()

    if playlist_id:
        data = _get_api_response(f"playlists/{playlist_id}", params={'limit': limit})
        if data and data.get('data'):
            songs = data['data'].get('songs', [])
            results = _normalize_songs_list(songs[:limit])
            if results:
                cache.set(cache_key, results, timeout=60 * 30)  # 30 min cache
                return results


    # Fallback
    print("[JioSaavn] Falling back to get_trending()")
    return get_trending(limit)

def get_nostalgia_songs(limit=20):
    """Fetch 90s nostalgic songs from JioSaavn with caching to prevent excessive API calls."""
    cache_key = f'jiosaavn_nostalgia_{CACHE_VERSION}_{limit}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    seen_ids = set()
    results = []

    queries = [
        'Kishore Kumar songs',
        '90s hits bollywood',
        '90s romance hindi',
        '90s best songs',
    ]

    for query in queries:
        if len(results) >= limit:
            break
        data = _get_api_response("search/songs", params={'query': query, 'page': 0, 'limit': limit})
        if data and data.get('data', {}).get('results'):
            for s in data['data']['results']:
                song = _normalize_song(s)
                if song and song['id'] not in seen_ids:
                    seen_ids.add(song['id'])
                    results.append(song)
                    if len(results) >= limit:
                        break


    if results:
        cache.set(cache_key, results, timeout=60 * 60 * 24)  # Cache for 24 hours

    return results[:limit]


def get_artist_songs(artist_name, limit=20):
    """Fetch songs by a specific artist from JioSaavn via search."""
    cache_key = f'jiosaavn_artist_{artist_name.lower().replace(" ", "_")}_{limit}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    seen_ids = set()
    results = []

    # Search with artist name to find their songs
    queries = [
        f'{artist_name} songs',
        f'{artist_name} hits',
        f'{artist_name} best songs',
    ]

    for query in queries:
        if len(results) >= limit:
            break
        data = _get_api_response("search/songs", params={'query': query, 'page': 0, 'limit': 50})
        if data and data.get('data', {}).get('results'):
            for s in data['data']['results']:
                song = _normalize_song(s)
                if not song or song['id'] in seen_ids:
                    continue
                
                clean_artist = song.get('artist', '').lower()
                clean_title = song.get('title', '').lower()
                clean_target = artist_name.lower()
                
                # Official Match: Artist name is in the artist metadata
                # Smart-Search Match: Artist name is in the title (catches official remixes/covers)
                if clean_target in clean_artist or clean_target in clean_title:
                    seen_ids.add(song['id'])
                    results.append(song)
                    if len(results) >= limit:
                        break


    if results:
        cache.set(cache_key, results, timeout=60 * 60)  # Cache for 1 hour

    return results[:limit]


def search_albums(query, limit=10):
    """
    Search JioSaavn for albums.
    Returns a list of album dicts with {id, title, year, image_url, type}.
    """
    cache_key = f'jiosaavn_album_search_{query.lower().replace(" ", "_")}_{limit}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = _get_api_response("search/albums", params={'query': query, 'page': 0, 'limit': limit})
    if data and data.get('data', {}).get('results'):
        results = []
        for a in data['data']['results']:
            results.append({
                'id': a.get('id', ''),
                'title': a.get('name', ''),
                'year': a.get('year', ''),
                'image_url': _get_best_image(a.get('image', [])),
                'type': a.get('type', 'album'),
            })
        if results:
            cache.set(cache_key, results[:limit], timeout=60 * 60)
            return results[:limit]

    return []


def get_album_details(album_id):
    """
    Get full details of an album, including its songs.
    Returns a dict with album details and a 'songs' list of normalized songs.
    """
    cache_key = f'jiosaavn_album_details_{album_id}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = _get_api_response("albums", params={'id': album_id})
    if data and data.get('data'):
        album_data = data['data']
        
        # Extract artists correctly from album API response
        primary_artists = album_data.get('artists', {}).get('primary', [])
        artist_name = ', '.join(a.get('name', '') for a in primary_artists) if primary_artists else 'Various Artists'
        
        album_details = {
            'id': album_data.get('id', ''),
            'title': album_data.get('name', ''),
            'artist': artist_name,
            'year': album_data.get('year', ''),
            'image_url': _get_best_image(album_data.get('image', [])),
            'song_count': album_data.get('songCount', 0),
            'songs': _normalize_songs_list(album_data.get('songs', []))
        }
        cache.set(cache_key, album_details, timeout=60 * 60 * 2) # Cache for 2 hours
        return album_details

    return None