"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
import os
from urllib2 import urlopen
from itertools import chain
from lxml import etree
from nineml.xmlns import E
from .visitors import ComponentVisitor
from ..dynamics import DynamicsClass
from ..ports import (PropertySendPort, PropertyReceivePort, IndexSendPort,
                     IndexReceivePort)
from ..expressions import Alias
from nineml.abstraction_layer.componentclass import Parameter
from nineml.annotations import annotate_xml, read_annotations
from ...utility import expect_single, filter_expect_single
from ...xmlns import NINEML, MATHML, nineml_namespace
from ...exceptions import NineMLRuntimeError


class BaseXMLLoader(object):

    """This class is used by XMLReader internally.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    def __init__(self, document=None):
        self.document = document

    def load_componentclasses(self, xmlroot, xml_node_filename_map):

        self.components = []
        self.component_srcs = {}
        for comp_block in xmlroot.find(NINEML + "ComponentClass"):
            component = self.load_componentclass(comp_block)

            self.components.append(component)
            self.component_srcs[component] = xml_node_filename_map[comp_block]

    def load_connectports(self, element):
        return element.get('source'), element.get('sink')

    def load_subnode(self, subnode):
        namespace = subnode.get('namespace')
        component_class = filter_expect_single(
            self.components, lambda c: c.name == subnode.get('node'))
        return namespace, component_class

    @read_annotations
    def load_componentclass(self, element):

        blocks = ('Parameter', 'AnalogSendPort', 'AnalogReceivePort',
                  'IndexSendPort', 'IndexReceivePort', 'AnalogReducePort',
                  'Dynamics', 'Subnode', 'ConnectPorts', 'Component')

        subnodes = self.loadBlocks(element, blocks=blocks)

        dynamics = expect_single(subnodes["Dynamics"])
        return DynamicsClass(
            name=element.get('name'),
            parameters=subnodes["Parameter"],
            ang_ports=chain(subnodes["AnalogSendPort"],
                               subnodes["AnalogReceivePort"],
                               subnodes["AnalogReducePort"]),
            index_ports=chain(subnodes["IndexSendPort"],
                              subnodes["IndexReceivePort"]),
            dynamics=dynamics,
            subnodes=dict(subnodes['Subnode']),
            portconnections=subnodes["ConnectPorts"])

    @read_annotations
    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_propertysendport(self, element):
        return PropertySendPort(
            name=element.get("name"),
            dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_propertyreceiveport(self, element):
        return PropertyReceivePort(
            name=element.get("name"),
            dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_indexsendport(self, element):
        return IndexSendPort(name=element.get('name'))

    @read_annotations
    def load_indexreceiveport(self, element):
        return IndexReceivePort(name=element.get('name'))

    @read_annotations
    def load_alias(self, element):
        name = element.get("name")
        rhs = self.load_single_internmaths_block(element)
        return Alias(lhs=name,
                               rhs=rhs)

    def load_single_internmaths_block(self, element, checkOnlyBlock=True):
        if checkOnlyBlock:
            elements = list(element.iterchildren(tag=etree.Element))
            if len(elements) != 1:
                print elements
                assert 0, 'Unexpected tags found'
        assert (len(element.find(MATHML + "MathML")) +
                len(element.find(NINEML + "MathInline"))) == 1
        if element.find(NINEML + "MathInline"):
            mblock = expect_single(element.find(NINEML +
                                                   'MathInline')).text.strip()
        elif element.find(MATHML + "MathML"):
            mblock = self.load_mathml(expect_single(element.find(MATHML +
                                                                    "MathML")))
        return mblock

    def load_mathml(self, mathml):
        raise NotImplementedError

    # These blocks map directly onto classes:
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

            if check_for_spurious_blocks and tag not in blocks:
                    err = "Unexpected Block tag: %s " % tag
                    err += '\n Expected: %s' % ','.join(blocks)
                    raise NineMLRuntimeError(err)

            res[tag].append(BaseXMLLoader.tag_to_loader[tag](self, t))
        return res

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "Parameter": load_parameter,
        "PropertySendPort": load_propertysendport,
        "PropertyReceivePort": load_propertyreceiveport,
        "IndexSendPort": load_indexsendport,
        "IndexReceivePort": load_indexreceiveport,
        "Alias": load_alias,
        "Subnode": load_subnode,
        "ConnectPorts": load_connectports,
    }


class BaseXMLReader(object):

    """A class that can read |COMPONENTCLASS| objects from a NineML XML file.
    """
    loader = BaseXMLLoader

    @classmethod
    def _load_include(cls, include_element, basedir, xml_node_filename_map):
        """Help function for replacing <Include> nodes.

        We replace the include node with the tree referenced
        by that filename. To do this, we load the file referenced,
        get  the elements in the root node, and copy them over to the place
        in the origintree where the originnode was. It is important that
        we preserve the order. Finy, we remove the <Include> element node.

        """

        filename = include_element.get('file')

        # Load the new XML
        included_xml = cls._load_nested_xml(
            filename=os.path.join(basedir, filename),
            xml_node_filename_map=xml_node_filename_map)

        # Insert it into the parent node:
        index_of_node = include_element.getparent().index(include_element)
        for i, newchild in enumerate(included_xml.getchildren()):
            include_element.getparent().insert(i + index_of_node, newchild)

        include_element.getparent().remove(include_element)

    @classmethod
    def _load_nested_xml(cls, filename, xml_node_filename_map):
        """ Load the XML, including   referenced Include files .

        We o populate a dictionary, ``xml_node_filename_map`` which maps each
        node to the name of the filename that it was originy in, so that when
        we load in single components from a file, which are hierachically and
        contain references to other components, we can find the components that
        were in the file specified.

        """

        if filename[:5] == "https":  # lxml only supports http and ftp
            doc = etree.parse(urlopen(filename))
        else:
            doc = etree.parse(filename)
        # Store the source filenames of  the nodes:
        for node in doc.getroot().getiterator():
            xml_node_filename_map[node] = filename

        root = doc.getroot()
        if root.nsmap[None] != nineml_namespace:
            errmsg = ("The XML namespace is not compatible with this version "
                      "of the NineML library. Expected {}, file contains {}")
            raise Exception(errmsg.format(nineml_namespace, root.nsmap[None]))

        # Recursively Load Include Nodes:
        for include_element in root.getiterator(tag=NINEML + 'Include'):
            cls._load_include(include_element=include_element,
                              basedir=os.path.dirname(filename),
                              xml_node_filename_map=xml_node_filename_map)
        return root

    @classmethod
    def read(cls, filename, component_name=None):
        """Reads a single |COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :param component_name: If the file contains more than one
            ComponentClass definition, this parameter must be provided as a
            ``string`` specifying which component to return, otherwise a
            NineMLRuntimeException will be raised.
        :rtype: Returns a |COMPONENTCLASS| object.
        """
        return cls.read_component(filename, component_name=component_name)

    @classmethod
    def read_component(cls, filename, component_name=None):
        """Reads a single |COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :param component_name: If the file contains more than one
            ComponentClass definition, this parameter must be provided as a
            ``string`` specifying which component to return, otherwise a
            NineMLRuntimeException will be raised.
        :rtype: Returns a |COMPONENTCLASS| object.
        """

        xml_node_filename_map = {}
        root = cls._load_nested_xml(
            filename=filename, xml_node_filename_map=xml_node_filename_map)

        loader = cls.loader()
        loader.load_componentclasses(
            xmlroot=root, xml_node_filename_map=xml_node_filename_map)

        if component_name is None:
            key_func = lambda c: loader.component_srcs[c] == filename
            return filter_expect_single(loader.components, key_func)

        else:
            key_func = lambda c: c.name == component_name
            return filter_expect_single(loader.components, key_func)

    @classmethod
    def read_components(cls, filename):
        """Reads a sever|COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :rtype: Returns a list of |COMPONENTCLASS| objects, for each
            <ComponentClass> node in the XML tree.

        """
        xml_node_filename_map = {}
        root = cls._load_nested_xml(filename, xml_node_filename_map)
        loader = cls.loader()
        loader.load_componentclasses(
            xmlroot=root, xml_node_filename_map=xml_node_filename_map)
        return loader.components


class BaseXMLWriter(ComponentVisitor):

    @classmethod
    def write(cls, component, file, flatten=True):  # @ReservedAssignment
        doc = cls.to_xml(component, flatten)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)

    @classmethod
    @annotate_xml
    def to_xml(cls, component):
        assert isinstance(component, DynamicsClass)
        component.standardize_unit_dimensions()
        xml = BaseXMLWriter().visit(component)
        xml = [BaseXMLWriter().visit_dimension(d) for d in component.dimensions
               if d is not None] + [xml]
        return E.NineML(*xml, xmlns=nineml_namespace)

    def visit_componentclass(self, comp_cls):
        elements = ([p.accept_visitor(self) for p in comp_cls.property_ports] +
                    [p.accept_visitor(self) for p in comp_cls.index_ports] +
                    [p.accept_visitor(self) for p in comp_cls.parameters] +
                    [comp_cls.dynamics.accept_visitor(self)])
        return E('ComponentClass', *elements, name=comp_cls.name)

    @annotate_xml
    def visit_parameter(self, parameter):
        return E('Parameter',
                 name=parameter.name,
                 dimension=parameter.dimension.name)

    @annotate_xml
    def visit_propertyreceiveport(self, port):
        return E('PropertyReceivePort', name=port.name,
                 dimension=port.dimension.name)

    @annotate_xml
    def visit_propertysendport(self, port):
        return E('PropertySendPort', name=port.name,
                 dimension=port.dimension.name)

    @annotate_xml
    def visit_indexsendport(self, port):
        return E('IndexSendPort', name=port.name)

    @annotate_xml
    def visit_indexreceiveport(self, port):
        return E('IndexReceivePort', name=port.name)

    @annotate_xml
    def visit_dimension(self, dimension):
        kwargs = {'name': dimension.name}
        kwargs.update(dict((k, str(v)) for k, v in dimension._dims.items()))
        return E('Dimension')

    @annotate_xml
    def visit_alias(self, alias):
        return E('Alias',
                 E("MathInline", alias.rhs),
                 name=alias.lhs)
