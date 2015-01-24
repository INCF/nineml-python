from .. import BaseALObject
from ..componentclass import ComponentClass


class Distribution(BaseALObject):

    defining_attributes = ()

    def __init__(self, standard_library, aliases=[]):
        self.standard_library = standard_library
        self.aliases = aliases

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_distribution(self, **kwargs)


class DistributionClass(ComponentClass):

    defining_attributes = ('name', '_parameters', 'distribution')

    def __init__(self, name, distribution, parameters=None):
        super(DistributionClass, self).__init__(
            name, parameters, main_block=distribution)

    @property
    def distribution(self):
        return self._main_block

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)
