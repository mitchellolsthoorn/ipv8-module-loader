from __future__ import absolute_import

import os
# Default library imports
from binascii import hexlify

# Third party imports
from ipv8.database import Database, database_blob

# Project imports
from module_loader.community.module.core.module import Module
from module_loader.community.module.core.module_identifier import ModuleIdentifier

# Constants
DATABASE_DIRECTORY = os.path.join(u"sqlite")  # Database sub-directory


class ModuleDatabase(Database):
    """
    Persistence layer for module information.
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

        super(ModuleDatabase, self).__init__(db_path)

        self._logger.info("persistence: module database path: %s", db_path)
        self._logger.info("persistence: module database version: %d", self.LATEST_DB_VERSION)
        self.db_name = db_name
        self.open()

    def get_schema(self):
        """
        Return the schema for the database.
        """
        return u"""
        CREATE TABLE IF NOT EXISTS module_cache (
            public_key  TEXT NOT NULL,
            info_hash   TEXT NOT NULL,

            PRIMARY KEY (public_key, info_hash)
        );
        
        CREATE TABLE IF NOT EXISTS module_catalog (
            public_key  TEXT NOT NULL,
            info_hash   TEXT NOT NULL,
            name        TEXT NOT NULL,
            votes       INTEGER NOT NULL,

            PRIMARY KEY (public_key, info_hash)
        );
        
        CREATE TABLE IF NOT EXISTS module_library (
            public_key  TEXT NOT NULL,
            info_hash   TEXT NOT NULL,

            PRIMARY KEY (public_key, info_hash)
        );
        
        CREATE TABLE IF NOT EXISTS module_votes (
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

    # module cache
    def add_module_to_cache(self, module_identifier):
        """
        Add module to cache

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: None
        """
        self._logger.info("persistence: Adding module (%s) to cache", module_identifier)

        sql = "INSERT INTO module_cache (public_key, info_hash) VALUES(?, ?)"
        self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),))
        self.commit()

    def get_module_from_cache(self, module_identifier):
        """
        Get module from the cache

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: module information
        """
        self._logger.debug("persistence: Getting module (%s) from cache", module_identifier)

        if not self.has_module_in_cache(module_identifier):
            return None

        sql = "SELECT * FROM module_cache WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),)))

        module = res[0]

        public_key = bytes(module[0])
        content_hash = str(module[1])
        identifier = ModuleIdentifier(public_key, content_hash)

        return identifier

    def get_modules_from_cache(self):
        """
        Retrieve all modules from the cache

        :return: All modules
        """
        self._logger.debug("persistence: Getting all modules from cache")

        sql = "SELECT * FROM module_cache;"
        res = list(self.execute(sql))

        modules = []
        for module in res:
            public_key = bytes(module[0])
            content_hash = str(module[1])
            identifier = ModuleIdentifier(public_key, content_hash)

            modules.append(identifier)
        return modules

    def has_module_in_cache(self, module_identifier):
        """
        Check if module exists in cache

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: If the module has been found
        """
        self._logger.debug("persistence: Check for module (%s) in cache", module_identifier)

        sql = "SELECT public_key, info_hash FROM module_cache WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    # module catalog
    def add_module_to_catalog(self, module):
        """
        Add module to the catalog

        :param module: module
        :type module: Module
        :return: None
        """
        self._logger.info("persistence: Adding module (%s) to catalog", module)

        sql = "INSERT INTO module_catalog (public_key, info_hash, name, votes) VALUES(?, ?, ?, ?)"
        self.execute(sql, (
            database_blob(module.id.creator), database_blob(module.id.content_hash), database_blob(module.name), module.votes,))
        self.commit()

    def add_vote_to_module_in_catalog(self, module_identifier):
        """
        Increment votes for the provided module

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: None
        """
        self._logger.debug("persistence: Adding vote to module (%s) in catalog", module_identifier)

        sql = "UPDATE module_catalog SET votes = votes + 1 WHERE public_key = ? AND info_hash = ?;"
        self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),))
        self.commit()

    def get_module_from_catalog(self, module_identifier):
        """
        Get module from the catalog

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: module information
        """
        self._logger.debug("persistence: Getting module (%s) from catalog", module_identifier)

        if not self.has_module_in_catalog(module_identifier):
            return None

        sql = "SELECT * FROM module_catalog WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),)))

        module = res[0]

        public_key = bytes(module[0])
        content_hash = str(module[1])
        name = str(module[2])
        identifier = ModuleIdentifier(public_key, content_hash)
        votes = int(module[3])

        return Module(identifier, name, votes)

    def get_modules_from_catalog(self):
        """
        Retrieve all modules from the catalog

        :return: All modules
        """
        self._logger.debug("persistence: Getting all modules from catalog")

        sql = "SELECT * FROM module_catalog;"
        res = list(self.execute(sql))

        modules = []
        for module in res:
            public_key = bytes(module[0])
            content_hash = str(module[1])
            name = str(module[2])
            identifier = ModuleIdentifier(public_key, content_hash)
            votes = int(module[3])

            modules.append(Module(identifier, name, votes))
        return modules

    def has_module_in_catalog(self, module_identifier):
        """
        Check if module exists in catalog

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: If the module has been found
        """
        self._logger.debug("persistence: Check for module (%s) in catalog", module_identifier)

        sql = "SELECT public_key, info_hash FROM module_catalog WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    def update_module_in_catalog(self, module_identifier, votes):
        """
        Update the number of votes for a module in the catalog

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :param votes: Number of votes
        :type votes: int
        :return: None
        """
        self._logger.debug("persistence: Update module (%s)", module_identifier)

        sql = "UPDATE module_catalog SET votes = ? WHERE public_key = ? AND info_hash = ?;"
        self.execute(sql, (votes, database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),))
        self.commit()

    # module library
    def add_module_to_library(self, module_identifier):
        """
        Add module to library

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: None
        """
        self._logger.info("persistence: Adding module (%s) to library", module_identifier)

        sql = "INSERT INTO module_library (public_key, info_hash) VALUES(?, ?)"
        self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),))
        self.commit()

    def get_module_from_library(self, module_identifier):
        """
        Get module from the library

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: module information
        """
        self._logger.debug("persistence: Getting module (%s) from library", module_identifier)

        if not self.has_module_in_library(module_identifier):
            return None

        sql = "SELECT * FROM module_library WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),)))

        module = res[0]

        public_key = bytes(module[0])
        content_hash = str(module[1])
        identifier = ModuleIdentifier(public_key, content_hash)

        return identifier

    def get_modules_from_library(self):
        """
        Retrieve all modules from the library

        :return: All modules
        """
        self._logger.debug("persistence: Getting all modules from library")

        sql = "SELECT * FROM module_library;"
        res = list(self.execute(sql))

        modules = []
        for module in res:
            public_key = bytes(module[0])
            content_hash = str(module[1])
            identifier = ModuleIdentifier(public_key, content_hash)

            modules.append(identifier)
        return modules

    def has_module_in_library(self, module_identifier):
        """
        Check if module exists in library

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: If the module has been found
        """
        self._logger.debug("persistence: Check for module (%s) in library", module_identifier)

        sql = "SELECT public_key, info_hash FROM module_library WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql,
                         (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    # module votes
    def add_vote_to_votes(self, voter_public_key, module_identifier):
        """
        Add vote to votes database

        :param voter_public_key: Public key of the voter
        :type voter_public_key: bytes
        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: None
        """
        self._logger.debug("persistence: Add vote (%s, %s) to votes", hexlify(voter_public_key), module_identifier)

        sql = "INSERT INTO module_votes (voter_public_key, public_key, info_hash) VALUES (?, ?, ?);"
        self.execute(sql, (database_blob(voter_public_key), database_blob(module_identifier.creator),
                           database_blob(module_identifier.content_hash),))
        self.commit()

    def get_votes_for_module(self, module_identifier):
        """
        Get votes for module

        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: vote information
        """
        self._logger.debug("persistence: Getting votes for module (%s)", module_identifier)

        if not self.has_module_in_catalog(module_identifier):
            return None

        sql = "SELECT * FROM module_votes WHERE public_key = ? AND info_hash = ?;"
        res = list(
            self.execute(sql, (database_blob(module_identifier.creator), database_blob(module_identifier.content_hash),)))

        votes = []
        for vote in res:
            voter_public_key = bytes(vote[0])
            creator = bytes(vote[1])
            content_hash = str(vote[2])
            identifier = ModuleIdentifier(creator, content_hash)

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

        sql = "SELECT * FROM module_votes WHERE voter_public_key = ?;"
        res = list(self.execute(sql, (database_blob(peer),)))

        votes = []
        for vote in res:
            voter_public_key = bytes(vote[0])
            creator = bytes(vote[1])
            content_hash = str(vote[2])
            identifier = ModuleIdentifier(creator, content_hash)

            votes.append({
                'voter': voter_public_key,
                'identifier': identifier,
            })
        return votes

    def did_vote(self, voter_public_key, module_identifier):
        """
        Check if the node with the provided public key voted on the module with the provided info_hash

        :param voter_public_key: Public key of the voter
        :type voter_public_key: bytes
        :param module_identifier: module identifier
        :type module_identifier: ModuleIdentifier
        :return: True if voted, otherwise False
        """
        self._logger.debug("persistence: Check for vote (%s, %s) in votes", hexlify(voter_public_key), module_identifier)

        sql = "SELECT * FROM module_votes WHERE voter_public_key = ? AND public_key = ? AND info_hash = ?;"
        res = list(self.execute(sql, (database_blob(voter_public_key), database_blob(module_identifier.creator),
                                      database_blob(module_identifier.content_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    def open(self, initial_statements=True, prepare_visioning=True):
        return super(ModuleDatabase, self).open(initial_statements, prepare_visioning)

    def close(self, commit=True):
        return super(ModuleDatabase, self).close(commit)

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
