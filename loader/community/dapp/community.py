from __future__ import absolute_import

# Default library imports
from binascii import unhexlify, hexlify
import logging
import os
import sys

# Third party imports
from ipv8.attestation.trustchain.block import TrustChainBlock
from ipv8.attestation.trustchain.community import TrustChainCommunity
from ipv8.attestation.trustchain.listener import BlockListener
from ipv8.community import Community
from ipv8.peer import Peer
from ipv8_service import IPv8
from twisted.application.service import MultiService
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

# Project imports
from loader import util
from loader.community.dapp.block import DAppBlock, DAPP_BLOCK_TYPE_VOTE, DAPP_BLOCK_TYPE_VOTE_KEY_CREATOR, \
    DAPP_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH, DAPP_BLOCK_TYPE_VOTE_KEY_NAME
from loader.community.dapp.core.dapp import DApp
from loader.community.dapp.core.dapp_identifier import DAppIdentifier
from loader.community.dapp.dapp_database import DAppDatabase
from loader.community.dapp.execution.engine import ExecutionEngine
from loader.community.dapp.transport.bittorrent import BittorrentTransport
from loader.event.bus import EventBus

# Constants
DAPP_DATABASE_NAME = "dapp"  # dApp database name
DAPP_CACHE_DIR = "cache"  # dApp cache directory
DAPP_LIBRARY_DIR = "library"  # dApp library directory
DAPP_PACKAGE_DIR = "package"  # dApp package directory
DAPP_TORRENT_DIR = "torrents"  # dApp torrent directory


