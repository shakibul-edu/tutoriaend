"""
seo/pagination.py
=================
Cursor-based pagination for the SEO tutor list.

Why cursor, not page-number?
-----------------------------
At 100 k+ rows, page-number pagination (LIMIT x OFFSET y) degrades
badly because PostgreSQL must count and skip all preceding rows for
each page.  Cursor pagination always issues a constant-cost WHERE clause:

    WHERE id > :last_seen_id ORDER BY id LIMIT :page_size

This stays fast at any page depth.

For the smaller tables (subjects, grades, locations) we use
the simple ListAPIView without pagination — those return ≤ a few
hundred rows and the full payload is cache-served in milliseconds.

Usage example (Next.js sitemap):
---------------------------------
    # Page 1
    GET /api/seo/tutors/
    Response headers: X-Next-Cursor: eyJpZCI6IDUwfQ==

    # Next page
    GET /api/seo/tutors/?cursor=eyJpZCI6IDUwfQ==

    # When X-Next-Cursor is absent → last page reached
"""

from rest_framework.pagination import CursorPagination


class SeoTutorCursorPagination(CursorPagination):
    """
    Cursor pagination for the tutor sitemap list.

    ordering = 'id'  — stable, index-backed, never changes per row.
                        (updated_at could cause rows to be re-visited
                         or skipped if profiles update during crawl.)
    page_size = 500  — each page is tiny JSON (slug + timestamp only),
                        so 500 rows is safe and reduces round-trips for
                        the sitemap generator.
    """
    page_size = 500
    ordering = 'id'                     # must match DB index
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'
    max_page_size = 1000
