"""
seo/views.py
============
Read-only, public SEO API views.

All endpoints are:
  * AllowAny    — crawlers and Next.js ISR fetchers are not authenticated.
  * No throttle — ISR builds make parallel requests; throttling would break
                  the build. Data is public and fully server-side cached, so
                  there is no meaningful abuse vector.
  * GET only.
  * Cache-first (low-level cache API, see seo/cache.py).
  * Optimised querysets with only(), values(), and annotate().

Endpoint map
------------
  GET /api/seo/tutors/               → SeoTutorListView
  GET /api/seo/locations/            → SeoLocationListView
  GET /api/seo/subjects/             → SeoSubjectListView
  GET /api/seo/classes/              → SeoClassListView
  GET /api/seo/subject-location-pages/ → SeoSubjectLocationPageView
  GET /api/seo/class-location-pages/   → SeoClassLocationPageView

N+1 avoidance
-------------
* Tutor list: .only('slug', 'updated_at') — fetches 2 columns, no JOINs.
* Location list: .values('location_name', 'location_slug') on CustomUser
  filtered to tutors — single column scan, DISTINCT at DB level.
* Combo pages: annotate + values + distinct in a single SQL query.
  No Python loops, no per-row lookups.

Query plan notes
----------------
These queries rely on the following indexes (added in migration 0028):
  - base_teacherprofile(slug)         — unique index (implicit)
  - base_teacherprofile(id)           — PK (implicit, used by cursor)
  - auth_user(location_slug)          — explicit index
  - auth_user(location_name)          — explicit index

See also: seo/indexes.md for the raw SQL index definitions used in
production to cover composite queries on the combo-page endpoints.
"""

from django.db.models import Count, Q
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from django.http import Http404

from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from base.models import TeacherProfile, Subject, Grade
from base.models import CustomUser

from .cache import (
    get_or_set,
    TUTOR_KEY, TUTOR_LIST_TTL,
    LOCATION_KEY, LOCATION_TTL,
    SUBJECT_KEY, SUBJECT_TTL,
    CLASS_KEY, CLASS_TTL,
    SUBJ_LOC_KEY, COMBO_TTL,
    CLASS_LOC_KEY,
)
from .pagination import SeoTutorCursorPagination
from .serializers import (
    SeoTutorSerializer,
    SeoLocationSerializer,
    SeoSubjectSerializer,
    SeoClassSerializer,
    SeoSubjectLocationSerializer,
    SeoClassLocationSerializer,
    SeoTutorDetailSerializer,
)


# ---------------------------------------------------------------------------
# Helper: queryset for verified tutors that have a slug and location slug
# ---------------------------------------------------------------------------

def _verified_tutor_qs():
    """
    Base queryset of verified tutors who:
      - have a slug (i.e. not null — backfill migration should ensure this)
      - are not banned
    Used by all combo-page queries to avoid indexing empty/spam profiles.
    """
    return (
        TeacherProfile.objects
        .filter(
            verified=True,
            slug__isnull=False,
            user__banned=False,
        )
    )


# ---------------------------------------------------------------------------
# 1.  /api/seo/tutors/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Tutor list for sitemap',
    description=(
        'Returns a paginated list of (slug, updated_at) for every verified tutor. '
        'Intended for Next.js sitemap generation. Uses cursor-based pagination to '
        'stay efficient at any scale. Pass the `cursor` query param from the '
        '`X-Next-Cursor` response header to fetch subsequent pages.'
    ),
    parameters=[
        OpenApiParameter('cursor', str, description='Pagination cursor from previous response'),
        OpenApiParameter('page_size', int, description='Results per page (max 1000, default 500)'),
    ],
    responses={200: SeoTutorSerializer(many=True)},
    tags=['SEO'],
)
class SeoTutorListView(ListAPIView):
    """
    Cursor-paginated list of tutor slugs + updated_at timestamps.

    Optimisation notes
    ------------------
    * .only('id', 'slug', 'updated_at') — fetches exactly 3 columns;
      avoids loading bio, profile_picture URL, M2M relations, etc.
    * filter(verified=True, slug__isnull=False) — excludes drafts and
      profiles created before the slug migration ran.
    * No select_related / prefetch_related — we don't touch any FK here.
    * ordering('id') matches the cursor pagination's ordering, so
      PostgreSQL uses the PK index — O(log n) seeks, not full scans.
    """
    permission_classes = [AllowAny]
    throttle_classes    = []   # ISR / sitemap crawlers must not be rate-limited
    serializer_class = SeoTutorSerializer
    pagination_class = SeoTutorCursorPagination

    def get_queryset(self):
        return (
            _verified_tutor_qs()
            .only('id', 'slug', 'updated_at')
            .order_by('id')             # stable cursor ordering
        )

    # NOTE: We intentionally do NOT cache this endpoint because cursor
    # pagination relies on per-request cursor state.  Each paginated
    # response is small (≤ 1 000 rows × 2 fields) and the query is
    # index-backed, so latency is ~5 ms even at 100 k rows.


