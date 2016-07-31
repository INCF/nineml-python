"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
import os
from urllib2 import urlopen
from lxml import etree
from itertools import chain
from nineml.xmlns import E
from . import ComponentVisitor
from ...expressions import Alias, Constant
from nineml.abstraction.componentclass.base import Parameter
from nineml.annotations import annotate_xml, read_annotations
from nineml.utils import expect_single, filter_expect_single
from nineml.xmlns import NINEML, MATHML, nineml_namespace
from nineml.exceptions import NineMLRuntimeError, handle_xml_exceptions


class ComponentClassXMLLoader(object):

    """This class is used by XMLReader internally.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    def __init__(self, document=None):
        if document is None:
            document = Document()
        self.document = document

    def load_connectports(self, element):
        return element.attrib['source'], element.attrib['sink']

    @read_annotations
    @handle_xml_exceptions
    def load_parameter(self, element):
        return Parameter(name=element.attrib['name'],
                         dimension=self.document[element.attrib['dimension']])

    @read_annotations
    @handle_xml_exceptions
    def load_alias(self, element):
        name = element.attrib['name']
        rhs = self.load_single_internmaths_block(element)
        return Alias(lhs=name, rhs=rhs)

    @read_annotations
    @handle_xml_exceptions
    def load_constant(self, element):
        return Constant(name=element.attrib['name'],
                        value=float(element.text),
                        units=self.document[element.attrib['units']])

    def load_single_internmaths_block(self, element, checkOnlyBlock=True):
        if checkOnlyBlock:
            elements = list(element.iterchildren(tag=etree.Element))
            if len(elements) != 1:
                raise NineMLRuntimeError(
                    "Unexpected tags found '{}'"
                    .format("', '".join(e.tag for e in elements)))
        assert (len(element.findall(MATHML + "MathML")) +
                len(element.findall(NINEML + "MathInline"))) == 1
        if element.find(NINEML + "MathInline") is not None:
            mblock = expect_single(
                element.findall(NINEML + 'MathInline')).text.strip()
        elif element.find(MATHML + "MathML") is not None:
            mblock = self.load_mathml(
                expect_single(element.find(MATHML + "MathML")))
        return mblock

    def load_mathml(self, mathml):
        raise NotImplementedError

    def _load_blocks(self, element, block_names):
        """
        Creates a dictionary that maps class-types to instantiated objects
        """
        # Initialise loaded objects with empty lists
        loaded_objects = dict((block, []) for block in block_names)

        for t in element.iterchildren(tag=etree.Element):
            # Strip namespace
            tag = t.tag[len(NINEML):] if t.tag.startswith(NINEML) else t.tag
            if tag not in block_names:
                raise NineMLRuntimeError(
                    "Unexpected element {} was found in {} block in '{}'"
                    " (expected tags are: '{}')"
                    .format(tag, element.tag[len(NINEML):], self.document.url,
                            "', '".join(block_names)))
            loaded_objects[tag].append(self.tag_to_loader[tag](self, t))
        return loaded_objects

    tag_to_loader = {
        "Parameter": load_parameter,
        "Alias": load_alias,
        "Constant": load_constant
    }


class ComponentClassXMLWriter(ComponentVisitor):

    @annotate_xml
    def visit_parameter(self, parameter):
        return E(Parameter.element_name,
                 name=parameter.name,
                 dimension=parameter.dimension.name)

    @annotate_xml
    def visit_alias(self, alias):
        return E(Alias.element_name,
                 E("MathInline", alias.rhs_cstr),
                 name=alias.lhs)

    @annotate_xml
    def visit_constant(self, constant):
        return E('Constant', str(constant.value),
                 name=constant.name,
                 units=constant.units.name)

# 
# class ComponentClassXMLReader(object):
# 
#     """A class that can read |COMPONENTCLASS| objects from a NineML XML file.
#     """
#     loader = ComponentClassXMLLoader
# 
#     @classmethod
#     def _load_include(cls, include_element, basedir, xml_node_filename_map):
#         """Help function for replacing <Include> nodes.
# 
#         We replace the include node with the tree referenced
#         by that filename. To do this, we load the file referenced,
#         get  the elements in the root node, and copy them over to the place
#         in the origintree where the originnode was. It is important that
#         we preserve the order. Finy, we remove the <Include> element node.
# 
#         """
# 
#         filename = include_element.get('file')
# 
#         # Load the new XML
#         included_xml = cls._load_nested_xml(
#             filename=os.path.join(basedir, filename),
#             xml_node_filename_map=xml_node_filename_map)
# 
#         # Insert it into the parent node:
#         index_of_node = include_element.getparent().index(include_element)
#         for i, newchild in enumerate(included_xml.getchildren()):
#             include_element.getparent().insert(i + index_of_node, newchild)
# 
#         include_element.getparent().remove(include_element)
# 
#     @classmethod
#     def _load_nested_xml(cls, filename, xml_node_filename_map):
#         """ Load the XML, including   referenced Include files .
# 
#         We o populate a dictionary, ``xml_node_filename_map`` which maps each
#         node to the name of the filename that it was originy in, so that when
#         we load in single components from a file, which are hierachically and
#         contain references to other components, we can find the components that
#         were in the file specified.
# 
#         """
# 
#         if filename[:5] == "https":  # lxml only supports http and ftp
#             doc = etree.parse(urlopen(filename))
#         else:
#             doc = etree.parse(filename)
#         # Store the source filenames of  the nodes:
#         for node in doc.getroot().getiterator():
#             xml_node_filename_map[node] = filename
# 
#         root = doc.getroot()
#         if root.nsmap[None] != nineml_namespace:
#             errmsg = ("The XML namespace is not compatible with this version "
#                       "of the NineML library. Expected {}, file contains {}")
#             raise Exception(errmsg.format(nineml_namespace, root.nsmap[None]))
# 
#         # Recursively Load Include Nodes:
#         for include_element in root.getiterator(tag=NINEML + 'Include'):
#             cls._load_include(include_element=include_element,
#                               basedir=os.path.dirname(filename),
#                               xml_node_filename_map=xml_node_filename_map)
#         return root
# 
#     @classmethod
#     def read(cls, filename, component_name=None):
#         """Reads a single |COMPONENTCLASS| object from a filename.
# 
#         :param filename: The name of the file.
#         :param component_name: If the file contains more than one
#             ComponentClass definition, this parameter must be provided as a
#             ``string`` specifying which component to return, otherwise a
#             NineMLRuntimeException will be raised.
#         :rtype: Returns a |COMPONENTCLASS| object.
#         """
#         return cls.read_component(filename, component_name=component_name)
# 
#     @classmethod
#     def read_component(cls, filename, component_name=None):
#         """Reads a single |COMPONENTCLASS| object from a filename.
# 
#         :param filename: The name of the file.
#         :param component_name: If the file contains more than one
#             ComponentClass definition, this parameter must be provided as a
#             ``string`` specifying which component to return, otherwise a
#             NineMLRuntimeException will be raised.
#         :rtype: Returns a |COMPONENTCLASS| object.
#         """
# 
#         xml_node_filename_map = {}
#         root = cls._load_nested_xml(
#             filename=filename, xml_node_filename_map=xml_node_filename_map)
# 
#         loader = cls.loader()
#         loader.load_componentclasses(
#             xmlroot=root, xml_node_filename_map=xml_node_filename_map)
# 
#         if component_name is None:
#             key_func = lambda c: loader.component_srcs[c] == filename
#             return filter_expect_single(loader.components, key_func)
# 
#         else:
#             key_func = lambda c: c.name == component_name
#             return filter_expect_single(loader.components, key_func)
# 
#     @classmethod
#     def read_components(cls, filename):
#         """Reads a sever|COMPONENTCLASS| object from a filename.
# 
#         :param filename: The name of the file.
#         :rtype: Returns a list of |COMPONENTCLASS| objects, for each
#             <ComponentClass> node in the XML tree.
# 
#         """
#         xml_node_filename_map = {}
#         root = cls._load_nested_xml(filename, xml_node_filename_map)
#         loader = cls.loader()
#         loader.load_componentclasses(
#             xmlroot=root, xml_node_filename_map=xml_node_filename_map)
#         return loader.components

from nineml.document import Document
