import requests
import random

API_BASE = "https://de1.api.radio-browser.info/json/stations"
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
        image_url = f"https://ui-avatars.com/api/?name={requests.utils.quote(name)}&background=0b0f19&color=3be2c8&size=512&font-size=0.3"
        
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
