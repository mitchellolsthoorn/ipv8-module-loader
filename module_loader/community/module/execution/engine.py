import importlib
import json
import logging
import os

from ipv8_service import _COMMUNITIES, _WALKERS
from twisted.internet import reactor

from module_loader.community.module.transport.bittorrent import MODULES_DIR, EXECUTE_FILE


class ExecutionEngine(object):
    """
    Execution engine for modules
    """

    def __init__(self, working_directory, community):
        super(ExecutionEngine, self).__init__()

        self.working_directory = working_directory
        self.community = community

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

        # State
        self.imported_modules = []

    def run_module(self, module):
        name = module.name
        modules_directory = os.path.join(os.path.abspath(self.working_directory), MODULES_DIR)
        module_path = os.path.join(modules_directory, name)
        module_executable = os.path.join(module_path, EXECUTE_FILE)

        if os.path.isdir(module_path) and os.path.isfile(os.path.join(module_path, 'module.json')):
            self._logger.info("module-community: module (%s) found", name)

            with open(os.path.join(module_path, 'module.json')) as f:
                data = json.load(f)

                package_type = data['type']
                if package_type == "executable":
                    self._logger.info("module-community: executable module (%s) found", name)
                    executable_file = data['executable_file']

                    if module.id not in self.imported_modules:
                        importlib.import_module(name + "." + executable_file)
                        self.imported_modules.append(module.id)

                elif package_type == "overlay":
                    self._logger.info("module-community: module overlay (%s) found", name)

                    overlay_file = data['overlay_file']

                    if module.id not in self.imported_modules:
                        configuration = getattr(importlib.import_module(name + "." + overlay_file), "config")
                        extra_communities = getattr(importlib.import_module(name + "." + overlay_file),
                                                    "extra_communities")

                        for overlay in configuration['overlays']:
                            overlay_class = _COMMUNITIES.get(overlay['class'],
                                                             (extra_communities or {}).get(overlay['class']))
                            my_peer = self.community.my_peer
                            overlay_instance = overlay_class(my_peer, self.community.endpoint, self.community.network,
                                                             **overlay['initialize'])
                            self.community.ipv8.overlays.append(overlay_instance)
                            for walker in overlay['walkers']:
                                strategy_class = _WALKERS.get(walker['strategy'],
                                                              overlay_instance.get_available_strategies().get(
                                                                  walker['strategy']))
                                args = walker['init']
                                target_peers = walker['peers']
                                self.community.ipv8.strategies.append(
                                    (strategy_class(overlay_instance, **args), target_peers))
                            for config in overlay['on_start']:
                                reactor.callWhenRunning(getattr(overlay_instance, config[0]), *config[1:])
                            self._logger.info("module-community: module overlay (%s) added", overlay['class'])

                        self.imported_modules.append(module.id)

                elif package_type == "service":
                    self._logger.info("module-community: module service (%s) found", name)
                    service_file = data['service_file']
                    service_class = data['service_class']
                    service_options = data['service_options']

                    if module.id not in self.imported_modules:
                        cls = getattr(importlib.import_module(name + "." + service_file), service_class)
                        service = cls().makeService(service_options)
                        self.community.master_service.addService(service)
                        self._logger.info("module-community: module service (%s) added", service.name)

                        self.imported_modules.append(module.id)
