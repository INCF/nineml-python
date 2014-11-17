from lxml import etree
import nineml
from nineml.utility import expect_single, filter_expect_single
from nineml.abstraction_layer.xmlns import NINEML
from nineml.abstraction_layer.components import Parameter
from .base import ComponentClass, StandardLibraryRandomDistribution


class XMLLoader(object):

    def __init__(self, context=None):
        self.context = context

    def load_subnode(self, subnode):
        namespace = subnode.get('namespace')
        component = filter_expect_single(self.components,
                                       lambda c: c.name == subnode.get('node'))
        return namespace, component

    def load_componentclass(self, element):

        blocks = ('Parameter', 'RandomDistribution')

        subnodes = self.loadBlocks(element, blocks=blocks)

        random_distribution = expect_single(subnodes["RandomDistribution"])
        return ComponentClass(name=element.get('name'),
                              random_distribution=random_distribution,
                              parameters=subnodes["Parameter"])

    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=self.context[element.get('dimension')])

    def load_randomdistribution(self, element):
        blocks = ('StandardLibrary',)
        subnodes = self.loadBlocks(element, blocks=blocks)
        #TODO: Only implemented built-in distributions at this stage
        return expect_single(subnodes['StandardLibrary'])

    def load_standardlibrary(self, element):
        return StandardLibraryRandomDistribution(name=element.text,
                                                webpage=element.get('webpage'))

    # These blocks map directly in to classes:
    def loadBlocks(self, element, blocks=None, check_for_spurious_blocks=True):
        """
        Creates a dictionary that maps class-types to instantiated objects
        """

        res = dict((block, []) for block in blocks)

        for t in element.iterchildren(tag=etree.Element):
            if t.tag.startswith(NINEML):
                tag = t.tag[len(NINEML):]
            else:
                tag = t.tag

            if check_for_spurious_blocks and not tag in blocks:
                    err = "Unexpected Block tag: %s " % tag
                    err += '\n Expected: %s' % ','.join(blocks)
                    raise nineml.exceptions.NineMLRuntimeError(err)

            res[tag].append(XMLLoader.tag_to_loader[tag](self, t))
        return res

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "RandomDistribution": load_randomdistribution,
        "StandardLibrary": load_standardlibrary,
        "Parameter": load_parameter,
    }
