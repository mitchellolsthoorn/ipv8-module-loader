import json
from binascii import unhexlify

from twisted.web import http

from loader.REST.root_endpoint import DAppEndpoint
from loader.community.dapp.core.dapp_identifier import DAppIdentifier


class DAppDownloadsEndpoint(DAppEndpoint):

    def __init__(self, ipv8):
        DAppEndpoint.__init__(self, ipv8)

    def getChild(self, path, request):
        return DAppDownloadsCreatorEndpoint(self.ipv8, path)


class DAppDownloadsCreatorEndpoint(DAppEndpoint):

    def __init__(self, ipv8, creator):
        DAppEndpoint.__init__(self, ipv8)
        self._creator = unhexlify(creator)

    def getChild(self, path, request):
        return DAppDownloadsContentHashEndpoint(self.ipv8, self._creator, path)


class DAppDownloadsContentHashEndpoint(DAppEndpoint):

    def __init__(self, ipv8, creator, content_hash):
        DAppEndpoint.__init__(self, ipv8)
        self._creator = creator
        self._content_hash = content_hash
        self._identifier = DAppIdentifier(creator, content_hash)

    def render_GET(self, request):
        if not self.get_dapp_overlay().persistence.has_dapp_in_catalog(self._identifier):
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "dApp not found in library"})

        self.get_dapp_overlay().download_dapp(self._identifier)

        return json.dumps({'status': "Downloading"})
