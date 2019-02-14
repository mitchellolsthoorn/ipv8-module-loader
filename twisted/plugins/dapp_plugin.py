"""
twistd plugin enables to start a cli using the twistd command.
"""

from __future__ import absolute_import

# Default library imports
import logging
import os
import signal
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Third party imports - Twisted
from twisted.application.service import MultiService, IServiceMaker
from twisted.internet import reactor
from twisted.internet.stdio import StandardIO
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.python.log import msg

# Third party imports - Util
from zope.interface import implements

# Third party imports - IPv8
from ipv8.attestation.trustchain.community import TrustChainTestnetCommunity
from ipv8.configuration import get_default_configuration
from ipv8.peerdiscovery.discovery import EdgeWalk, RandomWalk
from ipv8.REST.rest_manager import RESTManager
from ipv8_service import IPv8

# Project imports
from loader import util
from CLI.CLI import CLI
from loader.community.dapp.community import DAppCommunity
from loader.REST.root_endpoint import DAppRootEndpoint


class Options(usage.Options):
    optParameters = [
        ['port', 'p', 8090, "Use an alternative port for IPv8", int],
        ['statedir', 's', "./data", "Use an alternate statedir", str],
    ]
    optFlags = [
        ['testnet', 't', "Join the testnet"],
        ['verbose', 'v', "Verbose output"]
    ]


class DAppServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "dapp"
    description = "dSpp service"
    options = Options

    def __init__(self):
        """
        Initialize the variables of this service and the logger.
        """

        # Init service state
        self._stopping = False

        # Init variables
        self.service = None
        self.ipv8 = None
        self.my_peer = None
        self.discovery_community = None
        self.trustchain_community = None
        self.dapp_community = None
        self.cli = None
        self.rest_api = None

        # Setup logging
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.INFO)
        stderr_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
        root.addHandler(stderr_handler)

    def start(self, options, service):
        """
        Main method to startup the cli and add a signal handler.
        """

        msg("Service: Starting")

        self.service = service

        # State directory
        state_directory = options['statedir']
        util.create_directory_if_not_exists(state_directory)

        # port
        network_port = options['port']

        # Initial configuration
        configuration = get_default_configuration()
        configuration['address'] = "0.0.0.0"
        configuration['port'] = network_port
        configuration['keys'] = [{
            'alias': 'my peer',
            'generation': u"curve25519",
            'file': os.path.join(state_directory, u"ec.pem")
        }]
        configuration['logger'] = {'level': "ERROR"}
        configuration['overlays'] = [{
            'class': 'DiscoveryCommunity',
            'key': "my peer",
            'walkers': [
                {
                    'strategy': 'RandomWalk',
                    'peers': -1,
                    'init': {
                        'timeout': 3.0
                    }
                },
                {
                    'strategy': 'RandomChurn',
                    'peers': -1,
                    'init': {
                        'sample_size': 64,
                        'ping_interval': 1.0,
                        'inactive_time': 1.0,
                        'drop_time': 3.0
                    }
                }
            ],
            'initialize': {},
            'on_start': [
                ('resolve_dns_bootstrap_addresses',)
            ]
        }]
        configuration['overlays'] = []

        # IPv8 instance
        self.ipv8 = IPv8(configuration)

        # Network port
        actual_network_port = self.ipv8.endpoint.get_address()[1]

        # Peer
        self.my_peer = self.ipv8.keys.get('my peer')

        # Trustchain community
        self.trustchain_community = TrustChainTestnetCommunity(self.my_peer, self.ipv8.endpoint, self.ipv8.network,
                                                               working_directory=state_directory)
        self.ipv8.overlays.append(self.trustchain_community)
        self.ipv8.strategies.append((EdgeWalk(self.trustchain_community), 10))

        # dApp community
        self.dapp_community = DAppCommunity(self.my_peer, self.ipv8.endpoint, self.ipv8.network,
                                            trustchain=self.trustchain_community, working_directory=state_directory,
                                            ipv8=self.ipv8, service=self.service)
        self.ipv8.overlays.append(self.dapp_community)
        self.ipv8.strategies.append((RandomWalk(self.dapp_community), 10))

        # CLI
        self.cli = CLI(self, self.ipv8, self.dapp_community)

        def signal_handler(sig, _):
            msg("Service: Received shut down signal %s" % sig)
            if not self._stopping:
                self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.rest_api = RESTManager(self.ipv8)
        self.rest_api.start(actual_network_port + 1000)
        self.rest_api.root_endpoint.putChild('dapp', DAppRootEndpoint(self.ipv8))

        StandardIO(self.cli)

    def stop(self):
        self._stopping = True
        self.ipv8.stop()
        reactor.stop()

    def makeService(self, options):
        """
        Construct a IPv8 service.
        """

        dapp_service = MultiService()
        dapp_service.setName("dapp")

        reactor.callWhenRunning(self.start, options, dapp_service)

        return dapp_service


service_maker = DAppServiceMaker()