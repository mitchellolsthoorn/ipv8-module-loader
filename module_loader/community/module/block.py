from __future__ import absolute_import

from ipv8.attestation.trustchain.block import TrustChainBlock

# Constants
MODULE_BLOCK_TYPE_VOTE = 'module_vote'
MODULE_BLOCK_TYPE_VOTE_KEY_CREATOR = 'creator'
MODULE_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH = 'content_hash'
MODULE_BLOCK_TYPE_VOTE_KEY_NAME = 'name'


class ModuleBlock(TrustChainBlock):
    # TODO: Add create 'module_created' block and let random peers cross sign it
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
        required_fields = [MODULE_BLOCK_TYPE_VOTE_KEY_CREATOR, MODULE_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH,
                           MODULE_BLOCK_TYPE_VOTE_KEY_NAME]
        if self.type != MODULE_BLOCK_TYPE_VOTE:
            return False
        if not ModuleBlock.has_fields(required_fields, self.transaction):
            return False
        if len(self.transaction) != len(required_fields):
            return False

        required_types = [(MODULE_BLOCK_TYPE_VOTE_KEY_CREATOR, bytes), (MODULE_BLOCK_TYPE_VOTE_KEY_CONTENT_HASH, str),
                          (MODULE_BLOCK_TYPE_VOTE_KEY_NAME, str)]

        if not ModuleBlock.has_required_types(required_types, self.transaction):
            return False

        return True
