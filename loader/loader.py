import importlib
import os
import sys
import time

import libtorrent as lt

from constants import DAPPS_DIR, EXECUTE_FILE

DHT_ENABLE = False
LSD_ENABLE = True

use_magnet_link = bool(int(sys.argv[1]))
torrent_data = sys.argv[2]

# Create libtorrent session
ses = lt.session()
ses.listen_on(6881, 6891)

if DHT_ENABLE:
    # Enable and bootstrap DHT
    ses.add_dht_router("router.utorrent.com", 6881)
    ses.add_dht_router("router.bittorrent.com", 6881)
    ses.add_dht_router("dht.transmissionbt.com", 6881)
    ses.start_dht()

if LSD_ENABLE:
    # Enable LSD
    ses.start_lsd()

if use_magnet_link:
    params = {'save_path': DAPPS_DIR}
    h = lt.add_magnet_uri(ses, torrent_data, params)
else:
    e = lt.bdecode(open(torrent_data, 'rb').read())
    info = lt.torrent_info(e)
    params = {'save_path': DAPPS_DIR, 'storage_mode': lt.storage_mode_t.storage_mode_sparse, 'ti': info}
    h = ses.add_torrent(params)

print 'checking torrent: ', h.name()

while (not h.has_metadata()):
    time.sleep(1)

print 'metadata complete'

torrent_info = h.get_torrent_info()
print 'torrent infohash: ', torrent_info.info_hash()
print 'starting torrent: ', torrent_info.name()

s = h.status()
while (not s.is_seeding):
    s = h.status()

    state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
    print '%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
          (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, state_str[s.state])

    time.sleep(1)

print 'torrent: ', h.name(), ' complete'


def load_dapps():
    dapps = []
    modules = []

    dapp_directory = os.listdir(DAPPS_DIR)

    for dapp in dapp_directory:
        if dapp.startswith('__'):
            continue

        dapp_path = os.path.join(os.path.abspath('.'), DAPPS_DIR, dapp)
        dapp_executable = os.path.join(dapp_path, EXECUTE_FILE)
        if os.path.isdir(dapp_path) and os.path.isfile(dapp_executable):
            print 'dapp detected: ' + dapp
            dapps.append(dapp)

            modules.append(importlib.import_module(DAPPS_DIR + '.' + dapp + '.execute'))
        else:
            print 'invalid dapp detected: ' + dapp

    return dapps, modules


print '\nloading dApps\n-----'
load_dapps()
print '-----\nloading dApps complete'
