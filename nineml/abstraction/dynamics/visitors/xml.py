"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from nineml.annotations import annotate_xml
from nineml.utils import expect_single
from nineml.xml import E, get_xml_attr
from ..base import Dynamics
from nineml.annotations import read_annotations
from ...ports import (EventSendPort, EventReceivePort, AnalogSendPort,
                      AnalogReceivePort, AnalogReducePort)
from ..transitions import (
    OnEvent, OnCondition, StateAssignment, OutputEvent, Trigger)
from ..regimes import Regime, StateVariable, TimeDerivative
from .base import DynamicsVisitor
from ...componentclass.visitors.xml import (
    ComponentClassXMLLoader, ComponentClassXMLWriter)


class DynamicsXMLLoader(ComponentClassXMLLoader, DynamicsVisitor):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    def load_dynamics(self, element, **kwargs):  # @UnusedVariable
        block_names = ('Parameter', 'AnalogSendPort', 'AnalogReceivePort',
                       'EventSendPort', 'EventReceivePort', 'AnalogReducePort',
                       'Dynamics', 'Regime', 'Alias', 'StateVariable',
                       'Constant')
        blocks = self._load_blocks(element, block_names=block_names)
        dyn_kwargs = dict((k, v) for k, v in kwargs.iteritems()
                          if k in ('validate_dimensions', 'url'))
        return Dynamics(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            parameters=blocks["Parameter"],
            analog_ports=chain(blocks["AnalogSendPort"],
                               blocks["AnalogReceivePort"],
                               blocks["AnalogReducePort"]),
            event_ports=chain(blocks["EventSendPort"],
                              blocks["EventReceivePort"]),
            regimes=blocks["Regime"],
            aliases=blocks["Alias"],
            state_variables=blocks["StateVariable"],
            constants=blocks["Constant"], **dyn_kwargs)

    @read_annotations
    def load_eventsendport(self, element, **kwargs):  # @UnusedVariable
        return EventSendPort(name=get_xml_attr(element, 'name', self.document,
                                               **kwargs))

    @read_annotations
    def load_eventreceiveport(self, element, **kwargs):  # @UnusedVariable
        return EventReceivePort(name=get_xml_attr(element, 'name',
                                                  self.document, **kwargs))

    @read_annotations
    def load_analogsendport(self, element, **kwargs):  # @UnusedVariable
        return AnalogSendPort(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            dimension=self.document[get_xml_attr(element, 'dimension',
                                                 self.document, **kwargs)])

    @read_annotations
    def load_analogreceiveport(self, element, **kwargs):  # @UnusedVariable
        return AnalogReceivePort(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            dimension=self.document[get_xml_attr(element, 'dimension',
                                                 self.document, **kwargs)])

    @read_annotations
    def load_analogreduceport(self, element, **kwargs):  # @UnusedVariable
        return AnalogReducePort(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            dimension=self.document[get_xml_attr(element, 'dimension',
                                                 self.document, **kwargs)],
            operator=get_xml_attr(element, 'operator', self.document,
                                  **kwargs))

    @read_annotations
    def load_regime(self, element, **kwargs):  # @UnusedVariable
        block_names = ('TimeDerivative', 'OnCondition', 'OnEvent',
                       'Alias')
        blocks = self._load_blocks(element, block_names=block_names)
        transitions = blocks["OnEvent"] + blocks['OnCondition']
        return Regime(name=get_xml_attr(element, 'name', self.document,
                                        **kwargs),
                      time_derivatives=blocks["TimeDerivative"],
                      transitions=transitions,
                      aliases=blocks['Alias'])

    @read_annotations
    def load_statevariable(self, element, **kwargs):  # @UnusedVariable
        name = get_xml_attr(element, 'name', self.document, **kwargs)
        dimension = self.document[get_xml_attr(element, 'dimension',
                                               self.document, **kwargs)]
        return StateVariable(name=name, dimension=dimension)

    @read_annotations
    def load_timederivative(self, element, **kwargs):  # @UnusedVariable
        variable = get_xml_attr(element, 'variable', self.document, **kwargs)
        expr = self.load_single_internmaths_block(element)
        return TimeDerivative(variable=variable,
                              rhs=expr)

    @read_annotations
    def load_oncondition(self, element, **kwargs):  # @UnusedVariable
        block_names = ('Trigger', 'StateAssignment', 'OutputEvent')
        blocks = self._load_blocks(element, block_names=block_names)
        target_regime = get_xml_attr(element, 'target_regime',
                                     self.document, **kwargs)
        trigger = expect_single(blocks["Trigger"])
        return OnCondition(trigger=trigger,
                           state_assignments=blocks["StateAssignment"],
                           output_events=blocks["OutputEvent"],
                           target_regime=target_regime)

    @read_annotations
    def load_onevent(self, element, **kwargs):  # @UnusedVariable
        block_names = ('StateAssignment', 'OutputEvent')
        blocks = self._load_blocks(element, block_names=block_names)
        target_regime = get_xml_attr(element, 'target_regime',
                                     self.document, **kwargs)
        return OnEvent(src_port_name=get_xml_attr(element, 'port',
                                                  self.document, **kwargs),
                       state_assignments=blocks["StateAssignment"],
                       output_events=blocks["OutputEvent"],
                       target_regime=target_regime)

    @read_annotations
    def load_trigger(self, element, **kwargs):  # @UnusedVariable
        return Trigger(self.load_single_internmaths_block(element))

    @read_annotations
    def load_stateassignment(self, element, **kwargs):  # @UnusedVariable
        lhs = get_xml_attr(element, 'variable', self.document, **kwargs)
        rhs = self.load_single_internmaths_block(element)
        return StateAssignment(lhs=lhs, rhs=rhs)

    @read_annotations
    def load_outputevent(self, element, **kwargs):  # @UnusedVariable
        port_name = get_xml_attr(element, 'port', self.document, **kwargs)
        return OutputEvent(port_name=port_name)

    tag_to_loader = dict(
        tuple(ComponentClassXMLLoader.tag_to_loader.iteritems()) +
        (("Dynamics", load_dynamics),
         ("Regime", load_regime),
         ("StateVariable", load_statevariable),
         ("EventSendPort", load_eventsendport),
         ("AnalogSendPort", load_analogsendport),
         ("EventReceivePort", load_eventreceiveport),
         ("AnalogReceivePort", load_analogreceiveport),
         ("AnalogReducePort", load_analogreduceport),
         ("OnCondition", load_oncondition),
         ("OnEvent", load_onevent),
         ("TimeDerivative", load_timederivative),
         ("Trigger", load_trigger),
         ("StateAssignment", load_stateassignment),
         ("OutputEvent", load_outputevent)))


