"""
management/commands/populate_location_slugs.py
================================================
One-time (and periodic) management command to reverse-geocode every
tutor's lat/lng into a human-readable location_name + location_slug
and persist both on CustomUser.

Why a management command instead of doing it at request time?
-------------------------------------------------------------
* Reverse geocoding is a network call (Nominatim / OpenStreetMap).
  Doing it during an API request would add ~200–500 ms of latency
  and make the SEO endpoint depend on an external service.
* We want the SEO endpoints to be fast (<10 ms) and work even when
  the geocoding API is down.
* This command can be run nightly via cron or when new tutors sign up.

Usage
-----
    # Populate all tutors that don't have a location_slug yet
    python manage.py populate_location_slugs

    # Re-geocode ALL tutors (force re-run)
    python manage.py populate_location_slugs --force

    # Dry-run (print what would be set, don't save)
    python manage.py populate_location_slugs --dry-run

    # Process at most N tutors (useful for testing)
    python manage.py populate_location_slugs --limit 100

Dependencies
------------
This uses geopy (already in requirements.txt) with Nominatim.
Set a meaningful user_agent that identifies your project.

Rate limiting
-------------
Nominatim's usage policy: max 1 request/second.
We respect this with a 1.1 second sleep between calls.
For large datasets (> 5 000 tutors) consider using a commercial
geocoding provider like Google Maps, Mapbox, or Pelias.

Manual override
---------------
Admins can also set location_name / location_slug directly via the
Django admin if the reverse-geocoded name is not ideal (e.g. a
neighbourhood name instead of the district).
"""

import time
import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from base.models import CustomUser

logger = logging.getLogger(__name__)

# How long to wait between geocoding requests (Nominatim policy: 1 req/s)
RATE_LIMIT_SECONDS = 1.1

# Nominatim user agent — change to your domain
USER_AGENT = 'etuition-seo-populator/1.0 (contact@etuition.app)'


def _reverse_geocode(geocoder, lat: float, lon: float) -> tuple[str, str]:
    """
    Returns (location_name, location_slug) for a lat/lng pair.

    We prefer:
      1. city     (e.g. "Chattogram")
      2. town     (e.g. "Cox's Bazar")
      3. county   (e.g. "Chattogram District")
      4. state    (e.g. "Chittagong Division")
      5. country  (last resort)

    The slug is just slugify(name).
    """
    try:
        location = geocoder.reverse(
            (lat, lon),
            language='en',
            exactly_one=True,
            timeout=10,
        )
    except GeocoderTimedOut:
        logger.warning('Geocoder timed out for (%s, %s)', lat, lon)
        return '', ''
    except GeocoderServiceError as e:
        logger.error('Geocoder service error: %s', e)
        return '', ''

    if location is None:
        return '', ''

    addr = location.raw.get('address', {})

    # Priority order for a usable location name
    name = (
        addr.get('city')
        or addr.get('town')
        or addr.get('village')
        or addr.get('suburb')
        or addr.get('county')
        or addr.get('state_district')
        or addr.get('state')
        or addr.get('country')
        or ''
    )

    return name, slugify(name)


class Command(BaseCommand):
    help = 'Reverse-geocode tutor coordinates into location_name / location_slug on CustomUser.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-geocode ALL tutors, not just those missing location_slug.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be set without saving to the database.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Process at most LIMIT tutors (useful for testing).',
        )

    def handle(self, *args, **options):
        force   = options['force']
        dry_run = options['dry_run']
        limit   = options['limit']

        geocoder = Nominatim(user_agent=USER_AGENT)

        qs = CustomUser.objects.filter(
            is_teacher=True,
            banned=False,
            location__isnull=False,   # must have a Point stored
        ).select_related()

        if not force:
            # Only process users who haven't been geocoded yet
            qs = qs.filter(location_slug__isnull=True) | qs.filter(location_slug='')
            # Django ORM doesn't support | on querysets with different filters cleanly
            # Rewrite as:
            qs = CustomUser.objects.filter(
                is_teacher=True,
                banned=False,
                location__isnull=False,
            ).exclude(
                location_slug__isnull=False,
                location_slug__gt='',
            )

        if limit:
            qs = qs[:limit]

        total = qs.count() if not limit else min(qs.count(), limit)
        self.stdout.write(
            self.style.NOTICE(
                f'Processing {total} user(s). force={force}, dry_run={dry_run}'
            )
        )

        updated = 0
        errors  = 0

        for user in qs.iterator(chunk_size=50):
            point = user.location
            lat, lon = point.y, point.x

            name, slug = _reverse_geocode(geocoder, lat, lon)

            if not name:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Could not geocode user pk={user.pk} ({lat}, {lon})'
                    )
                )
                errors += 1
            else:
                self.stdout.write(
                    f'  User pk={user.pk} → "{name}" ({slug})'
                )
                if not dry_run:
                    CustomUser.objects.filter(pk=user.pk).update(
                        location_name=name,
                        location_slug=slug,
                    )
                updated += 1

            # Respect Nominatim rate limit
            time.sleep(RATE_LIMIT_SECONDS)

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Updated={updated}, Errors={errors}, Dry-run={dry_run}'
            )
        )
