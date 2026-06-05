"""
seo/signals.py
==============
Django signals that keep the SEO cache in sync when tutor data changes.

Connected in SeoConfig.ready() (see seo/apps.py).

What's invalidated
------------------
* TeacherProfile.post_save  → clear TUTOR_KEY, SUBJ_LOC_KEY, CLASS_LOC_KEY
  (slug, updated_at, subject_list, grade_list may all have changed)

* CustomUser.post_save       → clear LOCATION_KEY
  (location_name / location_slug may have changed)

We only wipe the keys that are actually affected, not the entire cache.

Performance note
----------------
cache.delete / cache.delete_many are O(1) Redis operations.
The signal fires at most once per profile save — not per request.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from base.models import TeacherProfile, CustomUser
from .cache import cache, TUTOR_KEY, LOCATION_KEY, SUBJ_LOC_KEY, CLASS_LOC_KEY

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TeacherProfile)
def invalidate_tutor_seo_cache(sender, instance, **kwargs):
    """
    Invalidate tutor-related SEO caches whenever a TeacherProfile is saved.

    We delete TUTOR_KEY so the next request rebuilds the tutor list.
    We also delete SUBJ_LOC_KEY and CLASS_LOC_KEY because a tutor may
    have changed their subject_list or grade_list, altering what
    programmatic pages exist.
    We also delete the individual tutor's detail cache key.
    """
    keys = [TUTOR_KEY, SUBJ_LOC_KEY, CLASS_LOC_KEY]
    if instance.slug:
        keys.append(f'seo:tutors:detail:{instance.slug}')
    cache.delete_many(keys)
    logger.debug(
        'SEO cache invalidated (tutor save): profile pk=%s, keys=%s',
        instance.pk, keys,
    )


@receiver(post_save, sender=CustomUser)
def invalidate_location_seo_cache(sender, instance, **kwargs):
    """
    Invalidate the location cache when a user's location_slug changes.

    We don't invalidate ALL keys here — only LOCATION_KEY, because
    user saves happen much more frequently (login updates, etc.) and
    we don't want to thrash the tutor/combo caches unnecessarily.
    """
    cache.delete(LOCATION_KEY)
    logger.debug(
        'SEO location cache invalidated (user save): user pk=%s', instance.pk
    )
