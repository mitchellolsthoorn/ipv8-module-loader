import json
from binascii import unhexlify

from twisted.web import http

from module_loader.REST.root_endpoint import ModuleEndpoint
from module_loader.community.module.core.module_identifier import ModuleIdentifier


class ModuleVotesEndpoint(ModuleEndpoint):

    def __init__(self, ipv8):
        ModuleEndpoint.__init__(self, ipv8)

    def getChild(self, path, request):
        return ModuleVotesCreatorEndpoint(self.ipv8, path)


class ModuleVotesCreatorEndpoint(ModuleEndpoint):

    def __init__(self, ipv8, creator):
        ModuleEndpoint.__init__(self, ipv8)
        self._creator = unhexlify(creator)

    def getChild(self, path, request):
        return ModuleVotesContentHashEndpoint(self.ipv8, self._creator, path)


class ModuleVotesContentHashEndpoint(ModuleEndpoint):

    def __init__(self, ipv8, creator, content_hash):
        ModuleEndpoint.__init__(self, ipv8)
        self._creator = creator
        self._content_hash = content_hash
        self._identifier = ModuleIdentifier(creator, content_hash)

    def render_GET(self, request):
        if not self.get_module_overlay().persistence.has_module_in_catalog(self._identifier):
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "module not found in library"})

        self.get_module_overlay().vote_module(self._identifier)

        return json.dumps({'status': "Voted"})
