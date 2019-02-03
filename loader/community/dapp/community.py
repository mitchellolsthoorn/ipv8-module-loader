from __future__ import absolute_import

# Default library imports
from binascii import unhexlify, hexlify
import importlib
import json
import logging
import os
import sys

# Third party imports
from ipv8.attestation.trustchain.block import TrustChainBlock
from ipv8.attestation.trustchain.community import TrustChainCommunity
from ipv8.attestation.trustchain.listener import BlockListener
from ipv8.community import Community
from ipv8.peer import Peer
from ipv8_service import IPv8, _COMMUNITIES, _WALKERS
from twisted.application.service import MultiService
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

# Project imports
from loader import util
from loader.community.dapp.block import DAppBlock, DAPP_BLOCK_TYPE_VOTE
from loader.community.dapp.dapp_database import DAppDatabase
from loader.community.dapp.transport.bittorrent import BittorrentTransport, DAPPS_DIR, PAYLOADS_DIR, TORRENTS_DIR, \
    EXECUTE_FILE

# Constants
DAPP_DATABASE_NAME = "dapp"  # dApp database name
DAPP_LIBRARY_DIR = "library"  # dApp library directory


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

    def __init__(self, my_peer, endpoint, network, trustchain, **kwargs):
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
        self.working_directory = kwargs.pop('working_directory', "./")  # type: str
        self.ipv8 = kwargs.pop('ipv8')  # type: IPv8
        self.master_service = kwargs.pop('service')  # type: MultiService

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

        # Block listeners
        self.trustchain.add_listener(self, [DAPP_BLOCK_TYPE_VOTE])

        # Database
        self.persistence = DAppDatabase(self.working_directory, DAPP_DATABASE_NAME)

        self.transport = BittorrentTransport(self.working_directory)
        self.discovery_strategy = None
        self.download_strategy = None
        self.seed_strategy = None
        self.execution_engine = None

        self._setup_working_directory_structure()
        self._load_dapp_library_namespace()

        # self.dapp_verify_task = self.register_task("dapp_verify", reactor.callLater(5, self._check_votes_in_catalog))
        self.dapp_crawl_task = self.register_task("dapp_crawl", LoopingCall(self._crawl_vote_blocks), delay=20,
                                                  interval=3600)

    # Util functions
    def _setup_working_directory_structure(self):
        """
        Setup working directory structure if it doesn't exist yet.

        :return: None
        """
        # dApp library
        dapp_library_directory = os.path.join(self.working_directory, DAPP_LIBRARY_DIR)
        util.create_directory_if_not_exists(dapp_library_directory)

        path = os.path.join(dapp_library_directory, "__init__.py")
        with open(path, 'a+'):
            os.utime(path, None)

        # dApps
        dapps_directory = os.path.join(self.working_directory, DAPPS_DIR)
        util.create_directory_if_not_exists(dapps_directory)

        path = os.path.join(dapps_directory, "__init__.py")
        with open(path, 'a+'):
            os.utime(path, None)

        # payloads
        payloads_directory = os.path.join(self.working_directory, PAYLOADS_DIR)
        util.create_directory_if_not_exists(payloads_directory)

        path = os.path.join(payloads_directory, "__init__.py")
        with open(path, 'a+'):
            os.utime(path, None)

        # torrents
        torrents_directory = os.path.join(self.working_directory, TORRENTS_DIR)
        util.create_directory_if_not_exists(torrents_directory)

        path = os.path.join(torrents_directory, "__init__.py")
        with open(path, 'a+'):
            os.utime(path, None)

    def _load_dapp_library_namespace(self):
        """
        Load the namespace for the dApp library

        :return: None
        """
        dapp_library_directory = os.path.join(self.working_directory, DAPPS_DIR)
        sys.path.append(os.path.abspath(dapp_library_directory))

    # Interface functions
    def create_dapp(self, name):
        """
        Create a dApp

        :return: None
        """
        package = self.transport.create_dapp_package(name)
        info_hash = str(package['info_hash'])
        name = package['name']

        self._logger.info("dApp-community: creating dApp (%s, %s)", info_hash, name)

        if self.persistence.has_dapp_in_catalog(info_hash):
            self._logger.info("dApp-community: dApp (%s) already exists, not creating new one", info_hash)
            return

        self.persistence.add_dapp_to_catalog(info_hash, name)
        self.vote_dapp(info_hash)

    def create_dapp_test(self):
        """
        Create a dApp

        :return: None
        """
        info_hash = "9626a56c551c916f5cea40c786b5dc02faf65916"  # Changed last digit from 7 to 6
        name = "execute2"

        self._logger.info("dApp-community: creating dApp (%s, %s)", info_hash, name)

        if self.persistence.has_dapp_in_catalog(info_hash):
            self._logger.info("dApp-community: dApp (%s) already exists, not creating new one", info_hash)
            return

        self.persistence.add_dapp_to_catalog(info_hash, name)
        self.vote_dapp(info_hash)

    def download_dapp(self, info_hash):
        """
        download a dApp

        :param info_hash: dApp identifier
        :type info_hash: str
        :return: None
        """
        self._logger.info("dApp-community: downloading dApp (%s)", info_hash)

        if not self.persistence.has_dapp_in_catalog(info_hash):
            self._logger.info("dApp-community: dApp (%s) not in catalog, not downloading", info_hash)
            return

        dapp = self.persistence.get_dapp_from_catalog(info_hash)

        if dapp:
            name = dapp['name']
            self.transport.download_dapp(info_hash, name)

    def get_dapp_from_catalog(self, info_hash):
        """
        Get dApp with the provided info_hash from the catalog

        :param info_hash: dApp identifier
        :type info_hash: str
        :return: The dApp requested or None if it doesn't exist
        """
        self._logger.info("dApp-community: Getting dApp (%s) from catalog", info_hash)
        return self.persistence.get_dapp_from_catalog(info_hash)

    def get_dapps_from_catalog(self):
        """
        Get all dApps from the catalog

        :return: All dApps
        """
        self._logger.debug("dApp-community: Getting all dApps from catalog")
        return self.persistence.get_dapps_from_catalog()

    def run_dapp(self, info_hash):
        """
        Run the dApp with the provided info_hash

        :param info_hash: dApp identifier
        :type info_hash: str
        :return: None
        """
        self._logger.info("dApp-community: running dApp (%s)", info_hash)

        if not self.persistence.has_dapp_in_catalog(info_hash):
            self._logger.info("dApp-community: dApp (%s) not in catalog, not running", info_hash)
            return

        dapp = self.persistence.get_dapp_from_catalog(info_hash)

        if dapp:
            name = dapp['name']
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
                        importlib.import_module(name + "." + executable_file)
                    elif package_type == "overlay":
                        self._logger.info("dApp-community: dApp overlay (%s) found", name)

                        overlay_file = data['overlay_file']
                        configuration = getattr(importlib.import_module(name + "." + overlay_file), "config")
                        extra_communities = getattr(importlib.import_module(name + "." + overlay_file), "extra_communities")

                        for overlay in configuration['overlays']:
                            overlay_class = _COMMUNITIES.get(overlay['class'], (extra_communities or {}).get(overlay['class']))
                            my_peer = self.my_peer
                            overlay_instance = overlay_class(my_peer, self.endpoint, self.network, **overlay['initialize'])
                            self.ipv8.overlays.append(overlay_instance)
                            for walker in overlay['walkers']:
                                strategy_class = _WALKERS.get(walker['strategy'], overlay_instance.get_available_strategies().get(walker['strategy']))
                                args = walker['init']
                                target_peers = walker['peers']
                                self.ipv8.strategies.append((strategy_class(overlay_instance, **args), target_peers))
                            for config in overlay['on_start']:
                                reactor.callWhenRunning(getattr(overlay_instance, config[0]), *config[1:])
                            self._logger.info("dApp-community: dApp overlay (%s) added", overlay['class'])

                    elif package_type == "service":
                        self._logger.info("dApp-community: dApp service (%s) found", name)
                        service_file = data['service_file']
                        service_class = data['service_class']
                        service_options = data['service_options']
                        cls = getattr(importlib.import_module(name + "." + service_file), service_class)
                        service = cls().makeService(service_options)
                        self.master_service.addService(service)
                        self._logger.info("dApp-community: dApp service (%s) added", service.name)

    def vote_dapp(self, info_hash):
        """
        Vote on dApp with provided info_hash

        :param info_hash: dApp identifier
        :type info_hash: str
        :return: None
        """
        if not self.persistence.has_dapp_in_catalog(info_hash):
            self._logger.info("dApp-community: dApp (%s) not in catalog, not voting", info_hash)
            return

        if self.persistence.did_vote(self.my_peer.public_key.key_to_bin(), info_hash):
            self._logger.info("dApp-community: Already voted on dApp (%s), not voting", info_hash)
            return

        dapp = self.persistence.get_dapp_from_catalog(info_hash)

        if dapp:
            name = dapp['name']

            # Add vote to catalog and votes
            self.persistence.add_vote(self.my_peer.public_key.key_to_bin(), info_hash)
            self.persistence.add_vote_to_dapp_in_catalog(info_hash)

            self._logger.info("dApp-community: Vote for dApp (%s, %s)", info_hash, name)
            self._sign_dapp(info_hash, name)

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
        info_hash = tx_dict['info_hash']  # type: str
        name = tx_dict['name']  # type: str

        # Add dApp to catalog if it isn't known yet
        if not self.persistence.has_dapp_in_catalog(info_hash):
            self._logger.info("dApp-community: Adding unknown dApp to catalog (%s, %s)", info_hash, name)
            self.persistence.add_dapp_to_catalog(info_hash, name, 0)

        # Add vote to catalog and votes if it isn't known yet
        if not self.persistence.did_vote(public_key, info_hash):
            self._logger.info("dApp-community: Received vote (%s, %s)", info_hash, name)
            self.persistence.add_vote(public_key, info_hash)
            self.persistence.add_vote_to_dapp_in_catalog(info_hash)

    def _sign_dapp(self, info_hash, name):
        """
        Internal function for signing a dApp

        :param info_hash: dApp identifier
        :type info_hash: str
        :param name: Name of the dApp
        :type name: str
        :return: None
        """
        self._logger.debug("dApp-community: Signing dApp (%s, %s)", info_hash, name)

        tx_dict = {
            'info_hash': info_hash,
            'name': name,
        }

        self.trustchain.self_sign_block(block_type=DAPP_BLOCK_TYPE_VOTE, transaction=tx_dict)

        self._logger.debug("dApp-community: Signed dApp (%s, %s)", info_hash, name)

    def _crawl_vote_blocks(self):
        """
        Crawl network peers for unknown dApps

        :return: None
        """
        self._logger.info("dApp-community: Crawl network peers for unknown dApps")

        for peer in self.get_peers():
            block = self.trustchain.persistence.get_latest(peer.public_key.key_to_bin())
            if block:
                latest_block_num = block.sequence_number
            else:
                latest_block_num = 0

            self.trustchain.crawl_chain(peer, latest_block_num)

    def _check_votes_in_catalog(self):
        """
        Check if the votes in the catalog match the votes in the trustchain

        :return: None
        """
        self._logger.info("dApp-community: Checking votes in catalog")

        blocks = self.trustchain.persistence.get_blocks_with_type(DAPP_BLOCK_TYPE_VOTE)  # type: [TrustChainBlock]

        votes = {}
        voters = {}

        for block in blocks:
            public_key = block.public_key
            info_hash = block.transaction['info_hash']

            # Check votes database
            if not self.persistence.did_vote(public_key, info_hash):
                self.persistence.add_vote(public_key, info_hash)

            # Check number of votes
            if info_hash in votes:
                votes[info_hash] = votes[info_hash] + 1
            else:
                votes[info_hash] = 0

            # Check double votes
            public_key_hex = hexlify(public_key)
            if public_key_hex not in voters:
                voters[public_key_hex] = {}

            voted_dapps = voters[public_key_hex]
            if info_hash not in voted_dapps:
                voted_dapps[info_hash] = 1
                voters[public_key_hex] = voted_dapps
            else:
                self._logger.info("dApp-community: Double vote for dApp (%s) by peer (%s)", info_hash, public_key_hex)

        dapps = self.persistence.get_dapps_from_catalog()

        # Compare and fix vote inconsistencies
        for dapp in dapps:
            info_hash = dapp['info_hash']
            votes_in_catalog = dapp['votes']

            if info_hash in votes and votes[info_hash] != votes_in_catalog:
                self._logger.info("dApp-community: Vote inconsistency for dApp (%s)", info_hash)
                self.persistence.update_dapp_in_catalog(info_hash, votes[info_hash])

            votes.pop(info_hash)

        if len(votes) != 0:
            self._logger.info("dApp-community: inconsistent vote db")

        # Clean up
        votes = None
        voters = None

        self._logger.info("dApp-community: Checking votes in catalog is done")

    def unload(self):
        """
        Unload the community

        :return: None
        """
        super(DAppCommunity, self).unload()

        # Close the persistence layer
        self.persistence.close()
