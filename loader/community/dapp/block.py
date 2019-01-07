from pyipv8.ipv8.attestation.trustchain.block import TrustChainBlock


class DAppBlock(TrustChainBlock):

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
        required_fields = ['info_hash', 'name']
        if self.type != "vote":
            return False
        if not DAppBlock.has_fields(required_fields, self.transaction):
            return False
        if len(self.transaction) != len(required_fields):
            return False

        required_types = [('info_hash', str), ('name', str)]

        if not DAppBlock.has_required_types(required_types, self.transaction):
            return False

        return True
