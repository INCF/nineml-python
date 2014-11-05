
from nineml.abstraction_layer.components import Parameter
from .base import ComponentClass


class XMLLoader(object):

    def load_componentclass(self, element):
        raise NotImplementedError


class XMLReader(object):

    @classmethod
    def read_component(cls, url):
        # this is a temporary hack. The url is not resolved, but is a label.
        if "normal_distribution" in url:
            parameters = [Parameter(name="standardDeviation", dimension=None),
                          Parameter(name="mean", dimension=None)]
        elif "uniform_distribution" in url:
            parameters = [Parameter(name="lowerBound", dimension=None),
                          Parameter(name="upperBound", dimension=None)]
        elif "exponential_distribution" in url:
            parameters = [Parameter(name="beta", dimension=None)]
        else:
            raise Exception("Random distribution %s not supported" % url)
        return ComponentClass(url, parameters)
