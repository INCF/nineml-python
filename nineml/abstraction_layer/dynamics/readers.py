"""
This file defines classes for reading NineML files.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""


import os
from urllib2 import urlopen
from lxml import etree
import quantities as pq

import nineml
from nineml.utility import expect_single, filter_expect_single
from nineml.abstraction_layer.xmlns import NINEML, MATHML, nineml_namespace
from nineml.abstraction_layer.components import Parameter
from nineml.abstraction_layer.dynamics import component as al

__all__ = ['XMLReader']


class XMLLoader(object):

    """This class is used by XMLReader internally.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It also records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    # FIXME: TGC 1/11/14 - I am implementing a general NineML root class
    #                      that will be able to read both User Layer and
    #                      Abstraction layer elements that will make this
    #                      obsolete I think (will create a GitHub issue about
    #                      this when I get back to the internet)
    def load_all_componentclasses(self, xmlroot, xml_node_filename_map):

        self.components = []
        self.component_srcs = {}
        for comp_block in xmlroot.findall(NINEML + "ComponentClass"):
            component = self.load_componentclass(comp_block)

            self.components.append(component)
            self.component_srcs[component] = xml_node_filename_map[comp_block]

    def load_connectports(self, element):
        return element.get('source'), element.get('sink')

    def load_subnode(self, subnode):
        namespace = subnode.get('namespace')
        component = filter_expect_single(self.components,
                                       lambda c: c.name == subnode.get('node'))
        return namespace, component

    def load_componentclass(self, element):

        blocks = ('Parameter', 'AnalogSendPort', 'AnalogReceivePort',
                  'EventSendPort', 'EventReceivePort', 'AnalogReducePort',
                  'Dynamics', 'Subnode', 'ConnectPorts', 'Component')

        subnodes = self.loadBlocks(element, blocks=blocks)

        dynamics = expect_single(subnodes["Dynamics"])
        return al.ComponentClass(
                         name=element.get('name'),
                         parameters=subnodes["Parameter"],
                         analog_send_ports=subnodes["AnalogSendPort"],
                         analog_receive_ports=subnodes["AnalogReceivePort"],
                         analog_reduce_ports=subnodes["AnalogReducePort"],
                         event_send_ports=subnodes["EventSendPort"],
                         event_receive_ports=subnodes["EventReceivePort"],
                         dynamics=dynamics,
                         subnodes=dict(subnodes['Subnode']),
                         portconnections=subnodes["ConnectPorts"])

