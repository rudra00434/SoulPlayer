"""
Shared utility functions for the SoulPlayer ML recommendation pipeline.
Provides similarity helpers, normalization, scoring, and logging utilities.
"""

import numpy as np
import logging

logger = logging.getLogger('ml_pipeline')


def normalize_scores(scores_dict):
    """
    Min-max normalize a dict of {item_id: score} to [0, 1] range.
    Returns a new dict with normalized scores.
    """
    if not scores_dict:
        return {}

    values = list(scores_dict.values())
    min_val = min(values)
    max_val = max(values)
    spread = max_val - min_val

    if spread == 0:
        # All scores are equal — return uniform 0.5
        return {k: 0.5 for k in scores_dict}

    return {k: (v - min_val) / spread for k, v in scores_dict.items()}


def merge_score_dicts(*score_dicts, weights=None):
    """
    Merge multiple {song_id: score} dicts into one using weighted addition.
    
    Args:
        *score_dicts: Variable number of {song_id: float} dictionaries.
        weights: List of floats matching len(score_dicts). Defaults to equal weights.
    
    Returns:
        dict: Combined {song_id: weighted_score}
    """
    if not score_dicts:
        return {}

    if weights is None:
        weights = [1.0 / len(score_dicts)] * len(score_dicts)

    if len(weights) != len(score_dicts):
        raise ValueError(f"weights length ({len(weights)}) != score_dicts count ({len(score_dicts)})")

    merged = {}
    for score_dict, weight in zip(score_dicts, weights):
        for song_id, score in score_dict.items():
            merged[song_id] = merged.get(song_id, 0.0) + (score * weight)

    return merged


def top_n(scores_dict, n=20, exclude_ids=None):
    """
    Return the top N song IDs from a scores dict, excluding specified IDs.
    
    Args:
        scores_dict: {song_id: score}
        n: Number of results to return.
        exclude_ids: set of song IDs to exclude (e.g. already played songs).
    
    Returns:
        list of (song_id, score) tuples sorted by score descending.
    """
    exclude_ids = exclude_ids or set()
    filtered = {k: v for k, v in scores_dict.items() if k not in exclude_ids}
    sorted_items = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
    return sorted_items[:n]


def build_song_feature_string(song):
    """
    Build a combined text feature string from a Song object's attributes.
    Used by TF-IDF vectorizer in content-based filtering.
    
    Repeats artist name to boost artist-match weight.
    """
    parts = []

    # Title words
    if song.get('title'):
        parts.append(song['title'].lower())

    # Artist (repeated 3x for higher weight in TF-IDF)
    if song.get('artist'):
        artist_clean = song['artist'].lower().replace(',', ' ')
        parts.extend([artist_clean] * 3)

    # Genre / song_type (repeated 2x)
    if song.get('song_type'):
        parts.extend([song['song_type'].lower()] * 2)

    # Language (if available from JioSaavn)
    if song.get('language'):
        parts.append(song['language'].lower())

    # Album
    if song.get('album'):
        parts.append(song['album'].lower())

    return ' '.join(parts)


def safe_divide(numerator, denominator, default=0.0):
    """Safe division that returns default on zero denominator."""
    if denominator == 0:
        return default
    return numerator / denominator
