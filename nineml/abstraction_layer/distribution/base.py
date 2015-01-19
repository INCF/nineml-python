from ..base import BaseComponentClass, BaseALObject


class DistributionClass(BaseComponentClass):

    writer_name = 'random'
    defining_attributes = ('name', '_parameters', 'distribution')

    def __init__(self, name, random_distribution, parameters=None):
        super(BaseComponentClass, self).__init__(name, parameters)
        self.random_distribution = random_distribution

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)


class Distribution(BaseALObject):

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_randomdistribution(self, **kwargs)
