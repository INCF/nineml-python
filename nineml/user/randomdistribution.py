from nineml.user.component import Component


class RandomDistributionProperties(Component):
    """
    Component representing a random number randomdistribution, e.g. normal,
    gamma, binomial.

    *Example*::

        example goes here
    """
    nineml_type = 'RandomDistributionProperties'

    @property
    def standard_library(self):
        return self.component_class.standard_library

    def get_nineml_type(self):
        return self.nineml_type
