import os
import re
import sys
import time

import importlib
import libtorrent as lt

DHT_enable = False
LSD_enable = True
magnet_link = True
magnet_link_url = "magnet:?xt=urn:btih:664aa08a1ebb1224baf7a70e32351464452606f4&dn=execute.py"

dapps_location = "dapps"

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

if magnet_link:
    params = {'save_path': dapps_location}
    link = magnet_link_url
    h = lt.add_magnet_uri(ses, link, params)
else:
    e = lt.bdecode(open("test.torrent", 'rb').read())
    info = lt.torrent_info(e)
    params = {'save_path': dapps_location, 'storage_mode': lt.storage_mode_t.storage_mode_sparse, 'ti': info}
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

def load_plugins():
    pysearchre = re.compile('.py$', re.IGNORECASE)
    pluginfiles = filter(pysearchre.search, os.listdir(os.path.join(os.path.dirname(__file__), dapps_location)))
    form_module = lambda fp: '.' + os.path.splitext(fp)[0]
    plugins = map(form_module, pluginfiles)

    # import parent module / namespace
    importlib.import_module(dapps_location)
    modules = []
    for plugin in plugins:
             if not plugin.startswith('__'):
                 modules.append(importlib.import_module(plugin, package=dapps_location))

    return modules

load_plugins()
