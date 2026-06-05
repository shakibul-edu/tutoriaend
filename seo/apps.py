from django.apps import AppConfig


class SeoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seo'
    verbose_name = 'SEO Endpoints'

    def ready(self):
        """Connect cache-invalidation signals when Django starts."""
        import seo.signals  # noqa: F401