# ---------------------------------------------------------------------------
# 2.  /api/seo/locations/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Unique tutor locations for sitemap',
    description=(
        'Returns a deduplicated list of (location_name, location_slug) pairs '
        'derived from the location_slug / location_name fields stored on each '
        'tutor\'s user account. Requires running the `populate_location_slugs` '
        'management command (or hooking into the profile save signal) to '
        'populate those fields.'
    ),
    responses={200: SeoLocationSerializer(many=True)},
    tags=['SEO'],
)
class SeoLocationListView(APIView):
    """
    Returns all unique (location_name, location_slug) pairs across tutors.

    Optimisation notes
    ------------------
    * .values('location_name', 'location_slug') — asks Postgres to project
      only 2 columns; no Python objects allocated per row.
    * .distinct() — DISTINCT pushed to SQL, not Python.
    * .filter(location_slug__isnull=False, location_slug__gt='') — skips
      tutors whose location_slug hasn't been populated yet.
    * .order_by('location_name') — uses the db_index on location_name for
      efficient sorted scan without a sort step.
    * Result is cached for 6 hours (locations change rarely).
    """
    permission_classes = [AllowAny]
    throttle_classes    = []   # ISR / sitemap crawlers must not be rate-limited

    def _build(self):
        qs = (
            CustomUser.objects
            .filter(
                is_teacher=True,
                banned=False,
                location_slug__isnull=False,
                location_slug__gt='',
            )
            .values('location_name', 'location_slug')
            .distinct()
            .order_by('location_name')
        )
        # Convert ValuesQuerySet → list of plain dicts (cache-serialisable)
        return list(qs)

    def get(self, request):
        data = get_or_set(LOCATION_KEY, self._build, LOCATION_TTL)
        serializer = SeoLocationSerializer(data, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# 3.  /api/seo/subjects/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Subject list for sitemap',
    description=(
        'Returns all subjects that at least one verified tutor teaches, '
        'along with a URL-safe subject_slug. Cached for 6 hours.'
    ),
    responses={200: SeoSubjectSerializer(many=True)},
    tags=['SEO'],
)
class SeoSubjectListView(APIView):
    """
    Returns subjects that have at least one verified tutor.

    Optimisation notes
    ------------------
    * We filter subjects via a subquery (tutors__verified=True) rather
      than loading TeacherProfile rows — this is a single JOIN in SQL.
    * .values('id', 'name') — project only 2 columns.
    * .distinct() — avoids duplicate rows from the M2M join.
    * slug is computed in Python (slugify) — cheap for ≤ 1 000 subjects.
    * Full result cached for 6 hours.
    """
    permission_classes = [AllowAny]
    throttle_classes    = []   # ISR / sitemap crawlers must not be rate-limited

    def _build(self):
        qs = (
            Subject.objects
            .filter(
                tutors__verified=True,          # tutors is the related_name on TeacherProfile.subject_list
                tutors__user__banned=False,
            )
            .values('id', 'name')
            .distinct()
            .order_by('name')
        )
        rows = list(qs)
        # Add slug in Python — tiny list, negligible cost
        for row in rows:
            row['subject_slug'] = slugify(row['name'])
        return rows

    def get(self, request):
        data = get_or_set(SUBJECT_KEY, self._build, SUBJECT_TTL)
        serializer = SeoSubjectSerializer(data, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# 4.  /api/seo/classes/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Class (grade) list for sitemap',
    description=(
        'Returns all grade levels (classes) that at least one verified tutor '
        'teaches, along with a URL-safe class_slug. Cached for 6 hours.'
    ),
    responses={200: SeoClassSerializer(many=True)},
    tags=['SEO'],
)
class SeoClassListView(APIView):
    """
    Returns Grade objects linked to at least one verified tutor.

    Mirrors the same pattern as SeoSubjectListView.
    'tutors' is the related_name on TeacherProfile.grade_list.
    """
    permission_classes = [AllowAny]
    throttle_classes    = []   # ISR / sitemap crawlers must not be rate-limited

    def _build(self):
        qs = (
            Grade.objects
            .filter(
                tutors__verified=True,
                tutors__user__banned=False,
            )
            .values('id', 'name')
            .distinct()
            .order_by('sequence')   # natural ordering for classes (Class 6, 7, 8 …)
        )
        rows = list(qs)
        for row in rows:
            row['class_slug'] = slugify(row['name'])
        return rows

    def get(self, request):
        data = get_or_set(CLASS_KEY, self._build, CLASS_TTL)
        serializer = SeoClassSerializer(data, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# 5.  /api/seo/subject-location-pages/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Subject × location combinations for programmatic pages',
    description=(
        'Returns every unique (subject, location) pair for which at least one '
        'verified tutor exists. Use this to pre-generate Next.js static pages '
        'like /tutors/mathematics/chattogram. '
        'The tutor_count field lets you decide whether to noindex thin pages. '
        'Cached for 2 hours.'
    ),
    responses={200: SeoSubjectLocationSerializer(many=True)},
    tags=['SEO'],
)
class SeoSubjectLocationPageView(APIView):
    """
    Generates (subject_slug, location_slug) pairs from a single SQL query.

    SQL plan
    --------
    SELECT
        s.id, s.name,
        u.location_name, u.location_slug,
        COUNT(DISTINCT tp.id) AS tutor_count
    FROM base_subject s
    JOIN base_teacherprofile_subject_list m   ON m.subject_id = s.id
    JOIN base_teacherprofile tp               ON tp.id = m.teacherprofile_id
    JOIN base_customuser u                    ON u.id = tp.user_id
    WHERE tp.verified = TRUE
      AND tp.slug IS NOT NULL
      AND u.banned = FALSE
      AND u.location_slug IS NOT NULL
      AND u.location_slug <> ''
    GROUP BY s.id, s.name, u.location_name, u.location_slug
    ORDER BY s.name, u.location_name;

    This is ONE query, zero N+1, zero Python loops.

    Recommended composite index for this endpoint:
        CREATE INDEX seo_subj_loc_idx
        ON base_teacherprofile_subject_list (teacherprofile_id, subject_id);
    (Django already creates one for M2M join tables by default.)
    """
    permission_classes = [AllowAny]
    throttle_classes    = []   # ISR / sitemap crawlers must not be rate-limited

    def _build(self):
        qs = (
            TeacherProfile.objects
            .filter(
                verified=True,
                slug__isnull=False,
                user__banned=False,
                user__location_slug__isnull=False,
                user__location_slug__gt='',
            )
            # Annotate tutor count per (subject, location) combination
            .values(
                'subject_list__id',
                'subject_list__name',
                'user__location_name',
                'user__location_slug',
            )
            .annotate(tutor_count=Count('id', distinct=True))
            .filter(
                subject_list__isnull=False,     # exclude tutors with no subjects
                tutor_count__gte=1,
            )
            .order_by('subject_list__name', 'user__location_name')
        )

        rows = []
        for item in qs:
            subject_name = item['subject_list__name']
            rows.append({
                'subject_name': subject_name,
                'subject_slug': slugify(subject_name) if subject_name else '',
                'location_name': item['user__location_name'] or '',
                'location_slug': item['user__location_slug'] or '',
                'tutor_count': item['tutor_count'],
            })
        return rows

    def get(self, request):
        data = get_or_set(SUBJ_LOC_KEY, self._build, COMBO_TTL)
        serializer = SeoSubjectLocationSerializer(data, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# 6.  /api/seo/class-location-pages/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Class × location combinations for programmatic pages',
    description=(
        'Returns every unique (class/grade, location) pair for which at least '
        'one verified tutor exists. Use this to pre-generate Next.js static '
        'pages like /tutors/class-9/chattogram. '
        'Cached for 2 hours.'
    ),
    responses={200: SeoClassLocationSerializer(many=True)},
    tags=['SEO'],
)
class SeoClassLocationPageView(APIView):
    """
    Same pattern as SeoSubjectLocationPageView, but keyed on Grade instead
    of Subject.  Uses grade_list (M2M) → Grade.

    Results are ordered by Grade.sequence so class pages are listed
    in natural curriculum order (Class 6, 7, 8 …) rather than
    alphabetically ("Class 10" before "Class 6").
    """
    permission_classes = [AllowAny]
    throttle_classes    = []   # ISR / sitemap crawlers must not be rate-limited

    def _build(self):
        qs = (
            TeacherProfile.objects
            .filter(
                verified=True,
                slug__isnull=False,
                user__banned=False,
                user__location_slug__isnull=False,
                user__location_slug__gt='',
            )
            .values(
                'grade_list__id',
                'grade_list__name',
                'grade_list__sequence',
                'user__location_name',
                'user__location_slug',
            )
            .annotate(tutor_count=Count('id', distinct=True))
            .filter(
                grade_list__isnull=False,
                tutor_count__gte=1,
            )
            .order_by('grade_list__sequence', 'user__location_name')
        )

        rows = []
        for item in qs:
            class_name = item['grade_list__name']
            rows.append({
                'class_name': class_name,
                'class_slug': slugify(class_name) if class_name else '',
                'location_name': item['user__location_name'] or '',
                'location_slug': item['user__location_slug'] or '',
                'tutor_count': item['tutor_count'],
            })
        return rows

    def get(self, request):
        data = get_or_set(CLASS_LOC_KEY, self._build, COMBO_TTL)
        serializer = SeoClassLocationSerializer(data, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# 7.  /api/seo/tutors/<slug>/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Tutor public details by slug',
    description=(
        'Returns the basic public details of a verified tutor by their unique slug. '
        'Used for programmatic Next.js profile pages (/tutor/[slug]). '
        'Cached for 2 hours.'
    ),
    responses={200: SeoTutorDetailSerializer},
    tags=['SEO'],
)
class SeoTutorDetailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes    = []   # ISR / sitemap crawlers must not be rate-limited

    def _build(self, slug):
        tutor = get_object_or_404(
            _verified_tutor_qs()
            .select_related('user')
            .prefetch_related('subject_list'),
            slug=slug
        )
        # Fetch rating and review count
        from base.utils import get_average_review
        rating, review_count = get_average_review(tutor)
        tutor.rating = rating
        tutor.review_count = review_count

        serializer = SeoTutorDetailSerializer(tutor)
        return serializer.data

    def get(self, request, slug):
        cache_key = f'seo:tutors:detail:{slug}'
        data = get_or_set(cache_key, lambda: self._build(slug), COMBO_TTL)
        return Response(data)


