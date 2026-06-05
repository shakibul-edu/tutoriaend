"""
seo/urls.py
===========
URL configuration for all SEO endpoints.
These are included under the prefix /api/seo/ in tutoria/urls.py.
"""

from django.urls import path
from .views import (
    SeoTutorListView,
    SeoLocationListView,
    SeoSubjectListView,
    SeoClassListView,
    SeoSubjectLocationPageView,
    SeoClassLocationPageView,
    SeoTutorDetailView,
    SeoLocationDetailView,
    SeoSubjectDetailView,
    SeoClassDetailView,
)

app_name = 'seo'

urlpatterns = [
    # ── Sitemap data ──────────────────────────────────────────────────────
    # Paginated (cursor-based) — intended for Next.js sitemap/[page].xml
    path('tutors/',                  SeoTutorListView.as_view(),           name='seo-tutors'),
    path('tutors/<slug>/',           SeoTutorDetailView.as_view(),         name='seo-tutor-detail'),

    # Small, fully-cached lists — can be fetched once and held in memory
    path('locations/',               SeoLocationListView.as_view(),        name='seo-locations'),
    path('locations/<slug>/',        SeoLocationDetailView.as_view(),      name='seo-location-detail'),
    path('subjects/',                SeoSubjectListView.as_view(),         name='seo-subjects'),
    path('subjects/<slug>/',         SeoSubjectDetailView.as_view(),       name='seo-subject-detail'),
    path('classes/',                 SeoClassListView.as_view(),           name='seo-classes'),
    path('classes/<slug>/',          SeoClassDetailView.as_view(),         name='seo-class-detail'),

    # ── Programmatic page generation ──────────────────────────────────────
    # Used by Next.js generateStaticParams() to build dynamic route paths
    path('subject-location-pages/',  SeoSubjectLocationPageView.as_view(), name='seo-subject-location-pages'),
    path('class-location-pages/',    SeoClassLocationPageView.as_view(),   name='seo-class-location-pages'),
]
