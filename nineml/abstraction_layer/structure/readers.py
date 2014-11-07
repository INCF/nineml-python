from lxml import etree

from nineml.exceptions import NineMLRuntimeError
from nineml.abstraction_layer.xmlns import NINEML
from nineml.abstraction_layer.components import Parameter
from nineml.abstraction_layer.dynamics.readers import XMLReader
from .base import ComponentClass


class XMLLoader(object):
    # for now we copy and modify the XMLLoader from the "dynamics" module
    # it would be better either to have a common base class, or to have
    # a single XMLLoader that worked for all AL modules.

    def __init__(self, context=None):
        self.context = context

    def load_all_componentclasses(self, xmlroot, xml_node_filename_map):
        self.components = []
        self.component_srcs = {}
        for comp_block in xmlroot.findall(NINEML + "ComponentClass"):
            component = self.load_componentclass(comp_block)

            self.components.append(component)
            self.component_srcs[component] = xml_node_filename_map[comp_block]

    def load_componentclass(self, element):

        blocks = ('Parameter', 'Structure')
        subnodes = self.loadBlocks(element, blocks=blocks)
        # structure = expect_single(subnodes["Structure"])
        structure = subnodes.get("structure", None)
        return ComponentClass(name=element.get('name'),
                              parameters=subnodes["Parameter"],
                              structure=structure)

    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=element.get('dimension'))

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
                    raise NineMLRuntimeError(err)

            res[tag].append(XMLLoader.tag_to_loader[tag](self, t))
        return res

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "Parameter": load_parameter,
        # "Structure": load_structure,
    }


class XMLReader(XMLReader):
    loader = XMLLoader

# 
# class XMLReader(object):  # temporary hack
# 
#     @classmethod
#     def read_component(cls, url):
#         # this is a temporary hack. The url is not resolved, but is a label.
#         if "2Dgrid" in url:
#             parameters = [Parameter(name="aspectRatioXY", dimension=None),
#                           Parameter(name="fillOrder", dimension=None),
#                           Parameter(name="dx", dimension="um"),
#                           Parameter(name="dy", dimension="um"),
#                           Parameter(name="x0", dimension="um"),
#                           Parameter(name="y0", dimension="um")]
#         else:
#             raise NotImplementedError()
#         return ComponentClass(url, parameters)
