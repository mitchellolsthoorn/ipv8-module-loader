from __future__ import absolute_import

# Default library imports
from binascii import hexlify
import os

# Third party imports
from ipv8.database import Database, database_blob

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
        CREATE TABLE IF NOT EXISTS dapp_catalog (
            info_hash   TEXT NOT NULL,
            name        TEXT NOT NULL,
            votes       INTEGER NOT NULL,

            PRIMARY KEY (info_hash)
        );
        
        CREATE TABLE IF NOT EXISTS dapp_votes (
            public_key  TEXT NOT NULL,
            info_hash   TEXT NOT NULL,

            PRIMARY KEY (public_key, info_hash)
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

    # dApp catalog
    def add_dapp_to_catalog(self, info_hash, name, votes=0):
        """
        Add dApp to the catalog

        :param info_hash: dApp identifier
        :type info_hash: str
        :param name: Name of the dApp
        :type name: str
        :param votes: Number of votes
        :type votes: int
        :return: None
        """

        self._logger.info("persistence: Adding dApp (%s) to catalog", info_hash)

        sql = "INSERT INTO dapp_catalog (info_hash, name, votes) VALUES(?, ?, ?)"
        self.execute(sql, (database_blob(info_hash), database_blob(name), votes,))
        self.commit()

    def add_vote_to_dapp_in_catalog(self, info_hash):
        """
        Increment votes for the provided dApp

        :param info_hash: dApp identifier
        :type info_hash: str
        :return: None
        """
        sql = "UPDATE dapp_catalog SET votes = votes + 1 WHERE info_hash = ?;"
        self.execute(sql, (database_blob(info_hash),))
        self.commit()

    def get_dapp_from_catalog(self, info_hash):
        """
        Get dApp from the catalog

        :param info_hash: dApp identifier
        :type info_hash: str
        :return: dApp information
        """
        self._logger.debug("persistence: Getting dApp (%s) from catalog", info_hash)

        if not self.has_dapp_in_catalog(info_hash):
            return None

        sql = "SELECT * FROM dapp_catalog WHERE info_hash = ?;"
        res = list(self.execute(sql, (database_blob(info_hash),)))

        dapp = res[0]
        return {
            'info_hash': str(dapp[0]),
            'name': str(dapp[1]),
            'votes': int(dapp[2]),
        }

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
            dapps.append({
                'info_hash': str(dapp[0]),
                'name': str(dapp[1]),
                'votes': str(dapp[2]),
            })
        return dapps

    def has_dapp_in_catalog(self, info_hash):
        """
        Check if dApp exists in catalog

        :param info_hash: dApp identifier
        :type info_hash: str
        :return: If the dApp has been found
        """
        self._logger.debug("persistence: Check for dApp (%s) in catalog", info_hash)

        sql = "SELECT info_hash FROM dapp_catalog WHERE info_hash = ?;"
        res = list(self.execute(sql, (database_blob(info_hash),)))
        count = len(res)

        if count > 0:
            return True

        return False

    def update_dapp_in_catalog(self, info_hash, votes):
        """
        Update the number of votes for a dApp in the catalog

        :param info_hash: dApp identifier
        :type info_hash: str
        :param votes: Number of votes
        :type votes: int
        :return: None
        """
        self._logger.debug("persistence: Update dapp (%s)", info_hash)

        sql = "UPDATE dapp_catalog SET votes = ? WHERE info_hash = ?;"
        self.execute(sql, (votes, database_blob(info_hash),))
        self.commit()

    # dApp votes
    def add_vote(self, public_key, info_hash):
        """
        Add vote to votes database

        :param public_key: Public key of the voter
        :type public_key: bytes
        :param info_hash: dApp identifier
        :type info_hash: str
        :return: None
        """
        self._logger.debug("persistence: Add vote (%s, %s) to votes", hexlify(public_key), info_hash)

        sql = "INSERT INTO dapp_votes (public_key, info_hash) VALUES (?, ?);"
        self.execute(sql, (database_blob(public_key), database_blob(info_hash),))
        self.commit()

    def did_vote(self, public_key, info_hash):
        """
        Check if the node with the provided public key voted on the dApp with the provided info_hash

        :param public_key: Public key of the voter
        :type public_key: bytes
        :param info_hash: dApp identifier
        :type info_hash: str
        :return: True if voted, otherwise False
        """
        self._logger.debug("persistence: Check for vote (%s, %s) in votes", hexlify(public_key), info_hash)

        sql = "SELECT * FROM dapp_votes WHERE public_key = ? AND info_hash = ?;"
        res = list(self.execute(sql, (database_blob(public_key), database_blob(info_hash),)))
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
