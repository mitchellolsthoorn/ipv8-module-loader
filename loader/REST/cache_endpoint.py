import json
from binascii import unhexlify

from twisted.web import http

from loader.REST.root_endpoint import DAppEndpoint
from loader.community.dapp.core.dapp_identifier import DAppIdentifier


class DAppCacheEndpoint(DAppEndpoint):

    def __init__(self, ipv8):
        DAppEndpoint.__init__(self, ipv8)

    def getChild(self, path, request):
        return DAppCacheCreatorEndpoint(self.ipv8, path)

    def render_GET(self, request):
        dapp_identifiers = [dapp.to_dict() for dapp in self.get_dapp_overlay().persistence.get_dapps_from_cache()]
        return json.dumps({'dapp_identifiers': dapp_identifiers})


class DAppCacheCreatorEndpoint(DAppEndpoint):

    def __init__(self, ipv8, creator):
        DAppEndpoint.__init__(self, ipv8)
        self._creator = unhexlify(creator)

    def getChild(self, path, request):
        return DAppCacheContentHashEndpoint(self.ipv8, self._creator, path)


class DAppCacheContentHashEndpoint(DAppEndpoint):

    def __init__(self, ipv8, creator, content_hash):
        DAppEndpoint.__init__(self, ipv8)
        self._creator = creator
        self._content_hash = content_hash
        self._identifier = DAppIdentifier(creator, content_hash)

    def render_GET(self, request):
        if not self.get_dapp_overlay().persistence.has_dapp_in_cache(self._identifier):
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "dApp not found in cache"})

        dapp_identifiers = self.get_dapp_overlay().persistence.get_dapp_from_cache(self._identifier).to_dict()
        return json.dumps({'dapp_identifiers': dapp_identifiers})
