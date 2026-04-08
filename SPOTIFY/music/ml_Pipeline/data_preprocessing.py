"""
Data Preprocessing Module for SoulPlayer ML Pipeline.
Extracts data from Django ORM models (Song, UserProfile, Artist)
and transforms them into pandas DataFrames suitable for ML algorithms.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger('ml_pipeline')


def get_all_songs_df():
    """
    Extract all Song records from the database into a pandas DataFrame.
    
    Returns:
        pd.DataFrame with columns:
            song_id, title, artist, song_type, duration, language,
            album, jiosaavn_id, has_jiosaavn
    """
    from music.models import Song

    songs = Song.objects.all().values(
        'id', 'title', 'artist', 'song_type', 'duration',
        'jiosaavn_id', 'remote_image_url', 'audio_link'
    )
    
    if not songs:
        logger.warning("No songs found in database.")
        return pd.DataFrame()

    df = pd.DataFrame(list(songs))
    df.rename(columns={'id': 'song_id'}, inplace=True)

    # Clean up text fields
    df['title'] = df['title'].fillna('').str.strip()
    df['artist'] = df['artist'].fillna('').str.strip()
    df['song_type'] = df['song_type'].fillna('unknown').str.strip().str.lower()

    # Flag whether song is from JioSaavn
    df['has_jiosaavn'] = df['jiosaavn_id'].notna() & (df['jiosaavn_id'] != '')

    # Extract primary artist (first name before comma)
    df['primary_artist'] = df['artist'].apply(
        lambda x: x.split(',')[0].strip().lower() if x else 'unknown'
    )

    logger.info(f"Loaded {len(df)} songs from database.")
    return df


def get_user_song_matrix():
    """
    Build a User-Song interaction matrix from UserProfile.played_songs M2M.
    
    Returns:
        tuple: (interaction_df, user_ids, song_ids)
            - interaction_df: pd.DataFrame with user_id as index, song_id as columns, 1/0 values
            - user_ids: list of user IDs
            - song_ids: list of song IDs
    """
    from music.models import UserProfile

    profiles = UserProfile.objects.prefetch_related('played_songs').all()

    records = []
    for profile in profiles:
        user_id = profile.user_id
        played = profile.played_songs.values_list('id', flat=True)
        for song_id in played:
            records.append({'user_id': user_id, 'song_id': song_id, 'interaction': 1})

    if not records:
        logger.warning("No user-song interactions found.")
        return pd.DataFrame(), [], []

    df = pd.DataFrame(records)

    # Pivot to create user-song matrix
    matrix = df.pivot_table(
        index='user_id',
        columns='song_id',
        values='interaction',
        fill_value=0,
        aggfunc='max'  # Binary: played or not
    )

    user_ids = list(matrix.index)
    song_ids = list(matrix.columns)

    logger.info(f"Built interaction matrix: {len(user_ids)} users × {len(song_ids)} songs.")
    return matrix, user_ids, song_ids


def get_user_profile_data(user_id):
    """
    Get a single user's played songs and favorite artists for recommendation.
    
    Args:
        user_id: Django User ID
    
    Returns:
        dict with keys:
            - played_song_ids: list of int
            - favorite_artist_names: list of str (lowercased)
            - personality: str or None
    """
    from music.models import UserProfile

    try:
        profile = UserProfile.objects.prefetch_related(
            'played_songs', 'favorite_artists'
        ).get(user_id=user_id)
    except UserProfile.DoesNotExist:
        logger.warning(f"No UserProfile found for user_id={user_id}")
        return {
            'played_song_ids': [],
            'favorite_artist_names': [],
            'personality': None,
        }

    played_ids = list(profile.played_songs.values_list('id', flat=True))
    fav_artists = list(
        profile.favorite_artists.values_list('name', flat=True)
    )

    return {
        'played_song_ids': played_ids,
        'favorite_artist_names': [a.lower() for a in fav_artists],
        'personality': profile.personality,
    }


def get_songs_as_feature_dicts(song_ids=None):
    """
    Return song data as a list of dicts ready for feature extraction.
    Optionally filter by specific song IDs.
    
    Args:
        song_ids: Optional list of song IDs to filter. None = all songs.
    
    Returns:
        list of dicts with keys: song_id, title, artist, song_type, language, album
    """
    from music.models import Song

    qs = Song.objects.all()
    if song_ids is not None:
        qs = qs.filter(id__in=song_ids)

    songs = qs.values('id', 'title', 'artist', 'song_type', 'jiosaavn_id')

    result = []
    for s in songs:
        result.append({
            'song_id': s['id'],
            'title': s['title'] or '',
            'artist': s['artist'] or '',
            'song_type': s['song_type'] or 'unknown',
            'language': '',  # Only available for JioSaavn songs at runtime
            'album': '',
        })

    return result
