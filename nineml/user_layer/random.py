from .components.base import BaseComponent


class RandomDistribution(BaseComponent):

    """
    Component representing a random number distribution, e.g. normal, gamma,
    binomial.
    """
    abstraction_layer_module = 'random'
