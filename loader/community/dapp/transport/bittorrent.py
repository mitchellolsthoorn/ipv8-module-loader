from __future__ import absolute_import

# Default library imports
import logging
import os
import time

# Third party imports
import libtorrent as lt

# Project imports

# Constants
DAPPS_DIR = "dapps"
EXECUTE_FILE = "execute.py"
PAYLOADS_DIR = "payloads"
TORRENTS_DIR = "torrents"


class BittorrentTransport(object):
    """
    BitTorrent transport for moving dApps between nodes
    """

    def __init__(self, working_directory, dht_enable=True, lsd_enable=True, tracker_enable=True):
        super(BittorrentTransport, self).__init__()

        self.working_directory = working_directory
        self.dht_enable = dht_enable
        self.lsd_enable = lsd_enable
        self.tracker_enable = tracker_enable

        # Logging
        self._logger = logging.getLogger(self.__class__.__name__)

        # Create libtorrent session
        self.ses = lt.session()
        self.ses.listen_on(6881, 6891)

        if self.dht_enable:
            # Enable and bootstrap DHT
            self.ses.add_dht_router("router.utorrent.com", 6881)
            self.ses.add_dht_router("router.bittorrent.com", 6881)
            self.ses.add_dht_router("dht.transmissionbt.com", 6881)
            self.ses.start_dht()

        if self.lsd_enable:
            # Enable LSD
            self.ses.start_lsd()

    def download_dapp(self, info_hash, name):
        dapps_directory = os.path.join(self.working_directory, DAPPS_DIR)

        params = {'save_path': dapps_directory}
        torrent = "magnet:?xt=urn:btih:{0}&dn={1}".format(info_hash, name)
        h = lt.add_magnet_uri(self.ses, torrent, params)

        self._logger.debug("transport: checking torrent (%s)", h.name())

        while not h.has_metadata():
            time.sleep(.1)

        self._logger.debug("transport: metadata complete for torrent (%s)", info_hash)

        torrent_info = h.get_torrent_info()
        h = self.ses.add_torrent({'ti': torrent_info, 'save_path': dapps_directory, 'seed_mode': True})

    def create_dapp_package(self, dapp):
        payloads_directory = os.path.join(self.working_directory, PAYLOADS_DIR)
        torrents_directory = os.path.join(self.working_directory, TORRENTS_DIR)

        tracker_list = ['udp://tracker.publicbt.com:80/announce', 'udp://tracker.openbittorrent.com:80/announce']

        self._logger.debug("transport: creating torrent (%s)", dapp)

        # Create torrent
        fs = lt.file_storage()
        lt.add_files(fs, os.path.join(payloads_directory, dapp))
        t = lt.create_torrent(fs)

        if self.tracker_enable:
            for tracker in tracker_list:
                t.add_tracker(tracker, 0)

        lt.set_piece_hashes(t, payloads_directory)
        torrent = t.generate()

        # Create torrent file
        torrent_file_path = os.path.join(torrents_directory, dapp + ".torrent")
        f = open(torrent_file_path, "wb")
        f.write(lt.bencode(torrent))
        f.close()

        # Create magnet link
        torrent_info = lt.torrent_info(torrent_file_path)
        magnet_link = "magnet:?xt=urn:btih:%s&dn=%s" % (torrent_info.info_hash(), torrent_info.name())
        magnet_file = os.path.join(torrents_directory, dapp + ".magnet")
        f = open(magnet_file, "wb")
        f.write(magnet_link)
        f.close()

        self._logger.debug("transport: seeding torrent (%s)", dapp)

        # Seed torrent
        h = self.ses.add_torrent({'ti': torrent_info, 'save_path': payloads_directory, 'seed_mode': True})

        return {
            'info_hash': torrent_info.info_hash(),
            'name': torrent_info.name(),
        }
