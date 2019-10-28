from twisted.web import resource
from twisted.web.resource import _computeAllowedMethods


class ModuleRootEndpoint(resource.Resource):

    def __init__(self, ipv8):
        resource.Resource.__init__(self)
        self.ipv8 = ipv8

        from module_loader.REST.cache_endpoint import ModuleCacheEndpoint
        self.putChild('cache', ModuleCacheEndpoint(self.ipv8))
        from module_loader.REST.catalog_endpoint import ModuleCatalogEndpoint
        self.putChild('catalog', ModuleCatalogEndpoint(self.ipv8))
        from module_loader.REST.library_endpoint import ModuleLibraryEndpoint
        self.putChild('library', ModuleLibraryEndpoint(self.ipv8))
        from module_loader.REST.votes_endpoint import ModuleVotesEndpoint
        self.putChild('votes', ModuleVotesEndpoint(self.ipv8))
        from module_loader.REST.downloads_endpoint import ModuleDownloadsEndpoint
        self.putChild('downloads', ModuleDownloadsEndpoint(self.ipv8))
        from module_loader.REST.run_endpoint import ModuleRunEndpoint
        self.putChild('run', ModuleRunEndpoint(self.ipv8))


class ModuleEndpoint(resource.Resource):
    def __init__(self, ipv8):
        resource.Resource.__init__(self)
        self.ipv8 = ipv8

    def get_module_overlay(self):
        for overlay in self.ipv8.overlays:
            from module_loader.community.module.community import ModuleCommunity
            if isinstance(overlay, ModuleCommunity):
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
