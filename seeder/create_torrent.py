import os
import sys

import libtorrent as lt

from constants import PAYLOADS_DIR, TORRENTS_DIR

payload = sys.argv[1]
payload_path = os.path.join(PAYLOADS_DIR, payload)
torrent_file_path = os.path.join(TORRENTS_DIR, payload + ".torrent")
magnet_file = os.path.join(TORRENTS_DIR, payload + ".magnet")

enable_trackers = False
magnet_link = True

tracker_list = ['udp://tracker.publicbt.com:80/announce', 'udp://tracker.openbittorrent.com:80/announce']

# Create torrent
fs = lt.file_storage()
lt.add_files(fs, payload_path)
t = lt.create_torrent(fs)

if enable_trackers:
    for tracker in tracker_list:
        t.add_tracker(tracker, 0)

lt.set_piece_hashes(t, "./payloads")
torrent = t.generate()
f = open(torrent_file_path, "wb")
f.write(lt.bencode(torrent))
f.close()

# Create magnet link
torrent_info = lt.torrent_info(torrent_file_path)
magnet_link = "magnet:?xt=urn:btih:%s&dn=%s" % (torrent_info.info_hash(), torrent_info.name())

f = open(magnet_file, "wb")
f.write(magnet_link)
f.close()

print magnet_link
