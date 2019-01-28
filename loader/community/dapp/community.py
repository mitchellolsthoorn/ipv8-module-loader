"""
"""

from __future__ import absolute_import

# Default library imports
from binascii import unhexlify
import logging
import os
import sys

# Third party imports
from ipv8.attestation.trustchain.listener import BlockListener
from ipv8.community import Community
from ipv8.peer import Peer

# Project imports
from loader import util
from loader.community.dapp.block import DAppBlock, DAPP_BLOCK_TYPE_VOTE
from loader.community.dapp.dapp_database import DAppDatabase

# Constants
DAPP_DATABASE_NAME = "dapp"
DAPP_LIBRARY_DIR = "library"


class DAppCommunity(Community, BlockListener):
    """

    """

    # Register this community with a master peer.
    # This peer defines the service identifier of this community.
    # Other peers will connect to this community based on the sha-1
    # hash of this peer's public key.
    master_peer = Peer(unhexlify("3081a7301006072a8648ce3d020106052b810400270381920004030d4d2d1fc98e2e3a7b0127acffbbc1a"
                                 "ade720955b6a3c8b4de1a25686f20b6e150591f1251252c4cd30bfaa8ca5f1d2c68327cbef939958c94d1"
                                 "a441c20b10acd9c53e5c9023a6011d626e69290a4ef98c2588ab1eb2ca9a3fb6f08042e1c93c9bad60bbb"
                                 "0f33fc156924e3914be9bd11d702fe1ab307c40634e97d476462d669ebc4a39c5dd10eb58ab2d8a86c690"
                                 ))

    #
    BLOCK_CLASS = DAppBlock

    def __init__(self, my_peer, endpoint, network, trustchain, **kwargs):
        super(DAppCommunity, self).__init__(my_peer, endpoint, network)
        super(BlockListener, self).__init__()
        self.trustchain = trustchain
        self.working_directory = kwargs.pop('working_directory', "")

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

        # Block listeners
        self.trustchain.add_listener(self, [DAPP_BLOCK_TYPE_VOTE])

        # Database
        self.persistence = DAppDatabase(self.working_directory, DAPP_DATABASE_NAME)

        self.transport = None
        self.discovery_strategy = None
        self.download_strategy = None
        self.seed_strategy = None
        self.execution_engine = None

        self._setup_working_directory_structure()
        self._load_dapp_library_namespace()

    # Util functions
    def _setup_working_directory_structure(self):
        # dApp library
        dapp_library_directory = os.path.join(self.working_directory, DAPP_LIBRARY_DIR)
        util.create_directory_if_not_exists(dapp_library_directory)

    def _load_dapp_library_namespace(self):
        dapp_library_directory = os.path.join(self.working_directory, DAPP_LIBRARY_DIR)
        sys.path.append(os.path.abspath(dapp_library_directory))

    # Interface functions
    def create_dapp(self):
        self._logger.info("community: creating a dApp")

        info_hash = "9626a56c551c916f5cea40c786b5dc02faf65917"
        name = "execute"
        if self.persistence.has_dapp_in_catalog(info_hash):
            self._logger.info("community: dApp already exists, not creating new one")
            return

        dapp = {
            'info_hash': info_hash,
            'name': name,
            'votes': 1,
        }

        self.persistence.add_dapp_to_catalog(dapp)
        self.vote_dapp(info_hash)

    def download_dapp(self, info_hash):
        """
        Manually download a dapp
        :param info_hash:
        :return:
        """
        dapp = {
            'info_hash': info_hash,
            'name': "Unknown",
            'votes': 0,
        }

        self.persistence.add_dapp_to_catalog(dapp)

    def get_dapp_from_catalog(self, info_hash):
        self._logger.info("community: Getting dApp from catalog")

        return self.persistence.get_dapp_from_catalog(info_hash)

    def get_dapps_from_catalog(self):
        self._logger.info("community: Getting dApps from catalog")

        return self.persistence.get_dapps_from_catalog()

    def run_dapp(self, info_hash):
        pass

    def vote_dapp(self, info_hash):
        self._logger.info("community: Vote for dapp")

        if not self.persistence.has_dapp_in_catalog(info_hash):
            self._logger.info("community: dApp not in catalog, not voting")
            return

        if self._did_vote_on_dapp(self.my_peer.public_key.key_to_bin(), info_hash):
            self._logger.info("community: Already voted on this dapp, not voting")
            return

        dapp = self.persistence.get_dapp_from_catalog(info_hash)

        if dapp:
            self._sign_dapp(dapp)

    # Helper functions
    def _did_vote_on_dapp(self, public_key, info_hash):
        self._logger.info("community: Check if we already voted on this dApp")

        votes_block = self.trustchain.persistence.get_blocks_with_type(block_type=DAPP_BLOCK_TYPE_VOTE,
                                                                       public_key=public_key)

        for vote_block in votes_block:
            if vote_block.transaction['info_hash'] == info_hash:
                self._logger.info("community: We already voted on this dApp")
                return True

        self._logger.info("community: We haven't voted on this dApp yet")
        return False

    # Internal logic functions
    def should_sign(self, block):
        # Vote block
        if block.type == DAPP_BLOCK_TYPE_VOTE:
            return True

        return False

    def received_block(self, block):
        self._logger.info("community: Received block")

        # Vote block
        if block.type == DAPP_BLOCK_TYPE_VOTE:
            self._process_vote_block(block)

    def _process_vote_block(self, block):
        if not block.is_valid_vote_block:
            self._logger.info("community: Invalid vote block received!")
            return

        if not self.persistence.has_dapp_in_catalog(block.transaction['info_hash']):
            self.persistence.add_dapp_to_catalog(block.transaction)

        tx_dict = block.transaction
        info_hash = tx_dict['info_hash']
        name = tx_dict['name']

        self._logger.info("Vote received for dapp with info_hash {0} and name {1}!".format(info_hash, name))

    def _sign_dapp(self, dapp):
        self._logger.info("community: Signing dApp")

        tx_dict = dapp

        info_hash = dapp['info_hash']
        name = dapp['name']

        self.trustchain.self_sign_block(block_type=DAPP_BLOCK_TYPE_VOTE, transaction=tx_dict)

        self._logger.info("Voted for dapp with info_hash {0} and name {1}!".format(info_hash, name))

    def unload(self):
        super(DAppCommunity, self).unload()

        # Close the persistence layer
        self.persistence.close()
