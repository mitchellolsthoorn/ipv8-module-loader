from __future__ import absolute_import
from twisted.internet import reactor
from twisted.internet.task import deferLater

from loader.community.dapp.community import DAppCommunity
from ipv8.attestation.trustchain.community import TrustChainTestnetCommunity
from ipv8.configuration import get_default_configuration
from ipv8.keyvault.crypto import ECCrypto
from ipv8.peer import Peer
from ipv8.peerdiscovery.discovery import EdgeWalk, RandomWalk
from ipv8_service import IPv8

import twisted
twisted.internet.base.DelayedCall.debug = True

for i in [1, 2]:
    configuration = get_default_configuration()
    configuration['address'] = '0.0.0.0'
    configuration['port'] = 8090 + i
    configuration['keys'] = []
    configuration['overlays'] = []
    ipv8 = IPv8(configuration)
    #my_peer = Peer(ECCrypto().generate_key(u"medium"))
    trustchain_peer = Peer(ECCrypto().generate_key(u"curve25519"))
    trustchain_community = TrustChainTestnetCommunity(trustchain_peer, ipv8.endpoint, ipv8.network, working_directory='./'+str(i))
    ipv8.overlays.append(trustchain_community)
    ipv8.strategies.append((EdgeWalk(trustchain_community), 10))
    dapp_community = DAppCommunity(trustchain_peer, ipv8.endpoint, ipv8.network, trustchain=trustchain_community)
    ipv8.overlays.append(dapp_community)
    ipv8.strategies.append((RandomWalk(dapp_community), 2))

    if i == 2:
        deferLater(reactor, 5, dapp_community.create_dapp)

if __name__ == "__main__":
    reactor.run()
