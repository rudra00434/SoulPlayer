"""
Content-Based Filtering Module for SoulPlayer.
Uses TF-IDF vectorization on song attributes (title, artist, genre/song_type)
to compute song-song similarity and recommend songs similar to what a user has played.
"""

import numpy as np
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .data_preprocessing import get_songs_as_feature_dicts, get_user_profile_data
from .utils import build_song_feature_string, normalize_scores

logger = logging.getLogger('ml_pipeline')


class ContentBasedRecommender:
    """
    Content-based recommender that builds a TF-IDF matrix from song features
    and recommends songs similar to a user's listening history.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),   # Unigrams + bigrams for better artist matching
            min_df=1,
            max_df=0.95,
        )
        self.tfidf_matrix = None
        self.song_ids = []       # Ordered list matching matrix rows
        self.song_id_to_idx = {} # song_id -> row index lookup
        self._is_fitted = False

    def fit(self, song_dicts=None):
        """
        Build the TF-IDF matrix from all songs in the database.
        
        Args:
            song_dicts: Optional pre-fetched list of song feature dicts.
                        If None, fetches from DB via data_preprocessing.
        """
        if song_dicts is None:
            song_dicts = get_songs_as_feature_dicts()

        if not song_dicts:
            logger.warning("ContentBased: No songs to fit. Aborting.")
            return

        # Build feature strings
        self.song_ids = [s['song_id'] for s in song_dicts]
        self.song_id_to_idx = {sid: idx for idx, sid in enumerate(self.song_ids)}

        feature_strings = [build_song_feature_string(s) for s in song_dicts]

        # Fit TF-IDF
        self.tfidf_matrix = self.vectorizer.fit_transform(feature_strings)
        self._is_fitted = True

        logger.info(
            f"ContentBased: Fitted TF-IDF matrix "
            f"({self.tfidf_matrix.shape[0]} songs × {self.tfidf_matrix.shape[1]} features)"
        )

    def get_similar_songs(self, song_id, n=10):
        """
        Get the top-N most similar songs to a given song.
        
        Args:
            song_id: int, the song ID to find similars for.
            n: Number of similar songs to return.
        
        Returns:
            dict: {song_id: similarity_score} for top N similar songs.
        """
        if not self._is_fitted:
            logger.error("ContentBased: Model not fitted. Call fit() first.")
            return {}

        if song_id not in self.song_id_to_idx:
            return {}

        idx = self.song_id_to_idx[song_id]
        song_vector = self.tfidf_matrix[idx]

        # Compute cosine similarity against all songs
        similarities = cosine_similarity(song_vector, self.tfidf_matrix).flatten()

        # Get top N+1 (exclude self)
        top_indices = similarities.argsort()[::-1][1:n + 1]

        return {
            self.song_ids[i]: float(similarities[i])
            for i in top_indices
            if similarities[i] > 0
        }

    def recommend_for_user(self, user_id, n=30):
        """
        Generate content-based recommendations for a user based on their
        listening history and favorite artists.
        
        Strategy:
        1. For each song the user has played, find similar songs.
        2. Boost scores for songs matching the user's favorite artists.
        3. Aggregate and normalize scores.
        
        Args:
            user_id: Django User ID
            n: Max number of recommendations.
        
        Returns:
            dict: {song_id: normalized_score}
        """
        if not self._is_fitted:
            logger.error("ContentBased: Model not fitted. Call fit() first.")
            return {}

        user_data = get_user_profile_data(user_id)
        played_ids = set(user_data['played_song_ids'])
        fav_artists = set(user_data['favorite_artist_names'])

        if not played_ids:
            logger.info(f"ContentBased: User {user_id} has no listening history.")
            return {}

        # Aggregate similarity scores across all played songs
        aggregated_scores = {}

        for song_id in played_ids:
            similar = self.get_similar_songs(song_id, n=20)
            for sim_id, sim_score in similar.items():
                if sim_id not in played_ids:  # Don't recommend already-played songs
                    aggregated_scores[sim_id] = aggregated_scores.get(sim_id, 0.0) + sim_score

        # Boost songs by favorite artists
        if fav_artists:
            song_dicts = get_songs_as_feature_dicts(list(aggregated_scores.keys()))
            for s in song_dicts:
                sid = s['song_id']
                artist_lower = s['artist'].lower()
                # Check if any favorite artist name appears in the song's artist field
                for fav in fav_artists:
                    if fav in artist_lower:
                        aggregated_scores[sid] = aggregated_scores.get(sid, 0.0) * 1.5
                        break

        # Normalize to [0, 1]
        normalized = normalize_scores(aggregated_scores)

        logger.info(f"ContentBased: Generated {len(normalized)} candidate scores for user {user_id}.")
        return normalized
