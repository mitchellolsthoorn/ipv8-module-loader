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
from module_loader import util
from module_loader.community.module.block import ModuleBlock, MODULE_BLOCK_TYPE_VOTE, MODULE_BLOCK_TYPE_VOTE_KEY_CREATOR, \
    MODULE_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH, MODULE_BLOCK_TYPE_VOTE_KEY_NAME
from module_loader.community.module.core.module import Module
from module_loader.community.module.core.module_identifier import ModuleIdentifier
from module_loader.community.module.module_database import ModuleDatabase
from module_loader.community.module.execution.engine import ExecutionEngine
from module_loader.community.module.transport.bittorrent import BittorrentTransport
from module_loader.event.bus import EventBus

# Constants
MODULE_DATABASE_NAME = "module"  # module database name
MODULE_CACHE_DIR = "cache"  # module cache directory
MODULE_LIBRARY_DIR = "package"  # module library directory
MODULE_PACKAGE_DIR = "package"  # module package directory
MODULE_TORRENT_DIR = "torrents"  # module torrent directory


class ModuleCommunity(Community, BlockListener):
    """
    Overlay for the module network. Handles all communication and actions related to managing and maintaining the module
    components.
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

    # Override block class with custom module block
    BLOCK_CLASS = ModuleBlock

    def __init__(self, my_peer, endpoint, network, trustchain, bus, **kwargs):
        """
        Initialize module overlay

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
        super(ModuleCommunity, self).__init__(my_peer, endpoint, network)
        super(BlockListener, self).__init__()

        self.trustchain = trustchain  # type: TrustChainCommunity
        self.bus = bus  # type: EventBus
        self.working_directory = kwargs.pop('working_directory', "./")  # type: str
        self.ipv8 = kwargs.pop('ipv8')  # type: IPv8
        self.master_service = kwargs.pop('service')  # type: MultiService

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

        # Block listeners
        self.trustchain.add_listener(self, [MODULE_BLOCK_TYPE_VOTE])

        # Database
        self.persistence = ModuleDatabase(self.working_directory, MODULE_DATABASE_NAME)

        # Sub components
        self.transport = BittorrentTransport(self.working_directory)
        self.execution_engine = ExecutionEngine(self.working_directory, self)

        self.transport.start()

        # Setup directory structure
        self._setup_working_directory_structure()

        # Load namespaces into path for live module loading
        self._load_module_library_namespace()

        # Task for verifying votes in the network
        self.module_verify_task = self.register_task("module_verify", reactor.callLater(5, self._check_votes_in_catalog))

        # Task for crawling neighbours for undiscovered modules
        self.module_crawl_task = self.register_task("module_crawl", LoopingCall(self._crawl_vote_blocks), delay=20,
                                                  interval=3600)

    # Util functions
    def _setup_working_directory_structure(self):
        """
        Setup working directory structure if it doesn't exist yet.

        :return: None
        """
        # module cache
        module_cache_directory = os.path.join(self.working_directory, MODULE_CACHE_DIR)
        util.create_directory_if_not_exists(module_cache_directory)

        # module library
        util.create_python_package_if_not_exists(self.working_directory, MODULE_LIBRARY_DIR)

        # module package
        module_package_directory = os.path.join(self.working_directory, MODULE_PACKAGE_DIR)
        util.create_directory_if_not_exists(module_package_directory)

        # torrents
        module_torrent_directory = os.path.join(self.working_directory, MODULE_TORRENT_DIR)
        util.create_directory_if_not_exists(module_torrent_directory)

    def _load_module_library_namespace(self):
        """
        Load the namespace for the module library

        :return: None
        """
        module_library_directory = os.path.join(self.working_directory, MODULE_LIBRARY_DIR)
        sys.path.append(os.path.abspath(module_library_directory))

    # Interface functions
    def create_module(self, name):
        """
        Create a module

        :return: None
        """
        module_package_directory = os.path.join(self.working_directory, MODULE_PACKAGE_DIR, name)

        print module_package_directory

        if not os.path.isdir(module_package_directory):
            self._logger.info("module-community: module package (%s) does not exists", name)
            return

        package = self.transport.create_module_package(name)
        info_hash = str(package['info_hash'])
        name = str(package['name'])

        identifier = ModuleIdentifier(self.my_peer.public_key.key_to_bin(), info_hash)
        module = Module(identifier, name)

        self._logger.info("module-community: creating module (%s, %s)", module.id, module.name)

        if self.persistence.has_module_in_catalog(module.id):
            self._logger.info("module-community: module (%s) already exists, not creating new one", module.id)
            return

        self.persistence.add_module_to_catalog(module)
        self.vote_module(module.id)

    def create_module_test(self):
        """
        Create a test module

        :return: None
        """
        info_hash = "0000000000000000000000000000000000000000"
        name = "test"

        identifier = ModuleIdentifier(self.my_peer.public_key.key_to_bin(), info_hash)
        module = Module(identifier, name)

        self._logger.info("module-community: creating test module (%s, %s)", module.id, module.name)

        if self.persistence.has_module_in_catalog(module.id):
            self._logger.info("module-community: test module (%s) already exists, not creating new one", module.id)
            return

        self.persistence.add_module_to_catalog(module)
        self.vote_module(module.id)

    def download_module(self, module_identifier):
        """
        download a module

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: None
        """
        if self.persistence.has_module_in_cache(module_identifier):
            self._logger.info("module-community: module (%s) already downloaded, not downloading again", module_identifier)
            return

        self._logger.info("module-community: downloading module (%s)", module_identifier)

        if not self.persistence.has_module_in_catalog(module_identifier):
            self._logger.info("module-community: module (%s) not in catalog, not downloading", module_identifier)
            return

        module = self.persistence.get_module_from_catalog(module_identifier)

        if module:
            self.transport.download_module(module)
            self.persistence.add_module_to_cache(module.id)
            self.persistence.add_module_to_library(module.id)

    def get_module_from_catalog(self, module_identifier):
        """
        Get module with the provided info_hash from the catalog

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: The module requested or None if it doesn't exist
        """
        self._logger.info("module-community: Getting module (%s) from catalog", module_identifier)
        return self.persistence.get_module_from_catalog(module_identifier)

    def get_modules_from_catalog(self):
        """
        Get all modules from the catalog

        :return: All modules
        """
        self._logger.debug("module-community: Getting all modules from catalog")
        return self.persistence.get_modules_from_catalog()

    def run_module(self, module_identifier):
        """
        Run the module with the provided info_hash

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: None
        """
        self._logger.info("module-community: running module (%s)", module_identifier)

        if not self.persistence.has_module_in_library(module_identifier):
            self._logger.info("module-community: module (%s) not in library, not running", module_identifier)
            return

        module = self.persistence.get_module_from_catalog(module_identifier)

        if module:
            self.execution_engine.run_module(module)

    def vote_module(self, module_identifier):
        """
        Vote on module with provided module id

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: None
        """
        if not self.persistence.has_module_in_catalog(module_identifier):
            self._logger.info("module-community: module (%s) not in catalog, not voting", module_identifier)
            return

        if self.persistence.did_vote(self.my_peer.public_key.key_to_bin(), module_identifier):
            self._logger.info("module-community: Already voted on module (%s), not voting", module_identifier)
            return

        module = self.persistence.get_module_from_catalog(module_identifier)

        if module:
            # Add vote to catalog and votes
            self.persistence.add_vote_to_votes(self.my_peer.public_key.key_to_bin(), module.id)
            self.persistence.add_vote_to_module_in_catalog(module.id)

            self._logger.info("module-community: Vote for module (%s, %s)", module.id, module.name)
            self._sign_module(module)

    # Internal logic functions
    def should_sign(self, block):
        """
        Function to determine if a block sign request should be signed

        :param block: The block to be signed
        :type block: ModuleBlock
        :return: True if the block should be signed, otherwise False
        """
        self._logger.debug("module-community: Received sign request for block (%s)", block.block_id)

        # Vote block
        if block.type == MODULE_BLOCK_TYPE_VOTE:
            return True

        return False

    def received_block(self, block):
        """
        Callback function for processing received blocks

        :param block: The block to be processed
        :type block: ModuleBlock
        :return: None
        """
        self._logger.debug("module-community: Received block (%s)", block.block_id)

        # Vote block
        if block.type == MODULE_BLOCK_TYPE_VOTE:
            self._process_vote_block(block)

    def _process_vote_block(self, block):
        """
        Internal function for processing vote blocks

        :param block: The block to be processed
        :type block: ModuleBlock
        :return: None
        """
        block_id = block.block_id

        self._logger.debug("module-community: Received vote block (%s)", block_id)

        if not block.is_valid_vote_block:
            self._logger.debug("module-community: Invalid vote block (%s) received!", block_id)
            return

        public_key = block.public_key  # type: bytes
        tx_dict = block.transaction  # type: dict
        creator = tx_dict[MODULE_BLOCK_TYPE_VOTE_KEY_CREATOR]  # type: bytes
        content_hash = tx_dict[MODULE_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH]  # type: str
        name = tx_dict[MODULE_BLOCK_TYPE_VOTE_KEY_NAME]  # type: str

        identifier = ModuleIdentifier(creator, content_hash)

        # Add module to catalog if it isn't known yet
        if not self.persistence.has_module_in_catalog(identifier):
            self._logger.info("module-community: Adding unknown module to catalog (%s, %s)", identifier, name)

            module = Module(identifier, name)
            self.persistence.add_module_to_catalog(module)

        # Add vote to catalog and votes if it isn't known yet
        if not self.persistence.did_vote(public_key, identifier):
            self._logger.info("module-community: Received vote (%s, %s)", identifier, name)
            self.persistence.add_vote_to_votes(public_key, identifier)
            self.persistence.add_vote_to_module_in_catalog(identifier)

    def _sign_module(self, module):
        """
        Internal function for signing a module

        :param module: module
        :type module: Module
        :return: None
        """
        self._logger.debug("module-community: Signing module (%s, %s)", module.id, module.name)

        tx_dict = {
            MODULE_BLOCK_TYPE_VOTE_KEY_CREATOR: module.id.creator,
            MODULE_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH: module.id.content_hash,
            MODULE_BLOCK_TYPE_VOTE_KEY_NAME: module.name,
        }

        self.trustchain.self_sign_block(block_type=MODULE_BLOCK_TYPE_VOTE, transaction=tx_dict)

        self._logger.debug("module-community: Signed module (%s, %s)", module.id, module.name)

    def _crawl_vote_blocks(self):
        """
        Crawl network peers for unknown modules

        :return: None
        """
        self._logger.info("module-community: Crawl network peers for unknown modules")

        for peer in self.get_peers():
            self.trustchain.crawl_chain(peer)

    def _check_votes_in_catalog(self):
        """
        Check if the votes in the catalog match the votes in trustchain

        :return: None
        """
        self._logger.info("module-community: Checking votes in catalog")

        blocks = self.trustchain.persistence.get_blocks_with_type(MODULE_BLOCK_TYPE_VOTE)  # type: [TrustChainBlock]

        votes = {}
        voters = {}

        for block in blocks:
            public_key = block.public_key  # type: bytes
            tx_dict = block.transaction  # type: dict
            creator = tx_dict[MODULE_BLOCK_TYPE_VOTE_KEY_CREATOR]  # type: bytes
            content_hash = tx_dict[MODULE_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH]  # type: str
            name = tx_dict[MODULE_BLOCK_TYPE_VOTE_KEY_NAME]  # type: str

            identifier = ModuleIdentifier(creator, content_hash)

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

            voted_modules = voters[public_key_hex]
            if identifier not in voted_modules:
                voted_modules[identifier] = 1
                voters[public_key_hex] = voted_modules
            else:
                self._logger.info("module-community: Double vote for module (%s) by peer (%s)", identifier, public_key_hex)

        modules = self.persistence.get_modules_from_catalog()

        # Compare and fix vote inconsistencies
        for module in modules:
            identifier = module.id
            votes_in_catalog = module.votes

            if identifier in votes and votes[identifier] != votes_in_catalog:
                self._logger.info("module-community: Vote inconsistency for module (%s)", identifier)
                self.persistence.update_module_in_catalog(identifier, votes[identifier])

            votes.pop(identifier)

        if len(votes) != 0:
            self._logger.info("module-community: inconsistent vote db")

        self._logger.info("module-community: Checking votes in catalog is done")

    def unload(self):
        """
        Unload the community

        :return: None
        """
        super(ModuleCommunity, self).unload()

        # Close the persistence layer
        self.persistence.close()

        # Stop transport
        self.transport.stop()
