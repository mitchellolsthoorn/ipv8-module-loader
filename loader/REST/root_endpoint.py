from twisted.web import resource


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