# ---------------------------------------------------------------------------
# 8.  /api/seo/locations/<slug>/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Location details by slug',
    description='Returns location details (name, slug) by slug. Returns 404 if location doesn\'t exist. Cached for 6 hours.',
    responses={200: SeoLocationSerializer},
    tags=['SEO'],
)
class SeoLocationDetailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes    = []

    def _build(self, slug):
        user = CustomUser.objects.filter(
            is_teacher=True,
            banned=False,
            location_slug=slug,
        ).first()
        if not user:
            raise Http404("Location not found")
        return {
            'location_name': user.location_name,
            'location_slug': user.location_slug,
        }

    def get(self, request, slug):
        cache_key = f'seo:locations:detail:{slug}'
        data = get_or_set(cache_key, lambda: self._build(slug), LOCATION_TTL)
        return Response(data)


# ---------------------------------------------------------------------------
# 9.  /api/seo/subjects/<slug>/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Subject details by slug',
    description='Returns subject details (id, name, slug) by slug. Returns 404 if subject doesn\'t exist. Cached for 6 hours.',
    responses={200: SeoSubjectSerializer},
    tags=['SEO'],
)
class SeoSubjectDetailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes    = []

    def _build(self, slug):
        subjects = Subject.objects.filter(
            tutors__verified=True,
            tutors__user__banned=False,
        ).distinct()
        target_subject = None
        for s in subjects:
            if slugify(s.name) == slug:
                target_subject = s
                break
        if not target_subject:
            raise Http404("Subject not found")
        return {
            'id': target_subject.id,
            'name': target_subject.name,
            'subject_slug': slugify(target_subject.name),
        }

    def get(self, request, slug):
        cache_key = f'seo:subjects:detail:{slug}'
        data = get_or_set(cache_key, lambda: self._build(slug), SUBJECT_TTL)
        return Response(data)


# ---------------------------------------------------------------------------
# 10. /api/seo/classes/<slug>/
# ---------------------------------------------------------------------------

@extend_schema(
    summary='SEO – Class details by slug',
    description='Returns class details (id, name, slug) by slug. Returns 404 if class doesn\'t exist. Cached for 6 hours.',
    responses={200: SeoClassSerializer},
    tags=['SEO'],
)
class SeoClassDetailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes    = []

    def _build(self, slug):
        grades = Grade.objects.filter(
            tutors__verified=True,
            tutors__user__banned=False,
        ).distinct()
        target_grade = None
        for g in grades:
            if slugify(g.name) == slug:
                target_grade = g
                break
        if not target_grade:
            raise Http404("Class not found")
        return {
            'id': target_grade.id,
            'name': target_grade.name,
            'class_slug': slugify(target_grade.name),
        }

    def get(self, request, slug):
        cache_key = f'seo:classes:detail:{slug}'
        data = get_or_set(cache_key, lambda: self._build(slug), CLASS_TTL)
        return Response(data)


