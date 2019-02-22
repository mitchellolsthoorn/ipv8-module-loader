from twisted.web import resource
from twisted.web.resource import _computeAllowedMethods


class DAppRootEndpoint(resource.Resource):

    def __init__(self, ipv8):
        resource.Resource.__init__(self)
        self.ipv8 = ipv8

        from loader.REST.cache_endpoint import DAppCacheEndpoint
        self.putChild('cache', DAppCacheEndpoint(self.ipv8))
        from loader.REST.catalog_endpoint import DAppCatalogEndpoint
        self.putChild('catalog', DAppCatalogEndpoint(self.ipv8))
        from loader.REST.library_endpoint import DAppLibraryEndpoint
        self.putChild('library', DAppLibraryEndpoint(self.ipv8))
        from loader.REST.votes_endpoint import DAppVotesEndpoint
        self.putChild('votes', DAppVotesEndpoint(self.ipv8))
        from loader.REST.downloads_endpoint import DAppDownloadsEndpoint
        self.putChild('downloads', DAppDownloadsEndpoint(self.ipv8))
        from loader.REST.run_endpoint import DAppRunEndpoint
        self.putChild('run', DAppRunEndpoint(self.ipv8))


class DAppEndpoint(resource.Resource):
    def __init__(self, ipv8):
        resource.Resource.__init__(self)
        self.ipv8 = ipv8

    def get_dapp_overlay(self):
        for overlay in self.ipv8.overlays:
            from loader.community.dapp.community import DAppCommunity
            if isinstance(overlay, DAppCommunity):
                return overlay

    def render_OPTIONS(self, request):
        """
        This methods renders the HTTP OPTIONS method used for returning available HTTP methods and Cross-Origin Resource
        Sharing preflight request checks.
        """
        # Check if the allowed methods were explicitly set, otherwise compute them automatically
        try:
            allowed_methods = self.allowedMethods
        except AttributeError:
            allowed_methods = _computeAllowedMethods(self)
        allowed_methods_string = " ".join(allowed_methods)

        # Set the header for the HTTP OPTION method
        request.setHeader(b'Allow', allowed_methods_string)

        # Set the required headers for preflight checks
        if request.getHeader(b'Access-Control-Request-Headers'):
            request.setHeader(b'Access-Control-Allow-Headers', request.getHeader(b'Access-Control-Request-Headers'))
        request.setHeader(b'Access-Control-Allow-Methods', allowed_methods_string)
        request.setHeader(b'Access-Control-Max-Age', 86400)

        # Return empty body
        return ""
