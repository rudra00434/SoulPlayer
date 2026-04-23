import requests
import random
from django.core.cache import cache

API_BASE = "https://de1.api.radio-browser.info/json/stations"
SPREAKER_API = "https://api.spreaker.com/v2"
SUNDAY_SUSPENSE_SHOW_ID = 6039407  # Official Mirchi Bangla show on Spreaker (no API key needed)
TIMEOUT = 8

def _normalize_station(data):
    """Normalize station data for template rendering."""
    # Handle missing names
    name = data.get('name', '').strip()
    if not name:
        return None
        
    # Get best stream URL
    stream_url = data.get('url_resolved') or data.get('url')
    if not stream_url:
        return None
        
    # Default image if empty
    image_url = data.get('favicon', '').strip()
    if not image_url or not image_url.startswith('http'):
        image_url = ""
        
    # Tags parsing
    tags = data.get('tags', '')
    genres = [t.strip().upper() for t in tags.split(',') if t.strip()][:3]
    if not genres:
        genres = ['RADIO']

    return {
        'id': data.get('stationuuid', ''),
        'name': name,
        'image_url': image_url,
        'stream_url': stream_url,
        'genres': genres,
        'country': data.get('countrycode', 'IN'),
        'language': data.get('language', '').split(',')[0].capitalize(),
        'bitrate': data.get('bitrate', 0)
    }

def get_top_indian_stations(limit=40):
    """Fetch top radio stations mostly focusing on India or Indian languages."""
    try:
        response = requests.get(
            f"{API_BASE}/search",
            params={
                'countrycode': 'IN',
                'limit': limit,
                'hidebroken': 'true',
                'order': 'votes',
                'reverse': 'true'
            },
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            raw_stations = response.json()
            results = []
            for s in raw_stations:
                norm = _normalize_station(s)
                if norm:
                    results.append(norm)
            return results
    except Exception as e:
        print(f"[Radio API] Top Stations error: {e}")
    return []

def get_station_by_uuid(uuid):
    """Fetch a specific station's details by its UUID to play it."""
    try:
        response = requests.get(
            f"{API_BASE}/byuuid/{uuid}",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return _normalize_station(data[0])
    except Exception as e:
        print(f"[Radio API] Station fetch error: {e}")
    return None


def get_mirchi_station():
    """Fetch Radio Mirchi 98.3 FM station from radio-browser.info with 1-hour cache."""
    cache_key = 'radio_mirchi_station_v1'
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        response = requests.get(
            f"{API_BASE}/search",
            params={
                'name': 'mirchi',
                'countrycode': 'IN',
                'hidebroken': 'true',
                'order': 'votes',
                'reverse': 'true',
                'limit': 10,
            },
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            for s in response.json():
                norm = _normalize_station(s)
                if norm and '98' in s.get('name', '') or 'mirchi' in s.get('name', '').lower():
                    cache.set(cache_key, norm, timeout=60 * 60)
                    return norm
    except Exception as e:
        print(f"[Radio API] Mirchi station fetch error: {e}")
    return None


def _format_duration_ms(ms):
    """Convert milliseconds to 'Xhr Ymin' or 'Xmin Ysec' string."""
    try:
        total_sec = int(ms) // 1000
        hours = total_sec // 3600
        mins = (total_sec % 3600) // 60
        secs = total_sec % 60
        if hours > 0:
            return f"{hours}hr {mins}min"
        elif mins > 0:
            return f"{mins}min {secs}sec"
        else:
            return f"{secs}sec"
    except (ValueError, TypeError):
        return ''


def get_sunday_suspense_episodes(limit=24):
    """Fetch latest Sunday Suspense episodes from Spreaker API with 6-hour cache."""
    cache_key = f'spreaker_sunday_suspense_{limit}'
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        response = requests.get(
            f"{SPREAKER_API}/shows/{SUNDAY_SUSPENSE_SHOW_ID}/episodes",
            params={'limit': limit, 'filter': 'listenable'},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            raw_items = data.get('response', {}).get('items', [])
            episodes = []
            for ep in raw_items:
                episode_id = ep.get('episode_id')
                if not episode_id:
                    continue
                # Use higher quality image
                img = ep.get('image_original_url') or ep.get('image_url', '')
                published = ep.get('published_at', '')[:10]  # 'YYYY-MM-DD'
                episodes.append({
                    'id': episode_id,
                    'title': ep.get('title', 'Untitled Episode'),
                    'image_url': img,
                    'playback_url': ep.get('playback_url', f'{SPREAKER_API}/episodes/{episode_id}/play.mp3'),
                    'duration_ms': ep.get('duration', 0),
                    'duration_str': _format_duration_ms(ep.get('duration', 0)),
                    'published_at': published,
                    'site_url': ep.get('site_url', ''),
                    'slug': ep.get('slug', ''),
                })
            if episodes:
                cache.set(cache_key, episodes, timeout=60 * 60 * 6)  # 6-hour cache
            return episodes
    except Exception as e:
        print(f"[Radio API] Sunday Suspense Spreaker error: {e}")
    return []


def get_episode_by_id(episode_id):
    """Fetch a single Sunday Suspense episode from Spreaker by episode_id.
    Used by the dedicated episode player page. Cached for 12 hours.
    """
    cache_key = f'spreaker_episode_{episode_id}'
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        response = requests.get(
            f"{SPREAKER_API}/episodes/{episode_id}",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            ep = data.get('response', {}).get('episode', {})
            if not ep:
                return None
            eid = ep.get('episode_id')
            img = ep.get('image_original_url') or ep.get('image_url', '')
            published = ep.get('published_at', '')[:10]
            result = {
                'id': eid,
                'title': ep.get('title', 'Untitled Episode'),
                'image_url': img,
                'playback_url': ep.get('playback_url', f'{SPREAKER_API}/episodes/{eid}/play.mp3'),
                'duration_ms': ep.get('duration', 0),
                'duration_str': _format_duration_ms(ep.get('duration', 0)),
                'published_at': published,
                'site_url': ep.get('site_url', ''),
                'slug': ep.get('slug', ''),
                'description': ep.get('description', ''),
            }
            cache.set(cache_key, result, timeout=60 * 60 * 12)
            return result
    except Exception as e:
        print(f"[Radio API] Episode fetch error (id={episode_id}): {e}")
    return None