class DAppCommunity(Community, BlockListener):
    """
    Overlay for the dApp network
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

    # Override block class with custom dApp block
    BLOCK_CLASS = DAppBlock

    def __init__(self, my_peer, endpoint, network, trustchain, bus, **kwargs):
        """
        Initialize dApp overlay

        :param my_peer: Node identity peer instance
        :type my_peer: Peer
        :param endpoint: IPv8 endpoint instance
        :type endpoint: Endpoint
        :param network: IPv8 network instance
        :type network: Network
        :param trustchain: TrustChain overlay
        :type trustchain: TrustChainCommunity
        :param kwargs:
        """
        super(DAppCommunity, self).__init__(my_peer, endpoint, network)
        super(BlockListener, self).__init__()

        self.trustchain = trustchain  # type: TrustChainCommunity
        self.bus = bus  # type: EventBus
        self.working_directory = kwargs.pop('working_directory', "./")  # type: str
        self.ipv8 = kwargs.pop('ipv8')  # type: IPv8
        self.master_service = kwargs.pop('service')  # type: MultiService

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

        # Block listeners
        self.trustchain.add_listener(self, [DAPP_BLOCK_TYPE_VOTE])

        # Database
        self.persistence = DAppDatabase(self.working_directory, DAPP_DATABASE_NAME)

        # Sub components
        self.transport = BittorrentTransport(self.working_directory)
        self.execution_engine = ExecutionEngine(self.working_directory, self)

        self.transport.start()

        self._setup_working_directory_structure()
        self._load_dapp_library_namespace()

        self.dapp_verify_task = self.register_task("dapp_verify", reactor.callLater(5, self._check_votes_in_catalog))
        self.dapp_crawl_task = self.register_task("dapp_crawl", LoopingCall(self._crawl_vote_blocks), delay=20,
                                                  interval=3600)

    # Util functions
    def _setup_working_directory_structure(self):
        """
        Setup working directory structure if it doesn't exist yet.

        :return: None
        """
        # dApp cache
        dapp_cache_directory = os.path.join(self.working_directory, DAPP_CACHE_DIR)
        util.create_directory_if_not_exists(dapp_cache_directory)

        # dApp library
        util.create_python_package_if_not_exists(self.working_directory, DAPP_LIBRARY_DIR)

        # dApp package
        dapp_package_directory = os.path.join(self.working_directory, DAPP_PACKAGE_DIR)
        util.create_directory_if_not_exists(dapp_package_directory)

        # torrents
        dapp_torrent_directory = os.path.join(self.working_directory, DAPP_TORRENT_DIR)
        util.create_directory_if_not_exists(dapp_torrent_directory)

    def _load_dapp_library_namespace(self):
        """
        Load the namespace for the dApp library

        :return: None
        """
        dapp_library_directory = os.path.join(self.working_directory, DAPP_LIBRARY_DIR)
        sys.path.append(os.path.abspath(dapp_library_directory))

    # Interface functions
    def create_dapp(self, name):
        """
        Create a dApp

        :return: None
        """
        dapp_package_directory = os.path.join(self.working_directory, DAPP_PACKAGE_DIR, name)

        if not os.path.isdir(dapp_package_directory):
            self._logger.info("dApp-community: dApp package (%s) does not exists", name)
            return

        package = self.transport.create_dapp_package(name)
        info_hash = str(package['info_hash'])
        name = str(package['name'])

        identifier = DAppIdentifier(self.my_peer.public_key.key_to_bin(), info_hash)
        dapp = DApp(identifier, name)

        self._logger.info("dApp-community: creating dApp (%s, %s)", dapp.id, dapp.name)

        if self.persistence.has_dapp_in_catalog(dapp.id):
            self._logger.info("dApp-community: dApp (%s) already exists, not creating new one", dapp.id)
            return

        self.persistence.add_dapp_to_catalog(dapp)
        self.vote_dapp(dapp.id)

    def create_dapp_test(self):
        """
        Create a test dApp

        :return: None
        """
        info_hash = "0000000000000000000000000000000000000000"
        name = "test"

        identifier = DAppIdentifier(self.my_peer.public_key.key_to_bin(), info_hash)
        dapp = DApp(identifier, name)

        self._logger.info("dApp-community: creating test dApp (%s, %s)", dapp.id, dapp.name)

        if self.persistence.has_dapp_in_catalog(dapp.id):
            self._logger.info("dApp-community: test dApp (%s) already exists, not creating new one", dapp.id)
            return

        self.persistence.add_dapp_to_catalog(dapp)
        self.vote_dapp(dapp.id)

    def download_dapp(self, dapp_identifier):
        """
        download a dApp

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: None
        """
        if self.persistence.has_dapp_in_cache(dapp_identifier):
            self._logger.info("dApp-community: dApp (%s) already downloaded, not downloading again", dapp_identifier)
            return

        self._logger.info("dApp-community: downloading dApp (%s)", dapp_identifier)

        if not self.persistence.has_dapp_in_catalog(dapp_identifier):
            self._logger.info("dApp-community: dApp (%s) not in catalog, not downloading", dapp_identifier)
            return

        dapp = self.persistence.get_dapp_from_catalog(dapp_identifier)

        if dapp:
            self.transport.download_dapp(dapp)
            self.persistence.add_dapp_to_cache(dapp.id)
            self.persistence.add_dapp_to_library(dapp.id)

    def get_dapp_from_catalog(self, dapp_identifier):
        """
        Get dApp with the provided info_hash from the catalog

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: The dApp requested or None if it doesn't exist
        """
        self._logger.info("dApp-community: Getting dApp (%s) from catalog", dapp_identifier)
        return self.persistence.get_dapp_from_catalog(dapp_identifier)

    def get_dapps_from_catalog(self):
        """
        Get all dApps from the catalog

        :return: All dApps
        """
        self._logger.debug("dApp-community: Getting all dApps from catalog")
        return self.persistence.get_dapps_from_catalog()

    def run_dapp(self, dapp_identifier):
        """
        Run the dApp with the provided info_hash

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: None
        """
        self._logger.info("dApp-community: running dApp (%s)", dapp_identifier)

        if not self.persistence.has_dapp_in_library(dapp_identifier):
            self._logger.info("dApp-community: dApp (%s) not in library, not running", dapp_identifier)
            return

        dapp = self.persistence.get_dapp_from_catalog(dapp_identifier)

        if dapp:
            self.execution_engine.run_dapp(dapp)

    def vote_dapp(self, dapp_identifier):
        """
        Vote on dApp with provided dApp id

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: None
        """
        if not self.persistence.has_dapp_in_catalog(dapp_identifier):
            self._logger.info("dApp-community: dApp (%s) not in catalog, not voting", dapp_identifier)
            return

        if self.persistence.did_vote(self.my_peer.public_key.key_to_bin(), dapp_identifier):
            self._logger.info("dApp-community: Already voted on dApp (%s), not voting", dapp_identifier)
            return

        dapp = self.persistence.get_dapp_from_catalog(dapp_identifier)

        if dapp:
            # Add vote to catalog and votes
            self.persistence.add_vote_to_votes(self.my_peer.public_key.key_to_bin(), dapp.id)
            self.persistence.add_vote_to_dapp_in_catalog(dapp.id)

            self._logger.info("dApp-community: Vote for dApp (%s, %s)", dapp.id, dapp.name)
            self._sign_dapp(dapp)

    # Internal logic functions
    def should_sign(self, block):
        """
        Function to determine if a block sign request should be signed

        :param block: The block to be signed
        :type block: DAppBlock
        :return: True if the block should be signed, otherwise False
        """
        self._logger.debug("dApp-community: Received sign request for block (%s)", block.block_id)

        # Vote block
        if block.type == DAPP_BLOCK_TYPE_VOTE:
            return True

        return False

    def received_block(self, block):
        """
        Callback function for processing received blocks

        :param block: The block to be processed
        :type block: DAppBlock
        :return: None
        """
        self._logger.debug("dApp-community: Received block (%s)", block.block_id)

        # Vote block
        if block.type == DAPP_BLOCK_TYPE_VOTE:
            self._process_vote_block(block)

    def _process_vote_block(self, block):
        """
        Internal function for processing vote blocks

        :param block: The block to be processed
        :type block: DAppBlock
        :return: None
        """
        block_id = block.block_id

        self._logger.debug("dApp-community: Received vote block (%s)", block_id)

        if not block.is_valid_vote_block:
            self._logger.debug("dApp-community: Invalid vote block (%s) received!", block_id)
            return

        public_key = block.public_key  # type: bytes
        tx_dict = block.transaction  # type: dict
        creator = tx_dict[DAPP_BLOCK_TYPE_VOTE_KEY_CREATOR]  # type: bytes
        content_hash = tx_dict[DAPP_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH]  # type: str
        name = tx_dict[DAPP_BLOCK_TYPE_VOTE_KEY_NAME]  # type: str

        identifier = DAppIdentifier(creator, content_hash)

        # Add dApp to catalog if it isn't known yet
        if not self.persistence.has_dapp_in_catalog(identifier):
            self._logger.info("dApp-community: Adding unknown dApp to catalog (%s, %s)", identifier, name)

            dapp = DApp(identifier, name)
            self.persistence.add_dapp_to_catalog(dapp)

        # Add vote to catalog and votes if it isn't known yet
        if not self.persistence.did_vote(public_key, identifier):
            self._logger.info("dApp-community: Received vote (%s, %s)", identifier, name)
            self.persistence.add_vote_to_votes(public_key, identifier)
            self.persistence.add_vote_to_dapp_in_catalog(identifier)

    def _sign_dapp(self, dapp):
        """
        Internal function for signing a dApp

        :param dapp: dApp
        :type dapp: DApp
        :return: None
        """
        self._logger.debug("dApp-community: Signing dApp (%s, %s)", dapp.id, dapp.name)

        tx_dict = {
            DAPP_BLOCK_TYPE_VOTE_KEY_CREATOR: dapp.id.creator,
            DAPP_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH: dapp.id.content_hash,
            DAPP_BLOCK_TYPE_VOTE_KEY_NAME: dapp.name,
        }

        self.trustchain.self_sign_block(block_type=DAPP_BLOCK_TYPE_VOTE, transaction=tx_dict)

        self._logger.debug("dApp-community: Signed dApp (%s, %s)", dapp.id, dapp.name)

    def _crawl_vote_blocks(self):
        """
        Crawl network peers for unknown dApps

        :return: None
        """
        self._logger.info("dApp-community: Crawl network peers for unknown dApps")

        for peer in self.get_peers():
            self.trustchain.crawl_chain(peer)

    def _check_votes_in_catalog(self):
        """
        Check if the votes in the catalog match the votes in trustchain

        :return: None
        """
        self._logger.info("dApp-community: Checking votes in catalog")

        blocks = self.trustchain.persistence.get_blocks_with_type(DAPP_BLOCK_TYPE_VOTE)  # type: [TrustChainBlock]

        votes = {}
        voters = {}

        for block in blocks:
            public_key = block.public_key  # type: bytes
            tx_dict = block.transaction  # type: dict
            creator = tx_dict[DAPP_BLOCK_TYPE_VOTE_KEY_CREATOR]  # type: bytes
            content_hash = tx_dict[DAPP_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH]  # type: str
            name = tx_dict[DAPP_BLOCK_TYPE_VOTE_KEY_NAME]  # type: str

            identifier = DAppIdentifier(creator, content_hash)

            # Check votes database
            if not self.persistence.did_vote(public_key, identifier):
                self.persistence.add_vote_to_votes(public_key, identifier)

            # Check number of votes
            if identifier in votes:
                votes[identifier] = votes[identifier] + 1
            else:
                votes[identifier] = 1

            # Check double votes
            public_key_hex = hexlify(public_key)
            if public_key_hex not in voters:
                voters[public_key_hex] = {}

            voted_dapps = voters[public_key_hex]
            if identifier not in voted_dapps:
                voted_dapps[identifier] = 1
                voters[public_key_hex] = voted_dapps
            else:
                self._logger.info("dApp-community: Double vote for dApp (%s) by peer (%s)", identifier, public_key_hex)

        dapps = self.persistence.get_dapps_from_catalog()

        # Compare and fix vote inconsistencies
        for dapp in dapps:
            identifier = dapp.id
            votes_in_catalog = dapp.votes

            if identifier in votes and votes[identifier] != votes_in_catalog:
                self._logger.info("dApp-community: Vote inconsistency for dApp (%s)", identifier)
                self.persistence.update_dapp_in_catalog(identifier, votes[identifier])

            votes.pop(identifier)

        if len(votes) != 0:
            self._logger.info("dApp-community: inconsistent vote db")

        self._logger.info("dApp-community: Checking votes in catalog is done")

    def unload(self):
        """
        Unload the community

        :return: None
        """
        super(DAppCommunity, self).unload()

        # Close the persistence layer
        self.persistence.close()

        # Stop transport
        self.transport.stop()
