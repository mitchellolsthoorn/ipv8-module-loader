from loader.community.dapp.core.dapp_identifier import DAppIdentifier


class DApp(object):

    def __init__(self, dapp_identifier, name, votes=0):
        super(DApp, self).__init__()

        self._dapp_identifier = dapp_identifier  # type: DAppIdentifier
        self._name = name  # type: str
        self._votes = votes  # type: int

    @property
    def id(self):
        return self._dapp_identifier

    @property
    def name(self):
        return self._name

    @property
    def votes(self):
        return self._votes

    def to_dict(self):
        return {
            'identifier': self._dapp_identifier.to_dict(),
            'name': self._name,
            'votes': self._votes,
        }

    def __str__(self):
        return "id: {0} - name: {1} - votes: {2}".format(self._dapp_identifier, self._name, self._votes)

    def __eq__(self, other):
        if not isinstance(other, DApp):
            return False

        return self._dapp_identifier == other._dapp_identifier

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._dapp_identifier)