#     def load_subcomponent(self, element):
#         return al.SubComponent(name=element.get('name'))

    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=element.get('dimension'))

    def load_eventsendport(self, element):
        return al.EventSendPort(name=element.get('name'))

    def load_eventreceiveport(self, element):
        return al.EventReceivePort(name=element.get('name'))

    def load_analogsendport(self, element):
        return al.AnalogSendPort(name=element.get("name"),
                                 dimension=element.get('dimension'))

    def load_analogreceiveport(self, element):
        return al.AnalogReceivePort(name=element.get("name"),
                                    dimension=element.get('dimension'))

    def load_analogreduceport(self, element):
        return al.AnalogReducePort(name=element.get('name'),
                                  dimension=element.get('dimension'),
                                  reduce_op=element.get("reduce_op"))

    def load_dynamics(self, element):
        subblocks = ('Regime', 'Alias', 'StateVariable')
        subnodes = self.loadBlocks(element, blocks=subblocks)

        return al.Dynamics(regimes=subnodes["Regime"],
                                  aliases=subnodes["Alias"],
                                  state_variables=subnodes["StateVariable"])

    def load_regime(self, element):
        subblocks = ('TimeDerivative', 'OnCondition', 'OnEvent')
        subnodes = self.loadBlocks(element, blocks=subblocks)
        transitions = subnodes["OnEvent"] + subnodes['OnCondition']
        return al.Regime(name=element.get('name'),
                                time_derivatives=subnodes["TimeDerivative"],
                                transitions=transitions)

    def load_statevariable(self, element):
        name = element.get("name")
        dimension = element.get('dimension')
        return al.StateVariable(name=name, dimension=dimension)

    def load_timederivative(self, element):
        variable = element.get("variable")
        expr = self.load_single_internal_maths_block(element)
        return al.TimeDerivative(dependent_variable=variable,
                                        rhs=expr)

    def load_alias(self, element):
        name = element.get("name")
        rhs = self.load_single_internal_maths_block(element)
        return al.Alias(lhs=name,
                               rhs=rhs)

    def load_oncondition(self, element):
        subblocks = ('Trigger', 'StateAssignment', 'EventOut')
        subnodes = self.loadBlocks(element, blocks=subblocks)
        target_regime = element.get('target_regime', None)
        trigger = expect_single(subnodes["Trigger"])

        return al.OnCondition(trigger=trigger,
                              state_assignments=subnodes["StateAssignment"],
                              event_outputs=subnodes["EventOut"],
                              target_regime_name=target_regime)

    def load_onevent(self, element):
        subblocks = ('StateAssignment', 'EventOut')
        subnodes = self.loadBlocks(element, blocks=subblocks)
        target_regime_name = element.get('target_regime', None)

        return al.OnEvent(src_port_name=element.get('port'),
                          state_assignments=subnodes["StateAssignment"],
                          event_outputs=subnodes["EventOut"],
                          target_regime_name=target_regime_name)

    def load_trigger(self, element):
        return self.load_single_internal_maths_block(element)

    def load_stateassignment(self, element):
        lhs = element.get('variable')
        rhs = self.load_single_internal_maths_block(element)
        return al.StateAssignment(lhs=lhs, rhs=rhs)

    def load_eventout(self, element):
        port_name = element.get('port')
        return al.OutputEvent(port_name=port_name)

    def load_single_internal_maths_block(self, element, checkOnlyBlock=True):
        if checkOnlyBlock:
            elements = list(element.iterchildren(tag=etree.Element))
            if len(elements) != 1:
                print elements
                assert False, 'Unexpected tags found'

        assert (len(element.findall(MATHML + "MathML")) +
                len(element.findall(NINEML + "MathInline")) +
                len(element.findall(NINEML + "Value"))) == 1

        if element.findall(NINEML + "MathInline"):
            mblock = expect_single(element.findall(NINEML +
                                                   'MathInline')).text.strip()
        elif element.findall(MATHML + "MathML"):
            mblock = self.load_mathml(expect_single(element.findall(MATHML +
                                                                    "MathML")))
        elif element.findall(NINEML + "Value"):
            mblock = self.load_value(expect_single(element.findall(NINEML +
                                                                   "Value")))
        return mblock

    def load_mathml(self, mathml):
        raise NotImplementedError

    def load_value(self, value):
        return pq.Quantity(float(value.text),
                           value.attrib.get('units', 'dimensionless'))

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
#         "Component": load_subcomponent,
        "Regime": load_regime,
        "StateVariable": load_statevariable,
        "Parameter": load_parameter,
        "EventSendPort": load_eventsendport,
        "AnalogSendPort": load_analogsendport,
        "EventReceivePort": load_eventreceiveport,
        "AnalogReceivePort": load_analogreceiveport,
        "AnalogReducePort": load_analogreduceport,
        "Dynamics": load_dynamics,
        "OnCondition": load_oncondition,
        "OnEvent": load_onevent,
        "Alias": load_alias,
        "TimeDerivative": load_timederivative,
        "Trigger": load_trigger,
        "StateAssignment": load_stateassignment,
        "EventOut": load_eventout,
        #"EventIn": load_eventin,
        "Subnode": load_subnode,
        "ConnectPorts": load_connectports,
    }


class XMLReader(object):

    """A class that can read |COMPONENTCLASS| objects from a NineML XML file.
    """
    loader = XMLLoader

    @classmethod
    def _load_include(cls, include_element, basedir, xml_node_filename_map):
        """Help function for replacing <Include> nodes.

        We replace the include node with the tree referenced
        by that filename. To do this, we load the file referenced,
        get all the elements in the root node, and copy them over to the place
        in the original tree where the original node was. It is important that
        we preserve the order. Finally, we remove the <Include> element node.

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
        """ Load the XML, including  all referenced Include files .

        We also populate a dictionary, ``xml_node_filename_map`` which maps
        each node to the name of the filename that it was originally in, so
        that when we load in single components from a file, which are
        hierachical and contain references to other components, we can find the
        components that were in the file specified.

        """

        if filename[:5] == "https":  # lxml only supports http and ftp
            doc = etree.parse(urlopen(filename))
        else:
            doc = etree.parse(filename)
        # Store the source filenames of all the nodes:
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
        root = cls._load_nested_xml(filename=filename,
                                   xml_node_filename_map=xml_node_filename_map)

        loader = cls.loader()
        loader.load_all_componentclasses(
                                   xmlroot=root,
                                   xml_node_filename_map=xml_node_filename_map)

        if component_name == None:
            key_func = lambda c: loader.component_srcs[c] == filename
            return filter_expect_single(loader.components, key_func)

        else:
            key_func = lambda c: c.name == component_name
            return filter_expect_single(loader.components, key_func)

    @classmethod
    def read_components(cls, filename):
        """Reads a several |COMPONENTCLASS| object from a filename.

        :param filename: The name of the file.
        :rtype: Returns a list of |COMPONENTCLASS| objects, for each
            <ComponentClass> node in the XML tree.

        """
        xml_node_filename_map = {}
        root = cls._load_nested_xml(filename, xml_node_filename_map)
        loader = cls.loader()
        loader.load_all_componentclasses(
                            xmlroot=root,
                            xml_node_filename_map=xml_node_filename_map)
        return loader.components
