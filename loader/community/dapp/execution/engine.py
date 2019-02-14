import importlib
import json
import logging
import os

from ipv8_service import _COMMUNITIES, _WALKERS
from twisted.internet import reactor

from loader.community.dapp.transport.bittorrent import DAPPS_DIR, EXECUTE_FILE


class ExecutionEngine(object):
    """
    Execution engine for dApps
    """

    def __init__(self, working_directory, community):
        super(ExecutionEngine, self).__init__()

        self.working_directory = working_directory
        self.community = community

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

        # State
        self.imported_dapps = []

    def run_dapp(self, dapp):
        name = dapp.name
        dapps_directory = os.path.join(os.path.abspath(self.working_directory), DAPPS_DIR)
        dapp_path = os.path.join(dapps_directory, name)
        dapp_executable = os.path.join(dapp_path, EXECUTE_FILE)

        if os.path.isdir(dapp_path) and os.path.isfile(os.path.join(dapp_path, 'package.json')):
            self._logger.info("dApp-community: dApp (%s) found", name)

            with open(os.path.join(dapp_path, 'package.json')) as f:
                data = json.load(f)

                package_type = data['type']
                if package_type == "executable":
                    self._logger.info("dApp-community: executable dApp (%s) found", name)
                    executable_file = data['executable_file']

                    if dapp.id not in self.imported_dapps:
                        importlib.import_module(name + "." + executable_file)
                        self.imported_dapps.append(dapp.id)

                elif package_type == "overlay":
                    self._logger.info("dApp-community: dApp overlay (%s) found", name)

                    overlay_file = data['overlay_file']

                    if dapp.id not in self.imported_dapps:
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
                            self._logger.info("dApp-community: dApp overlay (%s) added", overlay['class'])

                        self.imported_dapps.append(dapp.id)

                elif package_type == "service":
                    self._logger.info("dApp-community: dApp service (%s) found", name)
                    service_file = data['service_file']
                    service_class = data['service_class']
                    service_options = data['service_options']

                    if dapp.id not in self.imported_dapps:
                        cls = getattr(importlib.import_module(name + "." + service_file), service_class)
                        service = cls().makeService(service_options)
                        self.community.master_service.addService(service)
                        self._logger.info("dApp-community: dApp service (%s) added", service.name)

                        self.imported_dapps.append(dapp.id)
