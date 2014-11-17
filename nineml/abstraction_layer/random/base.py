from nineml.abstraction_layer.components import BaseComponentClass
from ..base import BaseALObject


class ComponentClass(BaseComponentClass):

    writer_name = 'random'
    defining_attributes = ('name', '_parameters', 'random_distribution')

    def __init__(self, name, random_distribution, parameters=None):
        super(ComponentClass, self).__init__(name, parameters)
        self.random_distribution = random_distribution

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)


class RandomDistribution(BaseALObject):

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_randomdistribution(self, **kwargs)


class StandardLibraryRandomDistribution(RandomDistribution):

    defining_attributes = ('name', 'webpage')

    def __init__(self, name, webpage):
        self.name = name
        self.webpage = webpage
