import json
from binascii import unhexlify

from twisted.web import http

from module_loader.REST.root_endpoint import ModuleEndpoint
from module_loader.community.module.core.module_identifier import ModuleIdentifier


class ModuleCacheEndpoint(ModuleEndpoint):

    def __init__(self, ipv8):
        ModuleEndpoint.__init__(self, ipv8)

    def getChild(self, path, request):
        return ModuleCacheCreatorEndpoint(self.ipv8, path)

    def render_GET(self, request):
        module_identifiers = [module.to_dict() for module in self.get_module_overlay().persistence.get_modules_from_cache()]
        return json.dumps({'module_identifiers': module_identifiers})


class ModuleCacheCreatorEndpoint(ModuleEndpoint):

    def __init__(self, ipv8, creator):
        ModuleEndpoint.__init__(self, ipv8)
        self._creator = unhexlify(creator)

    def getChild(self, path, request):
        return ModuleCacheContentHashEndpoint(self.ipv8, self._creator, path)


class ModuleCacheContentHashEndpoint(ModuleEndpoint):

    def __init__(self, ipv8, creator, content_hash):
        ModuleEndpoint.__init__(self, ipv8)
        self._creator = creator
        self._content_hash = content_hash
        self._identifier = ModuleIdentifier(creator, content_hash)

    def render_GET(self, request):
        if not self.get_module_overlay().persistence.has_module_in_cache(self._identifier):
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "module not found in cache"})

        module_identifiers = self.get_module_overlay().persistence.get_module_from_cache(self._identifier).to_dict()
        return json.dumps({'module_identifiers': module_identifiers})
