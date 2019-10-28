import json
from binascii import unhexlify

from twisted.web import http

from module_loader.REST.root_endpoint import ModuleEndpoint
from module_loader.community.module.core.module_identifier import ModuleIdentifier


class ModuleCatalogEndpoint(ModuleEndpoint):

    def __init__(self, ipv8):
        ModuleEndpoint.__init__(self, ipv8)

    def getChild(self, path, request):
        return ModuleCatalogCreatorEndpoint(self.ipv8, path)

    def render_GET(self, request):
        modules = [module.to_dict() for module in self.get_module_overlay().persistence.get_modules_from_catalog()]
        return json.dumps({'modules': modules})


class ModuleCatalogCreatorEndpoint(ModuleEndpoint):

    def __init__(self, ipv8, creator):
        ModuleEndpoint.__init__(self, ipv8)
        self._creator = unhexlify(creator)

    def getChild(self, path, request):
        return ModuleCatalogContentHashEndpoint(self.ipv8, self._creator, path)


class ModuleCatalogContentHashEndpoint(ModuleEndpoint):

    def __init__(self, ipv8, creator, content_hash):
        ModuleEndpoint.__init__(self, ipv8)
        self._creator = creator
        self._content_hash = content_hash
        self._identifier = ModuleIdentifier(creator, content_hash)

    def render_GET(self, request):
        if not self.get_module_overlay().persistence.has_module_in_catalog(self._identifier):
            request.setResponseCode(http.NOT_FOUND)
            return json.dumps({"error": "module not found in library"})

        modules = self.get_module_overlay().persistence.get_module_from_catalog(self._identifier).to_dict()
        return json.dumps({'modules': modules})
