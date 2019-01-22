from __future__ import absolute_import

import os

from pyipv8.ipv8.database import Database, database_blob
# from pyipv8.ipv8.util import is_unicode

DATABASE_DIRECTORY = os.path.join(u"sqlite")


class DAppDatabase(Database):
    """
    Persistence layer for the DAppCrowd Community.
    Connection layer to SQLiteDB.
    Ensures a proper DB schema on startup.
    """
    LATEST_DB_VERSION = 1

    def __init__(self, working_directory, db_name):
        """
        Sets up the persistence layer ready for use.
        :param working_directory: Path to the working directory
        that will contain the the db at working directory/DATABASE_PATH
        :param db_name: The name of the database
        """
        if working_directory != u":memory:":
            db_path = os.path.join(working_directory, os.path.join(DATABASE_DIRECTORY, u"%s.db" % db_name))
        else:
            db_path = working_directory

        super(DAppDatabase, self).__init__(db_path)

        self._logger.debug("DApp database path: %s", db_path)
        self.db_name = db_name
        self.open()

    def get_schema(self):
        """
        Return the schema for the database.
        """
        return u"""
        CREATE TABLE IF NOT EXISTS dapp_catalog (
            info_hash          TEXT NOT NULL,
            name               TEXT NOT NULL,

            PRIMARY KEY (info_hash)
        );

        CREATE TABLE IF NOT EXISTS option(key TEXT PRIMARY KEY, value BLOB);
        DELETE FROM option WHERE key = 'database_version';
        INSERT INTO option(key, value) VALUES('database_version', '%s');
        """ % str(self.LATEST_DB_VERSION)

    def get_upgrade_script(self, current_version):
        """
        Return the upgrade script for a specific version.
        :param current_version: the version of the script to return.
        """
        return None

    def add_dapp(self, block):
        tx = block.transaction
        sql = "INSERT INTO dapp_catalog (info_hash, name) VALUES(?, ?)"
        self.execute(sql, (database_blob(tx['info_hash']), database_blob(tx['name'])))
        self.commit()

    def get_dapp(self, info_hash):
        dapp = list(self.execute("SELECT info_hash, name FROM dapp_catalog WHERE info_hash = ?", (database_blob(info_hash))))
        if not dapp:
            return []
        return dapp

    def get_dapps(self):
        dapps = list(self.execute("SELECT * FROM dapp_catalog;"))

        dapps_list = []
        for dapp in dapps:
            dapps_list.append({
                'info_hash': dapp[0],
                'name': dapp[1],
            })
        return dapps_list

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
        # assert is_unicode(database_version)
        assert database_version.isdigit()
        assert int(database_version) >= 0
        database_version = int(database_version)

        if database_version < self.LATEST_DB_VERSION:
            self.executescript(self.get_schema())

        return self.LATEST_DB_VERSION
