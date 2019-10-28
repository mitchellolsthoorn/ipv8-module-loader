from binascii import hexlify


class ModuleIdentifier(object):

    def __init__(self, creator, content_hash):
        super(ModuleIdentifier, self).__init__()

        self._creator = creator
        self._content_hash = content_hash

    @property
    def creator(self):
        return self._creator

    @property
    def content_hash(self):
        return self._content_hash

    def to_dict(self):
        return {
            'creator': hexlify(self._creator),
            'content_hash': self._content_hash
        }

    def __str__(self):
        return "{0}.{1}".format(hexlify(self._creator), self._content_hash)

    def __eq__(self, other):
        if not isinstance(other, ModuleIdentifier):
            return False

        return self._creator == other._creator and self._content_hash == other._content_hash

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self._creator, self._content_hash))
