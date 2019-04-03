"""
This twistd plugin starts a TrustChain crawler.
"""
from __future__ import absolute_import

import logging
import os
import signal
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from twisted.application.service import MultiService, IServiceMaker
from twisted.internet import reactor
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.python.log import msg
from zope.interface import implements

from ipv8_service import IPv8
from ipv8.attestation.trustchain.settings import TrustChainSettings
from ipv8.peerdiscovery.discovery import RandomWalk
from ipv8.REST.rest_manager import RESTManager

from trust.community import TrustCommunity


class Options(usage.Options):
    optParameters = [
    ]
    optFlags = [
    ]


tc_settings = TrustChainSettings()
tc_settings.crawler = True
tc_settings.max_db_blocks = 1000000000

configuration = {
    'address': '0.0.0.0',
    'port': 8000,
    'keys': [
        {
            'alias': "my peer",
            'generation': u"medium",
            'file': u"ec.pem"
        }
    ],
    'logger': {
        'level': "ERROR"
    },
    'walker_interval': 0.5,
    'overlays': [
        {
            'class': 'DiscoveryCommunity',
            'key': "my peer",
            'walkers': [
                {
                    'strategy': "RandomWalk",
                    'peers': -1,
                    'init': {
                        'timeout': 3.0
                    }
                },
                {
                    'strategy': "RandomChurn",
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
        }, {
            'class': 'TrustChainTestnetCommunity',
            'key': "my peer",
            'walkers': [
                {
                    'strategy': "RandomWalk",
                    'peers': -1,
                    'init': {
                        'timeout': 3.0
                    }
                },
            ],
            'initialize': {
                'settings': tc_settings
            },
            'on_start': [],
        },
    ]
}


class TrustServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "trust"
    description = "trust"
    options = Options

    def __init__(self):
        """
        Initialize the variables of the trust and the logger.
        """
        self.ipv8 = None
        self.restapi = None
        self._stopping = False

    def start_trust(self, options):
        """
        Main method to startup the trust.
        """
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.INFO)
        stderr_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(message)s"))
        root.addHandler(stderr_handler)

        self.ipv8 = IPv8(configuration)

        # Peer
        my_peer = self.ipv8.keys.get('my peer')

        # trust community
        trust_community = TrustCommunity(my_peer, self.ipv8.endpoint, self.ipv8.network)
        self.ipv8.overlays.append(trust_community)
        self.ipv8.strategies.append((RandomWalk(trust_community), 10))

        def signal_handler(sig, _):
            msg("Received shut down signal %s" % sig)
            if not self._stopping:
                self._stopping = True
                self.restapi.stop()
                self.ipv8.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.restapi = RESTManager(self.ipv8)
        reactor.callLater(0.0, self.restapi.start, 8001)

    def makeService(self, options):
        """
        Construct a IPv8 service.
        """
        crawler_service = MultiService()
        crawler_service.setName("Trust")

        reactor.callWhenRunning(self.start_trust, options)

        return crawler_service


service_maker = TrustServiceMaker()
