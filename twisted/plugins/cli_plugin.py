"""
twistd plugin enables to start a cli using the twistd command.
"""

from __future__ import absolute_import

# Default library imports
import logging
import os
import signal
import sys

from ipv8.REST.rest_manager import RESTManager

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
from ipv8.attestation.trustchain.community import TrustChainTestnetCommunity
from ipv8.configuration import get_default_configuration
from ipv8.peerdiscovery.discovery import EdgeWalk, RandomWalk
from ipv8_service import IPv8

# Project imports
from loader import util
from loader.community.dapp.community import DAppCommunity


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

    MENU_MAIN = 0
    MENU_DAPP_LIST = 1
    MENU_DAPP = 2

    def __init__(self, service, ipv8, dapp_community):
        self.service = service
        self.ipv8 = ipv8
        self.dapp_community = dapp_community

        self.menu_level = self.MENU_MAIN
        self.current_option = None
        self.context = {}

        self.main_menu_items = [
            {"Create test dApp": self.create_test_dapp},
            {"Create dApp": self.create_dapp_setup},
            {"Show dApps": self.show_dapps},
            {"Exit": self.exit},
        ]

        self.dapp_menu_items = [
            {"Download dApp": self.download_dapp},
            {"Run dApp": self.run_dapp},
            {"Vote dApp": self.vote_dapp},
        ]

        self.print_main_menu()

    def _colorize(self, string, color):
        if color not in self.colors:
            return string

        return self.colors[color] + string + '\033[0m'

    def rawDataReceived(self, data):
        raise NotImplementedError

    def lineReceived(self, line):
        if self.current_option is None:
            if self.menu_level == self.MENU_MAIN:
                try:
                    if len(self.main_menu_items) - 1 < int(line) < 0:
                        raise ValueError

                    # Call the matching function
                    self.main_menu_items[int(line)].values()[0](line)
                except (ValueError, IndexError):
                    self.print_main_menu()
            elif self.menu_level == self.MENU_DAPP_LIST:
                try:
                    dapps = self.dapp_community.get_dapps_from_catalog()
                    if len(dapps) - 1 < int(line) < -1:
                        raise ValueError

                    if int(line) == -1:
                        self.menu_level = self.MENU_MAIN
                        self.current_option = None
                        self.context = {}
                        self.print_main_menu()
                        return

                    self.show_dapp(int(line))
                except (ValueError, IndexError):
                    self.print_dapp_list_menu()
            elif self.menu_level == self.MENU_DAPP:
                try:
                    if len(self.dapp_menu_items) - 1 < int(line) < -1:
                        raise ValueError

                    if int(line) == -1:
                        self.menu_level = self.MENU_DAPP_LIST
                        self.current_option = None
                        self.context = {}
                        self.print_dapp_list_menu()
                        return

                    # Call the matching function
                    self.dapp_menu_items[int(line)].values()[0](line)
                except (ValueError, IndexError):
                    self.print_dapp_menu()
            else:
                self.reset()
        else:
            self.current_option(line)

    def print_main_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))
        for item in self.main_menu_items:
            msg(self._colorize("[" + str(self.main_menu_items.index(item)) + "] ", 'blue') + item.keys()[0])

    def print_dapp_list_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))

        dapps = self.dapp_community.get_dapps_from_catalog()

        msg(self._colorize(str(len(dapps)) + " dApps found:", 'blue'))

        msg(self._colorize("[-1] ", 'blue') + self._colorize("Return to previous menu", 'green'))

        for dapp in dapps:
            msg(
                self._colorize("[" + str(dapps.index(dapp)) + "] ", 'blue') +
                self._colorize(
                    "info_hash: " + dapp['info_hash'] + " " +
                    "name: " + dapp['name'] + " " +
                    "votes: " + dapp['votes']
                    , 'green'))

    def print_dapp_menu(self):
        os.system('clear')
        msg(self._colorize('\n' + self.header, 'pink'))
        msg(self._colorize('version 0.1', 'green'))

        dapp = self.dapp_community.get_dapp_from_catalog(self.context['info_hash'])

        msg(self._colorize("Info Hash: " + str(dapp['info_hash']), 'green'))
        msg(self._colorize("Name: " + str(dapp['name']), 'green'))
        msg(self._colorize("Votes: " + str(dapp['votes']), 'green'))

        msg(self._colorize("[-1] ", 'blue') + self._colorize("Return to previous menu", 'green'))

        for item in self.dapp_menu_items:
            msg(self._colorize("[" + str(self.dapp_menu_items.index(item)) + "] ", 'blue') + item.keys()[0])

    def reset(self):
        self.menu_level = self.MENU_MAIN
        self.current_option = self.OPTION_NONE
        self.context = {}
        self.print_main_menu()

    def create_test_dapp(self, line):
        self.dapp_community.create_dapp_test()

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def create_dapp_setup(self, line):
        self.current_option = self.create_dapp
        msg(self._colorize("Press enter dApp package name", 'green'))

    def create_dapp(self, line):
        msg(self._colorize("dApp name: " + line, 'blue'))
        self.dapp_community.create_dapp(line)

        self.current_option = None
        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def show_dapps(self, line):
        self.menu_level = self.MENU_DAPP_LIST
        self.print_dapp_list_menu()

    def show_dapp(self, line):
        dapps = self.dapp_community.get_dapps_from_catalog()
        index = int(line)

        msg("Number of dapps retrieved: " + str(len(dapps)))

        self.menu_level = self.MENU_DAPP
        self.context = dapps[int(line)]
        self.print_dapp_menu()

    def download_dapp(self, line):
        self.dapp_community.download_dapp(self.context['info_hash'])

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def run_dapp(self, line):
        self.dapp_community.run_dapp(self.context['info_hash'])

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def vote_dapp(self, line):
        self.dapp_community.vote_dapp(self.context['info_hash'])

        # Display wait message
        msg(self._colorize("Press [Enter] to continue...", 'green'))

    def exit(self, line):
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
        self.rest_api = None

        # Setup logging
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.DEBUG)
        stderr_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
        root.addHandler(stderr_handler)

    def start(self, options):
        """
        Main method to startup the cli and add a signal handler.
        """

        msg("Service: Starting")

        # State directory
        state_directory = options['statedir']
        util.create_directory_if_not_exists(state_directory)

        # Initial configuration
        configuration = get_default_configuration()
        configuration['address'] = "0.0.0.0"
        configuration['port'] = 8090
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

        def signal_handler(sig, _):
            msg("Service: Received shut down signal %s" % sig)
            if not self._stopping:
                self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.rest_api = RESTManager(self.ipv8)
        reactor.callLater(5, self.rest_api.start, )

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
