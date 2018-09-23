import libtorrent as lt
import sys
import time

DHT_enable = False
LSD_enable = True

# Create libtorrent session
ses = lt.session()
ses.listen_on(6881, 6891)

if DHT_enable:
    # Enable and bootstrap DHT
    ses.add_dht_router("router.utorrent.com", 6881)
    ses.add_dht_router("router.bittorrent.com", 6881)
    ses.add_dht_router("dht.transmissionbt.com", 6881)
    ses.start_dht()

if LSD_enable:
    # Enable LSD
    ses.start_lsd()

# Seed torrent
ses = lt.session()
ses.listen_on(6881, 6891)
torrent_info = lt.torrent_info('test.torrent')
h = ses.add_torrent({'ti': torrent_info, 'save_path': '.', 'seed_mode': True})

print 'Total size: ', h.status().total_wanted
print 'Name: ', h.name()

while True:
    s = h.status()
    state_str = ['queued', 'checking', 'downloading metadata', \
                 'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']

    print('\r%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
          (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, state_str[s.state]))
    sys.stdout.flush()

    time.sleep(1)
