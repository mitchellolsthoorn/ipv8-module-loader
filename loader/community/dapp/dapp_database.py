from __future__ import absolute_import

import os
# Default library imports
from binascii import hexlify

# Third party imports
from ipv8.database import Database, database_blob

# Project imports
from loader.community.dapp.core.dapp import DApp
from loader.community.dapp.core.dapp_identifier import DAppIdentifier

# Constants
DATABASE_DIRECTORY = os.path.join(u"sqlite")  # Database sub-directory


class DAppDatabase(Database):
    """
    Persistence layer for dApp information.
    """

    # Database scheme version
    LATEST_DB_VERSION = 1  # type: int

    def __init__(self, working_directory, db_name):
        """
        Sets up the persistence layer.

        :param working_directory: Path to the working directory where the state is stored
        :type working_directory: str
        :param db_name: The name of the database
        :type db_name: str
        """
        if working_directory != u":memory:":
            db_path = os.path.join(working_directory, os.path.join(DATABASE_DIRECTORY, u"{0}.db".format(db_name)))
        else:
            db_path = working_directory

        super(DAppDatabase, self).__init__(db_path)

        self._logger.info("persistence: dApp database path: %s", db_path)
        self._logger.info("persistence: dApp database version: %d", self.LATEST_DB_VERSION)
        self.db_name = db_name
        self.open()

    def get_schema(self):
        """
        Return the schema for the database.
        """
        return u"""
        CREATE TABLE IF NOT EXISTS dapp_cache (
            public_key  TEXT NOT NULL,
            info_hash   TEXT NOT NULL,

            PRIMARY KEY (public_key, info_hash)
        );
        
        CREATE TABLE IF NOT EXISTS dapp_catalog (
            public_key  TEXT NOT NULL,
            info_hash   TEXT NOT NULL,
            name        TEXT NOT NULL,
            votes       INTEGER NOT NULL,

            PRIMARY KEY (public_key, info_hash)
        );
        
        CREATE TABLE IF NOT EXISTS dapp_library (
            public_key  TEXT NOT NULL,
            info_hash   TEXT NOT NULL,

            PRIMARY KEY (public_key, info_hash)
        );
        
        CREATE TABLE IF NOT EXISTS dapp_votes (
            voter_public_key    TEXT NOT NULL,
            public_key          TEXT NOT NULL,
            info_hash           TEXT NOT NULL,

            PRIMARY KEY (voter_public_key, public_key, info_hash)
        );

        CREATE TABLE IF NOT EXISTS option(key TEXT PRIMARY KEY, value BLOB);
        DELETE FROM option WHERE key = 'database_version';
        INSERT INTO option(key, value) VALUES('database_version', '{version}');
        """.format(version=self.LATEST_DB_VERSION)

    def get_upgrade_script(self, current_version):
        """
        Return the upgrade script for a specific version.
        :param current_version: the version of the script to return.
        """
        return None

    # dApp cache
    def add_dapp_to_cache(self, dapp_identifier):
        """
        Add dApp to cache

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: None
        """
        self._logger.info("persistence: Adding dApp (%s) to cache", dapp_identifier)

        sql = "INSERT INTO dapp_cache (public_key, info_hash) VALUES(?, ?)"
        self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),))
        self.commit()

    def get_dapp_from_cache(self, dapp_identifier):
        """
        Get dApp from the cache

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: dApp information
        """
        self._logger.debug("persistence: Getting dApp (%s) from cache", dapp_identifier)

        if not self.has_dapp_in_cache(dapp_identifier):
            return None

        sql = "SELECT * FROM dapp_cache WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),)))

        dapp = res[0]

        public_key = bytes(dapp[0])
        content_hash = str(dapp[1])
        identifier = DAppIdentifier(public_key, content_hash)

        return identifier

    def get_dapps_from_cache(self):
        """
        Retrieve all dApps from the cache

        :return: All dApps
        """
        self._logger.debug("persistence: Getting all dApps from cache")

        sql = "SELECT * FROM dapp_cache;"
        res = list(self.execute(sql))

        dapps = []
        for dapp in res:
            public_key = bytes(dapp[0])
            content_hash = str(dapp[1])
            identifier = DAppIdentifier(public_key, content_hash)

            dapps.append(identifier)
        return dapps

    def has_dapp_in_cache(self, dapp_identifier):
        """
        Check if dApp exists in cache

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: If the dApp has been found
        """
        self._logger.debug("persistence: Check for dApp (%s) in cache", dapp_identifier)

        sql = "SELECT public_key, info_hash FROM dapp_cache WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    # dApp catalog
    def add_dapp_to_catalog(self, dapp):
        """
        Add dApp to the catalog

        :param dapp: dApp
        :type dapp: DApp
        :return: None
        """
        self._logger.info("persistence: Adding dApp (%s) to catalog", dapp)

        sql = "INSERT INTO dapp_catalog (public_key, info_hash, name, votes) VALUES(?, ?, ?, ?)"
        self.execute(sql, (
            database_blob(dapp.id.creator), database_blob(dapp.id.content_hash), database_blob(dapp.name), dapp.votes,))
        self.commit()

    def add_vote_to_dapp_in_catalog(self, dapp_identifier):
        """
        Increment votes for the provided dApp

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: None
        """
        self._logger.debug("persistence: Adding vote to dApp (%s) in catalog", dapp_identifier)

        sql = "UPDATE dapp_catalog SET votes = votes + 1 WHERE public_key = ? AND info_hash = ?;"
        self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),))
        self.commit()

    def get_dapp_from_catalog(self, dapp_identifier):
        """
        Get dApp from the catalog

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: dApp information
        """
        self._logger.debug("persistence: Getting dApp (%s) from catalog", dapp_identifier)

        if not self.has_dapp_in_catalog(dapp_identifier):
            return None

        sql = "SELECT * FROM dapp_catalog WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),)))

        dapp = res[0]

        public_key = bytes(dapp[0])
        content_hash = str(dapp[1])
        name = str(dapp[2])
        identifier = DAppIdentifier(public_key, content_hash)
        votes = int(dapp[3])

        return DApp(identifier, name, votes)

    def get_dapps_from_catalog(self):
        """
        Retrieve all dApps from the catalog

        :return: All dApps
        """
        self._logger.debug("persistence: Getting all dApps from catalog")

        sql = "SELECT * FROM dapp_catalog;"
        res = list(self.execute(sql))

        dapps = []
        for dapp in res:
            public_key = bytes(dapp[0])
            content_hash = str(dapp[1])
            name = str(dapp[2])
            identifier = DAppIdentifier(public_key, content_hash)
            votes = int(dapp[3])

            dapps.append(DApp(identifier, name, votes))
        return dapps

    def has_dapp_in_catalog(self, dapp_identifier):
        """
        Check if dApp exists in catalog

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: If the dApp has been found
        """
        self._logger.debug("persistence: Check for dApp (%s) in catalog", dapp_identifier)

        sql = "SELECT public_key, info_hash FROM dapp_catalog WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    def update_dapp_in_catalog(self, dapp_identifier, votes):
        """
        Update the number of votes for a dApp in the catalog

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :param votes: Number of votes
        :type votes: int
        :return: None
        """
        self._logger.debug("persistence: Update dApp (%s)", dapp_identifier)

        sql = "UPDATE dapp_catalog SET votes = ? WHERE public_key = ? AND info_hash = ?;"
        self.execute(sql, (votes, database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),))
        self.commit()

    # dApp library
    def add_dapp_to_library(self, dapp_identifier):
        """
        Add dApp to library

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: None
        """
        self._logger.info("persistence: Adding dApp (%s) to library", dapp_identifier)

        sql = "INSERT INTO dapp_library (public_key, info_hash) VALUES(?, ?)"
        self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),))
        self.commit()

    def get_dapp_from_library(self, dapp_identifier):
        """
        Get dApp from the library

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: dApp information
        """
        self._logger.debug("persistence: Getting dApp (%s) from library", dapp_identifier)

        if not self.has_dapp_in_library(dapp_identifier):
            return None

        sql = "SELECT * FROM dapp_library WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),)))

        dapp = res[0]

        public_key = bytes(dapp[0])
        content_hash = str(dapp[1])
        identifier = DAppIdentifier(public_key, content_hash)

        return identifier

    def get_dapps_from_library(self):
        """
        Retrieve all dApps from the library

        :return: All dApps
        """
        self._logger.debug("persistence: Getting all dApps from library")

        sql = "SELECT * FROM dapp_library;"
        res = list(self.execute(sql))

        dapps = []
        for dapp in res:
            public_key = bytes(dapp[0])
            content_hash = str(dapp[1])
            identifier = DAppIdentifier(public_key, content_hash)

            dapps.append(identifier)
        return dapps

    def has_dapp_in_library(self, dapp_identifier):
        """
        Check if dApp exists in library

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: If the dApp has been found
        """
        self._logger.debug("persistence: Check for dApp (%s) in library", dapp_identifier)

        sql = "SELECT public_key, info_hash FROM dapp_library WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql,
                         (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    # dApp votes
    def add_vote_to_votes(self, voter_public_key, dapp_identifier):
        """
        Add vote to votes database

        :param voter_public_key: Public key of the voter
        :type voter_public_key: bytes
        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: None
        """
        self._logger.debug("persistence: Add vote (%s, %s) to votes", hexlify(voter_public_key), dapp_identifier)

        sql = "INSERT INTO dapp_votes (voter_public_key, public_key, info_hash) VALUES (?, ?, ?);"
        self.execute(sql, (database_blob(voter_public_key), database_blob(dapp_identifier.creator),
                           database_blob(dapp_identifier.content_hash),))
        self.commit()

    def get_votes_for_dapp(self, dapp_identifier):
        """
        Get votes for dApp

        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: vote information
        """
        self._logger.debug("persistence: Getting votes for dApp (%s)", dapp_identifier)

        if not self.has_dapp_in_catalog(dapp_identifier):
            return None

        sql = "SELECT * FROM dapp_votes WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(dapp_identifier.creator), database_blob(dapp_identifier.content_hash),)))

        votes = []
        for vote in res:
            voter_public_key = bytes(vote[0])
            creator = bytes(vote[1])
            content_hash = str(vote[2])
            identifier = DAppIdentifier(creator, content_hash)

            votes.append({
                'voter': voter_public_key,
                'identifier': identifier,
            })
        return votes

    def get_votes_for_peer(self, peer):
        """
        Get votes for peer

        :param peer: public key of peer
        :type peer: bytes
        :return: vote information
        """
        self._logger.debug("persistence: Getting votes for peer (%s)", hexlify(peer))

        sql = "SELECT * FROM dapp_votes WHERE voter_public_key = ?;"
        res = list(self.execute(sql, (database_blob(peer),)))

        votes = []
        for vote in res:
            voter_public_key = bytes(vote[0])
            creator = bytes(vote[1])
            content_hash = str(vote[2])
            identifier = DAppIdentifier(creator, content_hash)

            votes.append({
                'voter': voter_public_key,
                'identifier': identifier,
            })
        return votes

    def did_vote(self, voter_public_key, dapp_identifier):
        """
        Check if the node with the provided public key voted on the dApp with the provided info_hash

        :param voter_public_key: Public key of the voter
        :type voter_public_key: bytes
        :param dapp_identifier: dApp identifier
        :type dapp_identifier: DAppIdentifier
        :return: True if voted, otherwise False
        """
        self._logger.debug("persistence: Check for vote (%s, %s) in votes", hexlify(voter_public_key), dapp_identifier)

        sql = "SELECT * FROM dapp_votes WHERE voter_public_key = ? AND public_key = ? AND info_hash = ?;"
        res = list(self.execute(sql, (database_blob(voter_public_key), database_blob(dapp_identifier.creator),
                                      database_blob(dapp_identifier.content_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    def open(self, initial_statements=True, prepare_visioning=True):
        return super(DAppDatabase, self).open(initial_statements, prepare_visioning)

    def close(self, commit=True):
        return super(DAppDatabase, self).close(commit)

    def check_database(self, database_version):
        """
        Ensure the proper schema is used by the database.
        :param database_version: Current version of the database.
        :return:
        """
        assert database_version.isdigit()
        assert int(database_version) >= 0
        database_version = int(database_version)

        if database_version < self.LATEST_DB_VERSION:
            self.executescript(self.get_schema())

        return self.LATEST_DB_VERSION
