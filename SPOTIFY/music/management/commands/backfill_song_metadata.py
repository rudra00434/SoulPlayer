"""
Django Management Command: backfill_song_metadata

Fetches real genre/language/album data from JioSaavn API for songs
that were previously synced with song_type='jiosaavn' (a source label
instead of a real genre).

Usage:
    python manage.py backfill_song_metadata
    python manage.py backfill_song_metadata --dry-run
"""

import time
import logging
from django.core.management.base import BaseCommand

from music.models import Song
from music.jiosavan import get_song_details

logger = logging.getLogger('ml_pipeline')


class Command(BaseCommand):
    help = 'Backfill language, album, and real genre for JioSaavn songs stored with song_type="jiosaavn".'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Find songs with the generic 'jiosaavn' song_type
        songs = Song.objects.filter(song_type='jiosaavn', jiosaavn_id__isnull=False)
        total = songs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No songs need backfilling. All good!'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\nBackfilling metadata for {total} JioSaavn songs\n'
        ))
        if dry_run:
            self.stdout.write(self.style.WARNING('  DRY RUN - no changes will be saved.\n'))

        updated = 0
        failed = 0

        for song in songs:
            try:
                details = get_song_details(song.jiosaavn_id)
                if not details:
                    self.stdout.write(self.style.WARNING(
                        f'  ! {song.title[:40]} - API returned nothing'
                    ))
                    failed += 1
                    continue

                lang = details.get('language', '')
                album = details.get('album', '')
                new_type = lang.capitalize() if lang else song.song_type

                self.stdout.write(
                    f'  {song.title[:40]:40s} -> type={new_type}, lang={lang}, album={album[:30]}'
                )

                if not dry_run:
                    song.song_type = new_type
                    song.language = lang
                    song.album = album
                    song.save(update_fields=['song_type', 'language', 'album'])

                updated += 1

                # Rate limit to avoid hammering the API
                time.sleep(0.3)

            except Exception as e:
                failed += 1
                self.stderr.write(self.style.ERROR(
                    f'  x {song.title[:40]} - Error: {e}'
                ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! Updated: {updated}, Failed: {failed}, Total: {total}'
        ))
