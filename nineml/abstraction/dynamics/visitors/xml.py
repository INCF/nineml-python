"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from nineml.annotations import annotate_xml
from nineml.utils import expect_single
from nineml.xml import (
    E, get_xml_attr, unprocessed_xml, NINEMLv1, extract_xmlns)
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


version1_main = ('Regime', 'Alias', 'StateVariable', 'Constant')


class DynamicsXMLLoader(ComponentClassXMLLoader, DynamicsVisitor):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    @unprocessed_xml
    def load_dynamics(self, element, **kwargs):  # @UnusedVariable
        block_names = ('Parameter', 'AnalogSendPort', 'AnalogReceivePort',
                       'EventSendPort', 'EventReceivePort', 'AnalogReducePort',
                       'Regime', 'Alias', 'StateVariable', 'Constant')
        blocks = self._load_blocks(element, block_names=block_names,
                                   ignore=[(NINEMLv1, 'Dynamics')], **kwargs)
        if extract_xmlns(element.tag) == NINEMLv1:
            dyn_elem = expect_single(element.findall(NINEMLv1 + 'Dynamics'))
            dyn_blocks = self._load_blocks(
                dyn_elem,
                block_names=version1_main,
                **kwargs)
            blocks.update(dyn_blocks)
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
    @unprocessed_xml
    def load_eventsendport(self, element, **kwargs):  # @UnusedVariable
        return EventSendPort(name=get_xml_attr(element, 'name', self.document,
                                               **kwargs))

    @read_annotations
    @unprocessed_xml
    def load_eventreceiveport(self, element, **kwargs):  # @UnusedVariable
        return EventReceivePort(name=get_xml_attr(element, 'name',
                                                  self.document, **kwargs))

    @read_annotations
    @unprocessed_xml
    def load_analogsendport(self, element, **kwargs):  # @UnusedVariable
        return AnalogSendPort(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            dimension=self.document[get_xml_attr(element, 'dimension',
                                                 self.document, **kwargs)])

    @read_annotations
    @unprocessed_xml
    def load_analogreceiveport(self, element, **kwargs):  # @UnusedVariable
        return AnalogReceivePort(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            dimension=self.document[get_xml_attr(element, 'dimension',
                                                 self.document, **kwargs)])

    @read_annotations
    @unprocessed_xml
    def load_analogreduceport(self, element, **kwargs):  # @UnusedVariable
        return AnalogReducePort(
            name=get_xml_attr(element, 'name', self.document, **kwargs),
            dimension=self.document[get_xml_attr(element, 'dimension',
                                                 self.document, **kwargs)],
            operator=get_xml_attr(element, 'operator', self.document,
                                  **kwargs))

    @read_annotations
    @unprocessed_xml
    def load_regime(self, element, **kwargs):  # @UnusedVariable
        block_names = ('TimeDerivative', 'OnCondition', 'OnEvent',
                       'Alias')
        blocks = self._load_blocks(element, block_names=block_names, **kwargs)
        transitions = blocks["OnEvent"] + blocks['OnCondition']
        return Regime(name=get_xml_attr(element, 'name', self.document,
                                        **kwargs),
                      time_derivatives=blocks["TimeDerivative"],
                      transitions=transitions,
                      aliases=blocks['Alias'])

    @read_annotations
    @unprocessed_xml
    def load_statevariable(self, element, **kwargs):  # @UnusedVariable
        name = get_xml_attr(element, 'name', self.document, **kwargs)
        dimension = self.document[get_xml_attr(element, 'dimension',
                                               self.document, **kwargs)]
        return StateVariable(name=name, dimension=dimension)

    @read_annotations
    @unprocessed_xml
    def load_timederivative(self, element, **kwargs):  # @UnusedVariable
        variable = get_xml_attr(element, 'variable', self.document, **kwargs)
        expr = self.load_expression(element, **kwargs)
        return TimeDerivative(variable=variable,
                              rhs=expr)

    @read_annotations
    @unprocessed_xml
    def load_oncondition(self, element, **kwargs):  # @UnusedVariable
        block_names = ('Trigger', 'StateAssignment', 'OutputEvent')
        blocks = self._load_blocks(element, block_names=block_names, **kwargs)
        target_regime = get_xml_attr(element, 'target_regime',
                                     self.document, **kwargs)
        trigger = expect_single(blocks["Trigger"])
        return OnCondition(trigger=trigger,
                           state_assignments=blocks["StateAssignment"],
                           output_events=blocks["OutputEvent"],
                           target_regime=target_regime)

    @read_annotations
    @unprocessed_xml
    def load_onevent(self, element, **kwargs):  # @UnusedVariable
        block_names = ('StateAssignment', 'OutputEvent')
        blocks = self._load_blocks(element, block_names=block_names, **kwargs)
        target_regime = get_xml_attr(element, 'target_regime',
                                     self.document, **kwargs)
        return OnEvent(src_port_name=get_xml_attr(element, 'port',
                                                  self.document, **kwargs),
                       state_assignments=blocks["StateAssignment"],
                       output_events=blocks["OutputEvent"],
                       target_regime=target_regime)

    @read_annotations
    @unprocessed_xml
    def load_trigger(self, element, **kwargs):  # @UnusedVariable
        return Trigger(self.load_expression(element, **kwargs))

    @read_annotations
    @unprocessed_xml
    def load_stateassignment(self, element, **kwargs):  # @UnusedVariable
        lhs = get_xml_attr(element, 'variable', self.document, **kwargs)
        rhs = self.load_expression(element, **kwargs)
        return StateAssignment(lhs=lhs, rhs=rhs)

    @read_annotations
    @unprocessed_xml
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

    @annotate_xml
    def visit_componentclass(self, component_class):
        child_elems = [
            e.accept_visitor(self)
            for e in component_class.sorted_elements(
                as_class=self.class_to_visit)]
        if self.xmlns == NINEMLv1:
            v1_elems = [e for e in child_elems
                        if e.tag[len(NINEMLv1):] not in version1_main]
            v1_elems.append(
                self.E('Dynamics',
                       *(e for e in child_elems
                         if e.tag[len(NINEMLv1):] in version1_main)))
            xml = self.E(component_class.v1_element_name,
                         *v1_elems, name=component_class.name)
        else:
            xml = self.E(component_class.element_name,
                         *child_elems,
                         name=component_class.name)
        return xml

    @annotate_xml
    def visit_regime(self, regime):
        return self.E('Regime', name=regime.name,
                      *(e.accept_visitor(self)
                        for e in regime.sorted_elements()))

    @annotate_xml
    def visit_statevariable(self, state_variable):
        return self.E('StateVariable',
                      name=state_variable.name,
                      dimension=state_variable.dimension.name)

    @annotate_xml
    def visit_outputevent(self, event_out):
        return self.E('OutputEvent',
                      port=event_out.port_name)

    @annotate_xml
    def visit_analogreceiveport(self, port):
        return self.E('AnalogReceivePort', name=port.name,
                      dimension=port.dimension.name)

    @annotate_xml
    def visit_analogreduceport(self, port):
        return self.E('AnalogReducePort', name=port.name,
                      dimension=port.dimension.name, operator=port.operator)

    @annotate_xml
    def visit_analogsendport(self, port):
        return self.E('AnalogSendPort', name=port.name,
                      dimension=port.dimension.name)

    @annotate_xml
    def visit_eventsendport(self, port):
        return self.E('EventSendPort', name=port.name)

    @annotate_xml
    def visit_eventreceiveport(self, port):
        return self.E('EventReceivePort', name=port.name)

    @annotate_xml
    def visit_stateassignment(self, assignment):
        return self.E('StateAssignment',
                      self.E("MathInline", assignment.rhs_xml),
                      variable=assignment.lhs)

    @annotate_xml
    def visit_timederivative(self, time_derivative):
        return self.E('TimeDerivative',
                      self.E("MathInline", time_derivative.rhs_xml),
                      variable=time_derivative.variable)

    @annotate_xml
    def visit_oncondition(self, on_condition):
        return self.E('OnCondition', on_condition.trigger.accept_visitor(self),
                      target_regime=on_condition._target_regime.name,
                      *(e.accept_visitor(self)
                        for e in on_condition.sorted_elements()))

    @annotate_xml
    def visit_trigger(self, trigger):
        return self.E('Trigger', self.E("MathInline", trigger.rhs_xml))

    @annotate_xml
    def visit_onevent(self, on_event):
        return self.E('OnEvent', port=on_event.src_port_name,
                      target_regime=on_event.target_regime.name,
                      *(e.accept_visitor(self)
                        for e in on_event.sorted_elements()))
