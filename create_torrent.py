import libtorrent as lt

enable_trackers = False
magnet_link = True

tracker_list = ['udp://tracker.publicbt.com:80/announce', 'udp://tracker.openbittorrent.com:80/announce']

# Create torrent
fs = lt.file_storage()
lt.add_files(fs, "./test.txt")
t = lt.create_torrent(fs)

if enable_trackers:
    for tracker in tracker_list:
        t.add_tracker(tracker, 0)

t.set_creator('libtorrent %s' % lt.version)
t.set_comment("test")
lt.set_piece_hashes(t, ".")
torrent = t.generate()
f = open("test.torrent", "wb")
f.write(lt.bencode(torrent))
f.close()

# Create magnet link
torrent_info = lt.torrent_info('test.torrent')
print "magnet:?xt=urn:btih:%s&dn=%s" % (torrent_info.info_hash(), torrent_info.name())