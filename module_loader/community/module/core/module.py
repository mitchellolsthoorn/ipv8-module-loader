from module_loader.community.module.core.module_identifier import ModuleIdentifier


class Module(object):

    def __init__(self, module_identifier, name, votes=0):
        super(Module, self).__init__()

        self._module_identifier = module_identifier  # type: ModuleIdentifier
        self._name = name  # type: str
        self._votes = votes  # type: int

    @property
    def id(self):
        return self._module_identifier

    @property
    def name(self):
        return self._name

    @property
    def votes(self):
        return self._votes

    def to_dict(self):
        return {
            'identifier': self._module_identifier.to_dict(),
            'name': self._name,
            'votes': self._votes,
        }

    def __str__(self):
        return "id: {0} - name: {1} - votes: {2}".format(self._module_identifier, self._name, self._votes)

    def __eq__(self, other):
        if not isinstance(other, Module):
            return False

        return self._module_identifier == other._module_identifier

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._module_identifier)
