import libtorrent as lt
import os

payload_file = os.path.join("execute.py")
torrent_file = os.path.join("torrents", "prototype_dapp.torrent")

enable_trackers = False
magnet_link = True

tracker_list = ['udp://tracker.publicbt.com:80/announce', 'udp://tracker.openbittorrent.com:80/announce']

# Create torrent
fs = lt.file_storage()
lt.add_files(fs, payload_file)
t = lt.create_torrent(fs)

if enable_trackers:
    for tracker in tracker_list:
        t.add_tracker(tracker, 0)

t.set_creator('libtorrent %s' % lt.version)
lt.set_piece_hashes(t, ".")
torrent = t.generate()
f = open(torrent_file, "wb")
f.write(lt.bencode(torrent))
f.close()

# Create magnet link
torrent_info = lt.torrent_info(torrent_file)
print "magnet:?xt=urn:btih:%s&dn=%s" % (torrent_info.info_hash(), torrent_info.name())