class DynamicsXMLWriter(ComponentClassXMLWriter, DynamicsVisitor):

    # Maintains order of elements between writes
    write_order = ['Parameter', 'EventReceivePort', 'AnalogReceivePort',
                   'AnalogReducePort', 'EventSendPort', 'AnalogSendPort',
                   'StateVariable', 'Regime', 'Alias', 'Constant',
                   'TimeDerivative', 'OnEvent', 'OnCondition', 'Trigger',
                   'StateAssignment', 'OutputEvent', 'Annotations']

    @annotate_xml
    def visit_componentclass(self, component_class):
        return E('Dynamics',
                 *self._sort(e.accept_visitor(self)
                             for e in component_class.elements(
                                 as_class=self.class_to_visit)),
                 name=component_class.name)

    @annotate_xml
    def visit_regime(self, regime):
        return E('Regime', name=regime.name,
                 *self._sort(e.accept_visitor(self)
                             for e in regime.elements()))

    @annotate_xml
    def visit_statevariable(self, state_variable):
        return E('StateVariable',
                 name=state_variable.name,
                 dimension=state_variable.dimension.name)

    @annotate_xml
    def visit_outputevent(self, event_out):
        return E('OutputEvent',
                 port=event_out.port_name)

    @annotate_xml
    def visit_analogreceiveport(self, port):
        return E('AnalogReceivePort', name=port.name,
                 dimension=port.dimension.name)

    @annotate_xml
    def visit_analogreduceport(self, port):
        return E('AnalogReducePort', name=port.name,
                 dimension=port.dimension.name, operator=port.operator)

    @annotate_xml
    def visit_analogsendport(self, port):
        return E('AnalogSendPort', name=port.name,
                 dimension=port.dimension.name)

    @annotate_xml
    def visit_eventsendport(self, port):
        return E('EventSendPort', name=port.name)

    @annotate_xml
    def visit_eventreceiveport(self, port):
        return E('EventReceivePort', name=port.name)

    @annotate_xml
    def visit_stateassignment(self, assignment):
        return E('StateAssignment',
                 E("MathInline", assignment.rhs_xml),
                 variable=assignment.lhs)

    @annotate_xml
    def visit_timederivative(self, time_derivative):
        return E('TimeDerivative',
                 E("MathInline", time_derivative.rhs_xml),
                 variable=time_derivative.variable)

    @annotate_xml
    def visit_oncondition(self, on_condition):
        return E('OnCondition', on_condition.trigger.accept_visitor(self),
                 target_regime=on_condition._target_regime.name,
                 *self._sort(e.accept_visitor(self)
                             for e in on_condition.elements()))

    @annotate_xml
    def visit_trigger(self, trigger):
        return E('Trigger', E("MathInline", trigger.rhs_xml))

    @annotate_xml
    def visit_onevent(self, on_event):
        return E('OnEvent', port=on_event.src_port_name,
                 target_regime=on_event.target_regime.name,
                 *self._sort(e.accept_visitor(self)
                             for e in on_event.elements()))
