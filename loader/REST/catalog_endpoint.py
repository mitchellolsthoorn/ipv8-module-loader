import json
from binascii import unhexlify

from twisted.web import http

from loader.REST.root_endpoint import DAppEndpoint
from loader.community.dapp.core.dapp_identifier import DAppIdentifier


class DAppCatalogEndpoint(DAppEndpoint):

    def __init__(self, ipv8):
        DAppEndpoint.__init__(self, ipv8)

    def getChild(self, path, request):
        return DAppCatalogCreatorEndpoint(self.ipv8, path)

    def render_GET(self, request):
        dapps = [dapp.to_dict() for dapp in self.get_dapp_overlay().persistence.get_dapps_from_catalog()]
        return json.dumps({'dapps': dapps})


class DAppCatalogCreatorEndpoint(DAppEndpoint):

    def __init__(self, ipv8, creator):
        DAppEndpoint.__init__(self, ipv8)
        self._creator = unhexlify(creator)

    def getChild(self, path, request):
        return DAppCatalogContentHashEndpoint(self.ipv8, self._creator, path)


class DAppCatalogContentHashEndpoint(DAppEndpoint):

    def __init__(self, ipv8, creator, content_hash):
        DAppEndpoint.__init__(self, ipv8)
        self._creator = creator
        self._content_hash = content_hash
        self._identifier = DAppIdentifier(creator, content_hash)

    def render_GET(self, request):
        if not self.get_dapp_overlay().persistence.has_dapp_in_catalog(self._identifier):
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "dApp not found in library"})

        dapps = self.get_dapp_overlay().persistence.get_dapp_from_catalog(self._identifier).to_dict()
        return json.dumps({'dapps': dapps})
