"""
Django Management Command: train_recommendations

Runs the full hybrid ML recommendation pipeline:
1. Loads all songs and user interaction data from the database.
2. Fits the Content-Based (TF-IDF) and Collaborative Filtering models.
3. Generates personalized recommendations for every user.
4. Saves results to the Recommendation model (JSON cache).

Usage:
    python manage.py train_recommendations
    python manage.py train_recommendations --users 1 5 12
    python manage.py train_recommendations --top 50
"""

import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from music.models import Recommendation, UserProfile
from music.ml_Pipeline.hybrid import HybridRecommender, ALGORITHM_VERSION

logger = logging.getLogger('ml_pipeline')


class Command(BaseCommand):
    help = 'Train the ML recommendation engine and cache results for all users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            nargs='+',
            type=int,
            help='Only generate recommendations for specific user IDs. Default: all users.',
        )
        parser.add_argument(
            '--top',
            type=int,
            default=30,
            help='Number of recommendations per user (default: 30).',
        )
        parser.add_argument(
            '--cb-weight',
            type=float,
            default=0.6,
            help='Weight for content-based scores (default: 0.6).',
        )
        parser.add_argument(
            '--cf-weight',
            type=float,
            default=0.4,
            help='Weight for collaborative filtering scores (default: 0.4).',
        )

    def handle(self, *args, **options):
        start_time = time.time()

        n_recs = options['top']
        cb_weight = options['cb_weight']
        cf_weight = options['cf_weight']
        specific_users = options.get('users')

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n🎵 SoulPlayer — ML Recommendation Engine\n'
        ))
        self.stdout.write(f'  Algorithm version: {ALGORITHM_VERSION}')
        self.stdout.write(f'  Recommendations per user: {n_recs}')
        self.stdout.write(f'  Weights: CB={cb_weight}, CF={cf_weight}')
        self.stdout.write('')

        # ---------------------------------------------------
        # Step 1: Initialize and fit the hybrid recommender
        # ---------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO('Step 1/3: Fitting models...'))

        recommender = HybridRecommender(cb_weight=cb_weight, cf_weight=cf_weight)

        try:
            recommender.fit()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'  ✗ Error fitting models: {e}'))
            logger.exception("Failed to fit recommender models.")
            return

        self.stdout.write(self.style.SUCCESS('  ✓ Models fitted successfully.'))

        # ---------------------------------------------------
        # Step 2: Generate recommendations
        # ---------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO('Step 2/3: Generating recommendations...'))

        if specific_users:
            user_ids = specific_users
            self.stdout.write(f'  Targeting {len(user_ids)} specific user(s): {user_ids}')
        else:
            user_ids = list(
                UserProfile.objects.values_list('user_id', flat=True)
            )
            self.stdout.write(f'  Targeting all {len(user_ids)} user(s)')

        results = {}
        success_count = 0
        error_count = 0

        for user_id in user_ids:
            try:
                recs = recommender.recommend_for_user(user_id, n=n_recs)
                results[user_id] = recs
                success_count += 1

                # Progress indicator
                if success_count % 10 == 0:
                    self.stdout.write(f'  ... processed {success_count}/{len(user_ids)} users')

            except Exception as e:
                error_count += 1
                self.stderr.write(
                    self.style.WARNING(f'  ⚠ Error for user {user_id}: {e}')
                )
                logger.error(f"Recommendation failed for user {user_id}: {e}")
                results[user_id] = []

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Generated recommendations for {success_count} user(s) '
            f'({error_count} error(s)).'
        ))

        # ---------------------------------------------------
        # Step 3: Save to database
        # ---------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO('Step 3/3: Saving to database...'))

        saved_count = 0
        for user_id, recs in results.items():
            try:
                # Serialize: store list of {song_id, score}
                serialized = [
                    {'song_id': r['song_id'], 'score': r['score']}
                    for r in recs
                ]

                obj, created = Recommendation.objects.update_or_create(
                    user_id=user_id,
                    defaults={
                        'recommended_songs': serialized,
                        'algorithm_version': ALGORITHM_VERSION,
                    }
                )
                saved_count += 1
                action = 'Created' if created else 'Updated'
                logger.info(f"  {action} recommendation cache for user {user_id} ({len(recs)} songs)")

            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(f'  ⚠ Failed to save for user {user_id}: {e}')
                )
                logger.error(f"Save failed for user {user_id}: {e}")

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Saved {saved_count} recommendation caches to database.'
        ))

        # ---------------------------------------------------
        # Summary
        # ---------------------------------------------------
        elapsed = time.time() - start_time
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✅ Pipeline complete in {elapsed:.2f}s\n'
            f'   • {success_count} users processed\n'
            f'   • {saved_count} caches saved\n'
            f'   • {error_count} errors\n'
            f'   • Algorithm: {ALGORITHM_VERSION}'
        ))
