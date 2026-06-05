"""
seo/cache.py
============
Thin caching helpers used by the SEO views.

Strategy
--------
We use Django's low-level cache API (django.core.cache.cache) instead of
the @cache_page decorator because:

1. @cache_page caches the full HTTP response including headers — it can
   accidentally cache 40x responses when the DB is temporarily unavailable.
2. We want fine-grained TTL control per endpoint.
3. It lets us invalidate by key prefix (e.g. when a tutor updates their
   profile) without restarting the server.

Cache backend
-------------
* Production: configure Redis as the Django cache backend (see settings note).
* Development / staging: falls back to Django's LocMemCache (in-process dict).
  Nothing to set up, but doesn't survive restarts.

Recommended Redis settings (add to settings.py):

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "tutoria_seo",
            "TIMEOUT": 3600,      # default 1-hour TTL
        }
    }

TTL guidelines
--------------
Tutors list   : 1 hour  — profiles don't change that often
Locations     : 6 hours — basically static, only changes when new areas open
Subjects      : 6 hours — curriculum changes are rare
Classes       : 6 hours
Combo pages   : 2 hours — slightly more dynamic (tutors join/leave areas)
"""

from django.core.cache import cache

# ----- TTL constants (seconds) -------------------------------------------
TUTOR_LIST_TTL = 60 * 60        # 1 hour
LOCATION_TTL   = 60 * 60 * 6   # 6 hours
SUBJECT_TTL    = 60 * 60 * 6
CLASS_TTL      = 60 * 60 * 6
COMBO_TTL      = 60 * 60 * 2   # 2 hours

# ----- Cache key prefixes -------------------------------------------------
TUTOR_KEY          = 'seo:tutors:v1'
LOCATION_KEY       = 'seo:locations:v1'
SUBJECT_KEY        = 'seo:subjects:v1'
CLASS_KEY          = 'seo:classes:v1'
SUBJ_LOC_KEY       = 'seo:subject_location_pages:v1'
CLASS_LOC_KEY      = 'seo:class_location_pages:v1'


def get_or_set(key: str, builder_fn, ttl: int):
    """
    Generic helper: return cached value or call builder_fn() to populate.

    builder_fn must return a JSON-serialisable list/dict — i.e., already
    converted from querysets to Python primitives (list of dicts).

    We intentionally store the **already-serialised** Python structure, not
    the raw queryset, so Django doesn't need to re-evaluate ORM expressions
    on cache hit.
    """
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = builder_fn()
    cache.set(key, value, ttl)
    return value


def invalidate_seo_cache():
    """
    Call this from signals or management commands whenever tutor data
    changes in bulk (e.g. import script, nightly geocoding run).

    For per-profile invalidation on save, see the signal in seo/signals.py.
    """
    keys = [
        TUTOR_KEY, LOCATION_KEY, SUBJECT_KEY,
        CLASS_KEY, SUBJ_LOC_KEY, CLASS_LOC_KEY,
    ]
    cache.delete_many(keys)
