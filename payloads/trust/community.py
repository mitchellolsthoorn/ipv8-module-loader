from __future__ import absolute_import

# Default library imports
from binascii import unhexlify
import logging

# Third party imports
from ipv8.attestation.trustchain.listener import BlockListener
from ipv8.community import Community
from ipv8.peer import Peer


class TrustCommunity(Community, BlockListener):
    # Register this community with a master peer.
    # This peer defines the service identifier of this community.
    # Other peers will connect to this community based on the sha-1
    # hash of this peer's public key.
    master_peer = Peer(unhexlify("3ba6"))

    def __init__(self, my_peer, endpoint, network):
        super(TrustCommunity, self).__init__(my_peer, endpoint, network)
        super(BlockListener, self).__init__()

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

    def should_sign(self, block):
        return False

    def received_block(self, block):
        pass

    def unload(self):
        super(TrustCommunity, self).unload()
