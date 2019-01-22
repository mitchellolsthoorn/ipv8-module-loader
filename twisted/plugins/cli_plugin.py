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
from twisted.protocols.basic import LineReceiver
from twisted.python import usage
from twisted.python.log import msg

# Third party imports - Util
from zope.interface import implements

# Third party imports - IPv8
from pyipv8.ipv8.attestation.trustchain.community import TrustChainTestnetCommunity
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.peerdiscovery.discovery import EdgeWalk, RandomWalk
from pyipv8.ipv8_service import IPv8

# Project imports
from loader.community.dapp.community import DAppCommunity


# Not used anymore. Use export PYTHONPATH="${PYTHONPATH}:."
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class CLI(LineReceiver):
    delimiter = os.linesep

    header = "\
        .___  _____                         \n\
      __| _/ /  _  \  ______  ______  ______\n\
     / __ | /  /_\  \ \____ \ \____ \/  ___/\n\
    / /_/  /    |    \   |_> >   |_> >___ \ \n\
    \____  \____|__  /    __/ |   __/____  >\n\
         \/        \/ |__|    |__|       \/ \n"

    colors = {
        'blue': '\033[94m',
        'pink': '\033[95m',
        'green': '\033[92m',
    }

    def __init__(self, service, ipv8, dapp_community):
        self.service = service
        self.ipv8 = ipv8
        self.dapp_community = dapp_community

        self.menu_items = [
            {"Show dApps": self.show_dapps},
            {"Create dApp": self.create_dapp},
            {"Exit": self.exit},
        ]

    def _colorize(self, string, color):
        if color not in self.colors:
            return string

        return self.colors[color] + string + '\033[0m'

    def rawDataReceived(self, data):
        raise NotImplementedError

    def lineReceived(self, line):
        try:
            if len(self.menu_items) - 1 < int(line) < 0:
                raise ValueError

            # Call the matching function
            self.menu_items[int(line)].values()[0]()

            # Display wait message
            msg(self._colorize("Press [Enter] to continue...", 'green'))
        except (ValueError, IndexError):
            self.print_menu()

    def print_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))
        for item in self.menu_items:
            msg(self._colorize("[" + str(self.menu_items.index(item)) + "] ", 'blue') + item.keys()[0])

    def create_dapp(self):
        self.dapp_community.create_dapp()

    def show_dapps(self):
        dapps = self.dapp_community.get_dapps()

        # print(str(dapps))

        for dapp in dapps:
            msg(self._colorize("info_hash: " + dapp['info_hash'] + " name: " + dapp['name'], 'green'))

    def exit(self):
        self.service.stop()


class Options(usage.Options):
    optParameters = [
        ['port', 'p', 8090, "Use an alternative port for IPv8", int],
        ['statedir', 's', "./", "Use an alternate statedir", str],
    ]
    optFlags = [
        ['testnet', 't', "Join the testnet"],
        ['verbose', 'v', "Verbose output"]
    ]


class CLIServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "dapp"
    description = "dapp service"
    options = Options

    def __init__(self):
        """
        Initialize the variables of this service and the logger.
        """

        # Init service state
        self._stopping = False

        # Init variables
        self.ipv8 = None
        self.my_peer = None
        self.discovery_community = None
        self.trustchain_community = None
        self.dapp_community = None
        self.cli = None

        # Setup logging
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.INFO)
        stderr_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
        root.addHandler(stderr_handler)

    def start(self, options):
        """
        Main method to startup the cli and add a signal handler.
        """

        msg("Service: Starting")

        # Initial configuration
        configuration = get_default_configuration()
        configuration['address'] = "0.0.0.0"
        configuration['port'] = 8090
        state_directory = options['statedir']
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

        # IPv8 instance
        self.ipv8 = IPv8(configuration)

        # Peer
        self.my_peer = self.ipv8.keys.get('my peer')

        # Trustchain community
        self.trustchain_community = TrustChainTestnetCommunity(self.my_peer, self.ipv8.endpoint, self.ipv8.network,
                                                               working_directory=state_directory)
        self.ipv8.overlays.append(self.trustchain_community)
        self.ipv8.strategies.append((EdgeWalk(self.trustchain_community), 10))

        # dApp community
        self.dapp_community = DAppCommunity(self.my_peer, self.ipv8.endpoint, self.ipv8.network,
                                            trustchain=self.trustchain_community, working_directory=state_directory)
        self.ipv8.overlays.append(self.dapp_community)
        self.ipv8.strategies.append((RandomWalk(self.dapp_community), 10))

        # CLI
        self.cli = CLI(self, self.ipv8, self.dapp_community)
        self.cli.print_menu()

        def signal_handler(sig, _):
            msg("Service: Received shut down signal %s" % sig)
            if not self._stopping:
                self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

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

        reactor.callWhenRunning(self.start, options)

        return dapp_service


service_maker = CLIServiceMaker()
