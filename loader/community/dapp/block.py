from __future__ import absolute_import

from ipv8.attestation.trustchain.block import TrustChainBlock

# Constants
DAPP_BLOCK_TYPE_VOTE = 'dapp_vote'
DAPP_BLOCK_TYPE_VOTE_KEY_CREATOR = 'creator'
DAPP_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH = 'content_hash'
DAPP_BLOCK_TYPE_VOTE_KEY_NAME = 'name'


class DAppBlock(TrustChainBlock):
    # TODO: Add create 'dapp_created' block and let random peers cross sign it
    @staticmethod
    def has_fields(needles, haystack):
        for needle in needles:
            if needle not in haystack:
                return False
        return True

    @staticmethod
    def has_required_types(types, container):
        for key, required_type in types:
            if not isinstance(container[key], required_type):
                return False
        return True

    def is_valid_vote_block(self):
        required_fields = [DAPP_BLOCK_TYPE_VOTE_KEY_CREATOR, DAPP_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH,
                           DAPP_BLOCK_TYPE_VOTE_KEY_NAME]
        if self.type != DAPP_BLOCK_TYPE_VOTE:
            return False
        if not DAppBlock.has_fields(required_fields, self.transaction):
            return False
        if len(self.transaction) != len(required_fields):
            return False

        required_types = [(DAPP_BLOCK_TYPE_VOTE_KEY_CREATOR, bytes), (DAPP_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH, str),
                          (DAPP_BLOCK_TYPE_VOTE_KEY_NAME, str)]

        if not DAppBlock.has_required_types(required_types, self.transaction):
            return False

        return True
