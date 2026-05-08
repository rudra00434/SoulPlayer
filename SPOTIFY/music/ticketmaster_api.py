"""
Ticketmaster Discovery API v2 — Helper module for SoulPlayer Live Events.
Docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

Free tier: 5,000 calls/day, 5 req/sec.
All results are cached for 5 minutes via Django's cache framework.
"""

import requests
from django.conf import settings
from django.core.cache import cache

BASE_URL = "https://app.ticketmaster.com/discovery/v2"


def _get_api_key():
    return getattr(settings, 'TICKETMASTER_API_KEY', '')


def _make_request(endpoint, params=None):
    """Generic GET request to the Ticketmaster Discovery API."""
    api_key = _get_api_key()
    if not api_key:
        print("[Ticketmaster] No API key configured.")
        return None

    if params is None:
        params = {}
    params['apikey'] = api_key

    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[Ticketmaster] API error {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[Ticketmaster] Request failed: {e}")
        return None


def _parse_event(event_raw):
    """Parse a raw Ticketmaster event object into a clean dict for templates."""
    # Basic info
    name = event_raw.get('name', 'Untitled Event')
    event_id = event_raw.get('id', '')
    url = event_raw.get('url', '#')

    # Date & time
    dates = event_raw.get('dates', {})
    start = dates.get('start', {})
    date_str = start.get('localDate', '')
    time_str = start.get('localTime', '')
    status = dates.get('status', {}).get('code', 'unknown')  # onsale, offsale, cancelled, postponed, rescheduled

    # Format date for display
    display_date = ''
    if date_str:
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            display_date = dt.strftime('%b %d, %Y')  # e.g. "May 15, 2026"
        except ValueError:
            display_date = date_str

    # Format time for display
    display_time = ''
    if time_str:
        try:
            from datetime import datetime
            dt = datetime.strptime(time_str, '%H:%M:%S')
            display_time = dt.strftime('%I:%M %p')  # e.g. "07:30 PM"
        except ValueError:
            display_time = time_str

    # Images (get the highest quality)
    images = event_raw.get('images', [])
    image_url = ''
    if images:
        # Prefer 16:9 ratio, largest first
        ratio_16_9 = [img for img in images if img.get('ratio') == '16_9']
        if ratio_16_9:
            image_url = sorted(ratio_16_9, key=lambda x: x.get('width', 0), reverse=True)[0].get('url', '')
        else:
            image_url = sorted(images, key=lambda x: x.get('width', 0), reverse=True)[0].get('url', '')

    # Venue info
    venues = event_raw.get('_embedded', {}).get('venues', [])
    venue_name = ''
    city = ''
    country = ''
    if venues:
        v = venues[0]
        venue_name = v.get('name', '')
        city = v.get('city', {}).get('name', '')
        country = v.get('country', {}).get('name', '')

    # Price range
    price_ranges = event_raw.get('priceRanges', [])
    price_min = ''
    price_max = ''
    currency = ''
    if price_ranges:
        pr = price_ranges[0]
        price_min = pr.get('min', '')
        price_max = pr.get('max', '')
        currency = pr.get('currency', 'USD')

    # Genre / classification
    classifications = event_raw.get('classifications', [])
    genre = ''
    segment = ''
    if classifications:
        c = classifications[0]
        genre = c.get('genre', {}).get('name', '')
        segment = c.get('segment', {}).get('name', '')
        if genre == 'Undefined':
            genre = ''

    # Attractions (artists)
    attractions = event_raw.get('_embedded', {}).get('attractions', [])
    artist_names = [a.get('name', '') for a in attractions if a.get('name')]

    return {
        'id': event_id,
        'name': name,
        'url': url,
        'date': date_str,
        'display_date': display_date,
        'time': time_str,
        'display_time': display_time,
        'status': status,
        'image_url': image_url,
        'venue': venue_name,
        'city': city,
        'country': country,
        'price_min': price_min,
        'price_max': price_max,
        'currency': currency,
        'genre': genre,
        'segment': segment,
        'artists': artist_names,
    }


# ==========================================
# PUBLIC API FUNCTIONS
# ==========================================

def get_events(city='', keyword='', country_code='IN', size=20, sort='date,asc'):
    """
    Search for upcoming music events.
    
    Args:
        city: City name to search in (e.g. "Mumbai")
        keyword: Search keyword (artist name, event name, etc.)
        country_code: ISO country code (default: IN for India)
        size: Number of results (max 200)
        sort: Sort order — 'date,asc' or 'date,desc' or 'relevance,asc'
    
    Returns:
        List of parsed event dicts, or empty list on failure.
    """
    cache_key = f"tm_events_{city}_{keyword}_{country_code}_{size}_{sort}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        'size': min(size, 200),
        'sort': sort,
        'classificationName': 'music',  # Only music events
    }
    if city:
        params['city'] = city
    if keyword:
        params['keyword'] = keyword
    if country_code:
        params['countryCode'] = country_code

    data = _make_request('events.json', params)
    if not data:
        cache.set(cache_key, [], 60)  # Cache empty results for 1 min
        return []

    embedded = data.get('_embedded', {})
    raw_events = embedded.get('events', [])

    events = [_parse_event(e) for e in raw_events]

    cache.set(cache_key, events, 300)  # Cache for 5 minutes
    return events


def get_event_details(event_id):
    """
    Get full details for a single event by its Ticketmaster event ID.
    
    Returns:
        Parsed event dict, or None on failure.
    """
    cache_key = f"tm_event_{event_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    data = _make_request(f'events/{event_id}.json')
    if not data:
        return None

    event = _parse_event(data)
    cache.set(cache_key, event, 300)
    return event


def get_artist_events(artist_name, country_code='', size=10):
    """
    Search for upcoming events by a specific artist.
    
    Args:
        artist_name: Name of the artist (e.g. "Arijit Singh")
        country_code: Optional country filter
        size: Number of results
    
    Returns:
        List of parsed event dicts.
    """
    cache_key = f"tm_artist_events_{artist_name}_{country_code}_{size}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        'keyword': artist_name,
        'size': min(size, 50),
        'sort': 'date,asc',
        'classificationName': 'music',
    }
    if country_code:
        params['countryCode'] = country_code

    data = _make_request('events.json', params)
    if not data:
        cache.set(cache_key, [], 60)
        return []

    embedded = data.get('_embedded', {})
    raw_events = embedded.get('events', [])

    events = [_parse_event(e) for e in raw_events]
    cache.set(cache_key, events, 300)
    return events


def get_global_events(size=20):
    """
    Get trending/popular music events globally (no country filter).
    Useful for the hero section fallback.
    """
    cache_key = f"tm_global_events_{size}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        'size': min(size, 50),
        'sort': 'relevance,desc',
        'classificationName': 'music',
    }

    data = _make_request('events.json', params)
    if not data:
        cache.set(cache_key, [], 60)
        return []

    embedded = data.get('_embedded', {})
    raw_events = embedded.get('events', [])

    events = [_parse_event(e) for e in raw_events]
    cache.set(cache_key, events, 300)
    return events
