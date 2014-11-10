from nineml.abstraction_layer.components import BaseComponentClass


class ComponentClass(BaseComponentClass):

    writer_name = 'random'

    def __init__(self, name, random_distribution, parameters=None):
        super(ComponentClass, self).__init__(name, parameters)
        self.random_distribution = random_distribution

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)


class RandomDistribution(object):

    def __init__(self, builtin_definition):
        self.builtin_definition = builtin_definition

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_randomdistribution(self, **kwargs)


class BuiltInRandomDistribution(RandomDistribution):

    def __init__(self, uncertml_definition):
        self.uncertml_definition = uncertml_definition
