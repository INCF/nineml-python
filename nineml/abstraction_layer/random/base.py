from nineml.abstraction_layer.components import BaseComponentClass
from ..base import BaseALObject


class ComponentClass(BaseComponentClass):

    writer_name = 'random'

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

    def __init__(self, name, reference_url):
        self.name = name
        self.reference_url = reference_url
