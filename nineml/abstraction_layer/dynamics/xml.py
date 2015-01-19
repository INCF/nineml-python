"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
import os
from urllib2 import urlopen
from itertools import chain
from lxml import etree
from lxml.builder import E
from .subcomponent import ComponentFlattener
from .visitors import ComponentVisitor
from ...base import annotate_xml
from ..units import dimensionless
import nineml
from ...utility import expect_single, filter_expect_single
from ...xmlns import NINEML, MATHML, nineml_namespace
from .base import DynamicsClass, Parameter, Dynamics
from ...base import read_annotations
from ..ports import (EventSendPort, EventReceivePort, AnalogSendPort,
                     AnalogReceivePort, AnalogReducePort)
from .transitions import OnEvent, OnCondition, StateAssignment, EventOut
from .regimes import Regime, StateVariable, TimeDerivative
from ..maths.expressions import Alias

____ = ['XMLReader']


class XMLLoader(object):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    def __init__(self, document=None):
        self.document = document

    def load__componentclasses(self, xmlroot, xml_node_filename_map):

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

        blocks = ('Parameter', 'AngSendPort', 'AngReceivePort',
                  'EventSendPort', 'EventReceivePort', 'AngReducePort',
                  'Dynamics', 'Subnode', 'ConnectPorts', 'Component')

        subnodes = self.loadBlocks(element, blocks=blocks)

        dynamics = expect_single(subnodes["Dynamics"])
        return DynamicsClass(
            name=element.get('name'),
            parameters=subnodes["Parameter"],
            ang_ports=chain(subnodes["AngSendPort"],
                               subnodes["AngReceivePort"],
                               subnodes["AngReducePort"]),
            event_ports=chain(subnodes["EventSendPort"],
                              subnodes["EventReceivePort"]),
            dynamics=dynamics,
            subnodes=dict(subnodes['Subnode']),
            portconnections=subnodes["ConnectPorts"])

    @read_annotations
    def load_parameter(self, element):
        return Parameter(name=element.get('name'),
                         dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_eventsendport(self, element):
        return EventSendPort(name=element.get('name'))

    @read_annotations
    def load_eventreceiveport(self, element):
        return EventReceivePort(name=element.get('name'))

    @read_annotations
    def load_angsendport(self, element):
        return AnalogSendPort(
            name=element.get("name"),
            dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_angreceiveport(self, element):
        return AnalogReceivePort(
            name=element.get("name"),
            dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_angreduceport(self, element):
        return AnalogReducePort(
            name=element.get('name'),
            dimension=self.document[element.get('dimension')],
            reduce_op=element.get("operator"))

    @read_annotations
    def load_dynamics(self, element):
        subblocks = ('Regime', 'Alias', 'StateVariable')
        subnodes = self.loadBlocks(element, blocks=subblocks)

        return Dynamics(regimes=subnodes["Regime"],
                                  ases=subnodes["Alias"],
                                  state_variables=subnodes["StateVariable"])

    @read_annotations
    def load_regime(self, element):
        subblocks = ('TimeDerivative', 'OnCondition', 'OnEvent')
        subnodes = self.loadBlocks(element, blocks=subblocks)
        transitions = subnodes["OnEvent"] + subnodes['OnCondition']
        return Regime(name=element.get('name'),
                         time_derivatives=subnodes["TimeDerivative"],
                         transitions=transitions)

    @read_annotations
    def load_statevariable(self, element):
        name = element.get("name")
        dimension = self.document[element.get('dimension')]
        return StateVariable(name=name, dimension=dimension)

    @read_annotations
    def load_timederivative(self, element):
        variable = element.get("variable")
        expr = self.load_single_internmaths_block(element)
        return TimeDerivative(dependent_variable=variable,
                                        rhs=expr)

    @read_annotations
    def load_alias(self, element):
        name = element.get("name")
        rhs = self.load_single_internmaths_block(element)
        return Alias(lhs=name,
                               rhs=rhs)

    @read_annotations
    def load_oncondition(self, element):
        subblocks = ('Trigger', 'StateAssignment', 'EventOut')
        subnodes = self.loadBlocks(element, blocks=subblocks)
        target_regime = element.get('target_regime', None)
        trigger = expect_single(subnodes["Trigger"])

        return OnCondition(trigger=trigger,
                              state_assignments=subnodes["StateAssignment"],
                              event_outputs=subnodes["EventOut"],
                              target_regime_name=target_regime)

    @read_annotations
    def load_onevent(self, element):
        subblocks = ('StateAssignment', 'EventOut')
        subnodes = self.loadBlocks(element, blocks=subblocks)
        target_regime_name = element.get('target_regime', None)

        return OnEvent(src_port_name=element.get('port'),
                          state_assignments=subnodes["StateAssignment"],
                          event_outputs=subnodes["EventOut"],
                          target_regime_name=target_regime_name)

    def load_trigger(self, element):
        return self.load_single_internmaths_block(element)

    @read_annotations
    def load_stateassignment(self, element):
        lhs = element.get('variable')
        rhs = self.load_single_internmaths_block(element)
        return StateAssignment(lhs=lhs, rhs=rhs)

    @read_annotations
    def load_eventout(self, element):
        port_name = element.get('port')
        return EventOut(port_name=port_name)

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
                    raise nineml.exceptions.NineMLRuntimeError(err)

            res[tag].append(XMLLoader.tag_to_loader[tag](self, t))
        return res

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "Regime": load_regime,
        "StateVariable": load_statevariable,
        "Parameter": load_parameter,
        "EventSendPort": load_eventsendport,
        "AngSendPort": load_angsendport,
        "EventReceivePort": load_eventreceiveport,
        "AngReceivePort": load_angreceiveport,
        "AngReducePort": load_angreduceport,
        "Dynamics": load_dynamics,
        "OnCondition": load_oncondition,
        "OnEvent": load_onevent,
        "Alias": load_alias,
        "TimeDerivative": load_timederivative,
        "Trigger": load_trigger,
        "StateAssignment": load_stateassignment,
        "EventOut": load_eventout,
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

        We o populate a dictionary, ``xml_node_filename_map`` which maps
        each node to the name of the filename that it was originy in, so
        that when we load in single components from a file, which are
        hierachicand contain references to other components, we can find the
        components that were in the file specified.

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
        loader.load__componentclasses(
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
        loader.load__componentclasses(
            xmlroot=root, xml_node_filename_map=xml_node_filename_map)
        return loader.components


class XMLWriter(ComponentVisitor):

    @classmethod
    def write(cls, component, file, flatten=True):  # @ReservedAssignment
        doc = cls.to_xml(component, flatten)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)

    @classmethod
    @annotate_xml
    def to_xml(cls, component, flatten=True):  # @ReservedAssignment
        assert isinstance(component, DynamicsClass)
        if not component.is_flat():
            if not flatten:
                assert False, 'Trying to save nested models not yet supported'
            else:
                component = ComponentFlattener(component).\
                    reducedcomponent
        component.standardize_unit_dimensions()
        xml = XMLWriter().visit(component)
        xml = [XMLWriter().visit_dimension(d) for d in component.dimensions
               if d is not None] + [xml]
        return E.NineML(*xml, xmlns=nineml_namespace)

    def visit_componentclass(self, component):
        elements = ([p.accept_visitor(self) for p in component.analog_ports] +
                    [p.accept_visitor(self) for p in component.event_ports] +
                    [p.accept_visitor(self) for p in component.parameters] +
                    [component.dynamics.accept_visitor(self)])
        return E('ComponentClass', *elements, name=component.name)

    @annotate_xml
    def visit_dynamics(self, dynamics):
        elements = ([r.accept_visitor(self) for r in dynamics.regimes] +
                    [b.accept_visitor(self) for b in dynamics.aliases] +
                    [b.accept_visitor(self) for b in dynamics.state_variables])
        return E('Dynamics', *elements)

    @annotate_xml
    def visit_regime(self, regime):
        nodes = ([node.accept_visitor(self)
                  for node in regime.time_derivatives] +
                 [node.accept_visitor(self) for node in regime.on_events] +
                 [node.accept_visitor(self) for node in regime.on_conditions])
        return E('Regime', name=regime.name, *nodes)

    @annotate_xml
    def visit_statevariable(self, state_variable):
        kwargs = {}
        if state_variable.dimension != dimensionless:
            kwargs['dimension'] = state_variable.dimension.name
        return E('StateVariable',
                 name=state_variable.name, **kwargs)

    @annotate_xml
    def visit_outputevent(self, output_event, **kwargs):  # @UnusedVariable
        return E('EventOut',
                 port=output_event.port_name)

    @annotate_xml
    def visit_parameter(self, parameter):
        kwargs = {}
        if parameter.dimension != dimensionless:
            kwargs['dimension'] = parameter.dimension.name
        return E('Parameter',
                 name=parameter.name, **kwargs)

    @annotate_xml
    def visit_dimension(self, dimension):
        kwargs = {'name': dimension.name}
        kwargs.update(dict((k, str(v)) for k, v in dimension._dims.items()))
        return E('Dimension',
                 **kwargs)

    @annotate_xml
    def visit_analogreceiveport(self, port, **kwargs):
        return E('AnalogReceivePort', name=port.name,
                 dimension=(port.dimension.name
                            if port.dimension else 'dimensionless'),
                 **kwargs)

    @annotate_xml
    def visit_analogreduceport(self, port, **kwargs):
        kwargs['operator'] = port.reduce_op
        return E('AnalogReducePort', name=port.name,
                 dimension=(port.dimension.name
                            if port.dimension else 'dimensionless'),
                 **kwargs)

    @annotate_xml
    def visit_analogsendport(self, port, **kwargs):
        return E('AnalogSendPort', name=port.name,
                 dimension=(port.dimension.name
                            if port.dimension else 'dimensionless'),
                 **kwargs)

    @annotate_xml
    def visit_eventsendport(self, port, **kwargs):
        return E('EventSendPort', name=port.name, **kwargs)

    @annotate_xml
    def visit_eventreceiveport(self, port, **kwargs):
        return E('EventReceivePort', name=port.name, **kwargs)

    @annotate_xml
    def visit_assignment(self, assignment, **kwargs):  # @UnusedVariable
        return E('StateAssignment',
                 E("MathInline", assignment.rhs),
                 variable=assignment.lhs)

    @annotate_xml
    def visit_alias(self, alias, **kwargs):  # @UnusedVariable
        return E('Alias',
                 E("MathInline", alias.rhs),
                 name=alias.lhs)

    @annotate_xml
    def visit_timederivative(self, time_derivative, **kwargs):  # @UnusedVariable @IgnorePep8
        return E('TimeDerivative',
                 E("MathInline", time_derivative.rhs),
                 variable=time_derivative.dependent_variable)

    @annotate_xml
    def visit_oncondition(self, on_condition):
        nodes = chain(on_condition.state_assignments,
                      on_condition.event_outputs, [on_condition.trigger])
        newNodes = [n.accept_visitor(self) for n in nodes]
        kwargs = {}
        if on_condition.target_regime:
            kwargs['target_regime'] = on_condition._target_regime.name
        return E('OnCondition', *newNodes, **kwargs)

    @annotate_xml
    def visit_condition(self, condition):
        return E('Trigger',
                 E("MathInline", condition.rhs))

    @annotate_xml
    def visit_onevent(self, on_event, **kwargs):  # @UnusedVariable
        elements = ([p.accept_visitor(self)
                     for p in on_event.state_assignments] +
                    [p.accept_visitor(self) for p in on_event.event_outputs])
        kwargs = {'port': on_event.src_port_name}
        if on_event.target_regime:
            kwargs['target_regime'] = on_event.target_regime.name
        return E('OnEvent', *elements, **kwargs)
        assert False
