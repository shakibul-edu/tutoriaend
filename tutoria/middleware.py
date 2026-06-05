class DisableAPICacheMiddleware:
    """
    Adds no-store Cache-Control headers to all /api/ responses.

    Exception: /api/seo/* endpoints are public, read-only, and benefit
    from edge caching (CDN / Cloudflare), so we skip them here.
    Django's server-side cache (cache.get/set) is separate and always active.
    """

    # SEO paths that should be cacheable at the HTTP / CDN level
    _SEO_PREFIX = '/api/seo/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/') and not request.path.startswith(self._SEO_PREFIX):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response

