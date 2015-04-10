from .. import BaseALObject
from ..componentclass import ComponentClass


class RandomDistributionBlock(BaseALObject):

    defining_attributes = ('standard_library',)

    def __init__(self, standard_library):
        self.standard_library = standard_library

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_randomdistributionblock(self, **kwargs)


class RandomDistributionClass(ComponentClass):

    defining_attributes = ('name', '_parameters', '_main_block')

    def __init__(self, name, randomdistributionblock, parameters=None):
        super(RandomDistributionClass, self).__init__(
            name, parameters, main_block=randomdistributionblock)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)
