"""
Hybrid Recommendation Module for SoulPlayer.
Combines content-based and collaborative filtering scores using a
weighted strategy. Handles cold-start scenarios gracefully.
"""

import logging

from .content_based import ContentBasedRecommender
from .collaborative_filtering import CollaborativeFilteringRecommender
from .data_preprocessing import get_user_profile_data, get_songs_as_feature_dicts
from .utils import merge_score_dicts, normalize_scores, top_n

logger = logging.getLogger('ml_pipeline')

# Default weights: 60% content-based, 40% collaborative
DEFAULT_CB_WEIGHT = 0.6
DEFAULT_CF_WEIGHT = 0.4

# Algorithm version tag stored in Recommendation model
ALGORITHM_VERSION = 'hybrid_v1'


class HybridRecommender:
    """
    Hybrid recommender that combines:
    - Content-Based Filtering (TF-IDF on song features)
    - Collaborative Filtering (user-user cosine similarity)
    
    Adapts weights based on data availability:
    - New user (no history): returns popular/trending songs (cold start)
    - User with history but few other users: 100% content-based
    - Full data available: weighted hybrid (default 60/40)
    """

    def __init__(self, cb_weight=DEFAULT_CB_WEIGHT, cf_weight=DEFAULT_CF_WEIGHT):
        self.cb_weight = cb_weight
        self.cf_weight = cf_weight
        self.content_recommender = ContentBasedRecommender()
        self.collab_recommender = CollaborativeFilteringRecommender()
        self._is_fitted = False

    def fit(self):
        """
        Train both sub-recommenders on the full database.
        Call this once before generating recommendations for all users.
        """
        logger.info("Hybrid: Fitting content-based recommender...")
        self.content_recommender.fit()

        logger.info("Hybrid: Fitting collaborative filtering recommender...")
        self.collab_recommender.fit()

        self._is_fitted = True
        logger.info("Hybrid: Both models fitted successfully.")

    def recommend_for_user(self, user_id, n=30, exclude_played=True):
        """
        Generate hybrid recommendations for a user.
        
        Args:
            user_id: Django User ID
            n: Number of recommendations to return.
            exclude_played: If True, exclude songs the user already played.
        
        Returns:
            list of dicts: [{song_id, score}, ...] sorted by score descending.
        """
        if not self._is_fitted:
            logger.error("Hybrid: Models not fitted. Call fit() first.")
            return []

        user_data = get_user_profile_data(user_id)
        played_ids = set(user_data['played_song_ids'])

        # --- Get scores from both models ---
        cb_scores = self.content_recommender.recommend_for_user(user_id, n=n * 2)
        cf_scores = self.collab_recommender.recommend_for_user(user_id, n=n * 2)

        # --- Determine weights based on data availability ---
        actual_cb_weight = self.cb_weight
        actual_cf_weight = self.cf_weight

        if not cb_scores and not cf_scores:
            # Cold start — no data at all
            logger.info(f"Hybrid: Cold start for user {user_id}. Returning popular songs.")
            return self._cold_start_recommendations(n, played_ids)

        if not cf_scores:
            # No collaborative data (new user or too few users)
            actual_cb_weight = 1.0
            actual_cf_weight = 0.0
            logger.info(f"Hybrid: No collab data for user {user_id}. Using 100% content-based.")

        if not cb_scores:
            # Edge case: collab data exists but no content data
            actual_cb_weight = 0.0
            actual_cf_weight = 1.0
            logger.info(f"Hybrid: No content data for user {user_id}. Using 100% collaborative.")

        # --- Merge scores ---
        merged = merge_score_dicts(
            cb_scores, cf_scores,
            weights=[actual_cb_weight, actual_cf_weight]
        )

        # Normalize the merged scores
        merged = normalize_scores(merged)

        # Exclude already-played songs
        exclude = played_ids if exclude_played else set()

        # Get top N
        top_songs = top_n(merged, n=n, exclude_ids=exclude)

        results = [
            {'song_id': song_id, 'score': round(score, 4)}
            for song_id, score in top_songs
        ]

        logger.info(
            f"Hybrid: Generated {len(results)} recommendations for user {user_id} "
            f"(weights: CB={actual_cb_weight:.1f}, CF={actual_cf_weight:.1f})"
        )
        return results

    def _cold_start_recommendations(self, n, exclude_ids=None):
        """
        Fallback for users with no listening history.
        Returns genre-diverse popular songs — samples across different
        song_type/language groups to avoid a monotone list.
        """
        from music.models import Song
        from django.db.models import Count
        import random

        exclude_ids = exclude_ids or set()

        # Get songs grouped by genre (song_type), ordered by popularity within each genre
        genres = (
            Song.objects
            .exclude(id__in=exclude_ids)
            .values_list('song_type', flat=True)
            .distinct()
        )

        genre_buckets = {}
        for genre in genres:
            songs = list(
                Song.objects
                .filter(song_type=genre)
                .exclude(id__in=exclude_ids)
                .annotate(play_count=Count('played_songs'))
                .order_by('-play_count')[:n*4]
                .values_list('id', flat=True)
            )
            if songs:
                random.shuffle(songs) # Randomize so each new user gets a completely unique cold-start mix
                genre_buckets[genre] = songs

        # Round-robin sample from each genre for diversity
        results = []
        if genre_buckets:
            bucket_keys = list(genre_buckets.keys())
            random.shuffle(bucket_keys)  # Randomize genre order for variety
            idx = 0
            while len(results) < n and any(genre_buckets.values()):
                genre = bucket_keys[idx % len(bucket_keys)]
                if genre_buckets[genre]:
                    sid = genre_buckets[genre].pop(0)
                    results.append({
                        'song_id': sid,
                        'score': round(1.0 - (len(results) * 0.01), 4)
                    })
                idx += 1
                # Break if all buckets are empty
                if all(len(v) == 0 for v in genre_buckets.values()):
                    break

        # Backfill with any remaining songs if needed
        if len(results) < n:
            existing_ids = {r['song_id'] for r in results} | exclude_ids
            remaining = list(
                Song.objects
                .exclude(id__in=existing_ids)
                .order_by('-id')[:n - len(results)]
                .values_list('id', flat=True)
            )
            for sid in remaining:
                results.append({
                    'song_id': sid,
                    'score': round(0.5 - (len(results) * 0.01), 4)
                })

        logger.info(f"Hybrid: Cold start returned {len(results)} diverse songs from {len(genre_buckets)} genres.")
        return results

    def recommend_all_users(self, n=30):
        """
        Generate recommendations for ALL users in the system.
        Used by the management command for batch processing.
        
        Returns:
            dict: {user_id: [{'song_id': int, 'score': float}, ...]}
        """
        from music.models import UserProfile

        all_profiles = UserProfile.objects.values_list('user_id', flat=True)
        all_recommendations = {}

        for user_id in all_profiles:
            try:
                recs = self.recommend_for_user(user_id, n=n)
                all_recommendations[user_id] = recs
                logger.info(f"Hybrid: User {user_id} → {len(recs)} recommendations")
            except Exception as e:
                logger.error(f"Hybrid: Error generating for user {user_id}: {e}")
                all_recommendations[user_id] = []

        return all_recommendations
