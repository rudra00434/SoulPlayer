"""
Collaborative Filtering Module for SoulPlayer.
Implements user-user collaborative filtering based on the played_songs 
interaction matrix. Uses cosine similarity between user listening vectors
to find similar users and recommend what they listened to.
"""

import numpy as np
import logging
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
from scipy.sparse import csr_matrix

from .data_preprocessing import get_user_song_matrix, get_user_profile_data
from .utils import normalize_scores

logger = logging.getLogger('ml_pipeline')


class CollaborativeFilteringRecommender:
    """
    User-User Collaborative Filtering recommender.
    
    Builds a user-song binary interaction matrix from played_songs history,
    computes user-user cosine similarity, and recommends songs that similar
    users have listened to but the target user has not.
    """

    def __init__(self, min_common_songs=1, n_similar_users=10):
        """
        Args:
            min_common_songs: Minimum songs in common to consider a user similar.
            n_similar_users: Number of most-similar users to aggregate recommendations from.
        """
        self.min_common_songs = min_common_songs
        self.n_similar_users = n_similar_users
        self.interaction_matrix = None  # pd.DataFrame (user_id × song_id)
        self.user_similarity = None     # np.ndarray (n_users × n_users)
        self.user_ids = []
        self.song_ids = []
        self.user_id_to_idx = {}
        self._is_fitted = False

    def fit(self):
        """
        Build the interaction matrix and compute user-user similarity.
        """
        matrix, user_ids, song_ids = get_user_song_matrix()

        if matrix.empty or len(user_ids) < 2:
            logger.warning(
                f"CollabFilter: Not enough data to build model "
                f"(users={len(user_ids)}, songs={len(song_ids)}). "
                f"Need at least 2 users with listening history."
            )
            self.user_ids = user_ids
            self.song_ids = song_ids
            self._is_fitted = False
            return

        self.interaction_matrix = matrix
        self.user_ids = user_ids
        self.song_ids = song_ids
        self.user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}

        # Convert to sparse matrix for efficient computation
        sparse_matrix = csr_matrix(matrix.values)

        # Compute user-user cosine similarity
        self.user_similarity = sklearn_cosine(sparse_matrix)

        # Zero out self-similarity on diagonal
        np.fill_diagonal(self.user_similarity, 0)

        self._is_fitted = True
        logger.info(
            f"CollabFilter: Fitted model with {len(user_ids)} users × "
            f"{len(song_ids)} songs. Similarity matrix computed."
        )

    def _get_similar_users(self, user_id):
        """
        Find the top N most similar users to the given user.
        
        Returns:
            list of (user_id, similarity_score) tuples, sorted descending.
        """
        if user_id not in self.user_id_to_idx:
            return []

        user_idx = self.user_id_to_idx[user_id]
        similarities = self.user_similarity[user_idx]

        # Get indices sorted by similarity (descending)
        sorted_indices = similarities.argsort()[::-1]

        similar_users = []
        for idx in sorted_indices:
            if len(similar_users) >= self.n_similar_users:
                break

            sim_score = similarities[idx]
            if sim_score <= 0:
                break

            other_user_id = self.user_ids[idx]

            # Check minimum common songs threshold
            user_vec = self.interaction_matrix.iloc[user_idx].values
            other_vec = self.interaction_matrix.iloc[idx].values
            common_songs = int(np.sum(np.minimum(user_vec, other_vec)))

            if common_songs >= self.min_common_songs:
                similar_users.append((other_user_id, float(sim_score)))

        return similar_users

    def recommend_for_user(self, user_id, n=30):
        """
        Generate collaborative filtering recommendations for a user.
        
        Strategy:
        1. Find the most similar users.
        2. For each similar user, get songs they played that the target user hasn't.
        3. Weight each song by the similarity score of the user who played it.
        4. Aggregate and normalize.
        
        Args:
            user_id: Django User ID
            n: Max number of recommendations.
        
        Returns:
            dict: {song_id: normalized_score}
        """
        if not self._is_fitted:
            logger.info("CollabFilter: Model not fitted or insufficient data.")
            return {}

        if user_id not in self.user_id_to_idx:
            logger.info(f"CollabFilter: User {user_id} not in interaction matrix.")
            return {}

        user_idx = self.user_id_to_idx[user_id]
        user_played = set(
            self.interaction_matrix.columns[
                self.interaction_matrix.iloc[user_idx].values > 0
            ].tolist()
        )

        similar_users = self._get_similar_users(user_id)

        if not similar_users:
            logger.info(f"CollabFilter: No similar users found for user {user_id}.")
            return {}

        # Accumulate weighted scores
        candidate_scores = {}

        for other_user_id, sim_score in similar_users:
            other_idx = self.user_id_to_idx[other_user_id]
            other_played = set(
                self.interaction_matrix.columns[
                    self.interaction_matrix.iloc[other_idx].values > 0
                ].tolist()
            )

            # Songs the similar user played that target user hasn't
            new_songs = other_played - user_played

            for song_id in new_songs:
                candidate_scores[song_id] = candidate_scores.get(song_id, 0.0) + sim_score

        # Normalize
        normalized = normalize_scores(candidate_scores)

        logger.info(
            f"CollabFilter: Generated {len(normalized)} candidate scores "
            f"for user {user_id} from {len(similar_users)} similar users."
        )
        return normalized
