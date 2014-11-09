from nineml.abstraction_layer.components import BaseComponentClass


class ComponentClass(BaseComponentClass):

    def __init__(self, name, random_distribution, parameters=None):
        super(ComponentClass, self).__init__(name, parameters)
        self.random_distribution = random_distribution


class RandomDistribution(object):

    def __init__(self, builtin_definition):
        self.builtin_definition = builtin_definition
