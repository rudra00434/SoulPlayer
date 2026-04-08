"""
Recommendation Orchestrator Module for SoulPlayer.
Provides a clean interface for views to fetch cached ML recommendations
for a given user. Falls back to on-the-fly generation if no cache exists.
"""

import logging
from django.utils import timezone

logger = logging.getLogger('ml_pipeline')


def get_recommendations_for_user(user, n=30):
    """
    Fetch personalized song recommendations for a user.
    
    Priority:
    1. Return cached recommendations from the Recommendation model (fast).
    2. If no cache exists, generate on-the-fly using the hybrid engine (slower).
    3. If ML pipeline fails, fall back to popular/recent songs.
    
    Args:
        user: Django User instance (must be authenticated).
        n: Number of recommendations to return.
    
    Returns:
        dict: {
            'songs': list of Song objects,
            'algorithm': str (e.g. 'hybrid_v1'),
            'updated_at': datetime or None,
            'source': str ('cache', 'realtime', or 'fallback'),
        }
    """
    from music.models import Recommendation, Song

    # --- Step 1: Try cached recommendations ---
    try:
        rec_cache = Recommendation.objects.get(user=user)
        cached_data = rec_cache.recommended_songs  # JSONField: [{'song_id': int, 'score': float}, ...]

        if cached_data:
            song_ids = [item['song_id'] for item in cached_data[:n]]
            songs = _fetch_songs_by_ids_ordered(song_ids)

            if songs:
                logger.info(
                    f"Recommendations: Serving {len(songs)} cached results for user {user.username} "
                    f"(algorithm={rec_cache.algorithm_version})"
                )
                return {
                    'songs': songs,
                    'algorithm': rec_cache.algorithm_version,
                    'updated_at': rec_cache.updated_at,
                    'source': 'cache',
                }
    except Recommendation.DoesNotExist:
        logger.info(f"Recommendations: No cache for user {user.username}. Trying realtime.")

    # --- Step 2: Try real-time generation ---
    try:
        songs = _generate_realtime(user, n)
        if songs:
            return {
                'songs': songs,
                'algorithm': 'hybrid_v1_realtime',
                'updated_at': timezone.now(),
                'source': 'realtime',
            }
    except Exception as e:
        logger.error(f"Recommendations: Realtime generation failed for user {user.username}: {e}")

    # --- Step 3: Fallback to popular songs ---
    songs = _fallback_popular(user, n)
    return {
        'songs': songs,
        'algorithm': 'popularity_fallback',
        'updated_at': None,
        'source': 'fallback',
    }


def _fetch_songs_by_ids_ordered(song_ids):
    """
    Fetch Song objects by a list of IDs, preserving the order of the input list.
    """
    from music.models import Song

    if not song_ids:
        return []

    songs_qs = Song.objects.filter(id__in=song_ids)
    songs_map = {song.id: song for song in songs_qs}

    # Preserve recommendation ranking order
    return [songs_map[sid] for sid in song_ids if sid in songs_map]


def _generate_realtime(user, n):
    """
    Generate recommendations on-the-fly using the hybrid ML engine.
    This is slower than cached results but ensures fresh recommendations.
    """
    from music.ml_Pipeline.hybrid import HybridRecommender
    from music.models import Recommendation

    recommender = HybridRecommender()
    recommender.fit()

    results = recommender.recommend_for_user(user.id, n=n)

    if not results:
        return []

    # Cache the results for future requests
    try:
        serialized = [
            {'song_id': r['song_id'], 'score': r['score']}
            for r in results
        ]
        Recommendation.objects.update_or_create(
            user=user,
            defaults={
                'recommended_songs': serialized,
                'algorithm_version': 'hybrid_v1_realtime',
            }
        )
        logger.info(f"Recommendations: Cached {len(results)} realtime results for user {user.username}")
    except Exception as e:
        logger.error(f"Recommendations: Failed to cache realtime results: {e}")

    song_ids = [r['song_id'] for r in results]
    return _fetch_songs_by_ids_ordered(song_ids)


def _fallback_popular(user, n):
    """
    Fallback: return globally popular songs (most played by all users)
    and recent additions, excluding songs the user has already heard.
    """
    from music.models import Song, UserProfile
    from django.db.models import Count

    # Get user's already-played songs
    played_ids = set()
    try:
        profile = UserProfile.objects.get(user=user)
        played_ids = set(profile.played_songs.values_list('id', flat=True))
    except UserProfile.DoesNotExist:
        pass

    # Most played songs globally
    popular = list(
        Song.objects
        .annotate(play_count=Count('played_songs'))
        .exclude(id__in=played_ids)
        .order_by('-play_count')[:n]
    )

    # Fill remaining slots with recent songs
    if len(popular) < n:
        existing_ids = {s.id for s in popular} | played_ids
        recent = list(
            Song.objects
            .exclude(id__in=existing_ids)
            .order_by('-id')[:n - len(popular)]
        )
        popular.extend(recent)

    # If still not enough (new user, few songs), just get any songs
    if len(popular) < n:
        existing_ids = {s.id for s in popular}
        remaining = list(
            Song.objects
            .exclude(id__in=existing_ids)
            .order_by('?')[:n - len(popular)]
        )
        popular.extend(remaining)

    logger.info(f"Recommendations: Fallback returned {len(popular)} popular songs for user {user.username}")
    return popular
