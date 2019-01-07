from block import DAppBlock
from pyipv8.ipv8.attestation.trustchain.listener import BlockListener
from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8.peer import Peer


class DAppCommunity(Community, BlockListener):
    # Register this community with a master peer.
    # This peer defines the service identifier of this community.
    # Other peers will connect to this community based on the sha-1
    # hash of this peer's public key.
    master_peer = Peer("3081a7301006072a8648ce3d020106052b810400270381920004030d4d2d1fc98e2e3a7b0127acffbbc1aade7209"
                       "55b6a3c8b4de1a25686f20b6e150591f1251252c4cd30bfaa8ca5f1d2c68327cbef939958c94d1a441c20b10acd9"
                       "c53e5c9023a6011d626e69290a4ef98c2588ab1eb2ca9a3fb6f08042e1c93c9bad60bbb0f33fc156924e3914be9b"
                       "d11d702fe1ab307c40634e97d476462d669ebc4a39c5dd10eb58ab2d8a86c690".decode('hex'))

    BLOCK_CLASS = DAppBlock
    voted_dapps = []

    def __init__(self, my_peer, endpoint, network, **kwargs):
        super(DAppCommunity, self).__init__(my_peer, endpoint, network)
        self.trustchain = kwargs.pop('trustchain')
        self.trustchain.add_listener(self, ['vote'])

    def should_sign(self, block):
        if block.type == "vote":
            return True
        else:
            return False

    def received_block(self, block):
        if block.type == "vote":
            self.process_vote_block(block)

    def process_vote_block(self, block):
        if not block.is_valid_vote_block:
            print "Invalid vote block received!"
            return

        tx_dict = block.transaction
        info_hash = tx_dict['info_hash']
        name = tx_dict['name']
        print "Vote received for dapp with info_hash {0} and name {1}!".format(info_hash, name)
        if info_hash in self.voted_dapps:
            pass
        else:
            self.sign_dapp(info_hash, name)


    def sign_dapp(self, info_hash, name):
        tx_dict = {
            "info_hash": info_hash,
            "name": name
        }
        print "Voted for dapp with info_hash {0} and name {1}!".format(info_hash, name)
        self.voted_dapps.append(info_hash)
        return self.trustchain.self_sign_block(block_type='vote', transaction=tx_dict)

    def create_dapp(self):
        self.sign_dapp("9626a56c551c916f5cea40c786b5dc02faf65917", "execute")
