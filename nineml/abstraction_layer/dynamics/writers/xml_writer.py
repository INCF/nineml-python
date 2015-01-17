"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from itertools import chain
from lxml import etree
from lxml.builder import E
from nineml.abstraction_layer.dynamics import flattening
from nineml.abstraction_layer.xmlns import nineml_namespace
from nineml.abstraction_layer.dynamics.component import ComponentClass
from ..visitors import ComponentVisitor
from nineml.base import annotate_xml
from nineml.abstraction_layer.units import dimensionless


class XMLWriter(ComponentVisitor):

    @classmethod
    def write(cls, component, file, flatten=True):  # @ReservedAssignment
        doc = cls.to_xml(component, flatten)
        etree.ElementTree(doc).write(file, encoding="UTF-8", pretty_print=True,
                                     xml_declaration=True)

    @classmethod
    @annotate_xml
    def to_xml(cls, component, flatten=True):  # @ReservedAssignment
        assert isinstance(component, ComponentClass)
        if not component.is_flat():
            if not flatten:
                assert False, 'Trying to save nested models not yet supported'
            else:
                component = flattening.ComponentFlattener(component).\
                    reducedcomponent
        # Convert the component class and the dimensions it uses to xml
        component.standardize_unit_dimensions()
        xml = [XMLWriter().visit(component)] + [XMLWriter().visit_dimension(d)
                                                for d in component.dimensions]
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
        return E('StateVariable',
                 name=state_variable.name,
                 dimension=state_variable.dimension.name)

    @annotate_xml
    def visit_outputevent(self, output_event, **kwargs):  # @UnusedVariable
        return E('EventOut',
                 port=output_event.port_name)

    @annotate_xml
    def visit_parameter(self, parameter):
        return E('Parameter',
                 name=parameter.name,
                 dimension=parameter.dimension.name)

    @annotate_xml
    def visit_dimension(self, dimension):
        kwargs = {'name': dimension.name}
        kwargs.update(dict((k, str(v)) for k, v in dimension._dims.items()))
        return E('Dimension',
                 **kwargs)

    @annotate_xml
    def visit_analogreceiveport(self, port):
        return E('AnalogReceivePort', name=port.name,
                 dimension=port.dimension.name)

    @annotate_xml
    def visit_analogreduceport(self, port):
        return E('AnalogReducePort', name=port.name,
                 dimension=port.dimension.name,
                 operator=port.reduce_op)

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
    def visit_assignment(self, assignment):
        return E('StateAssignment',
                 E("MathInline", assignment.rhs),
                 variable=assignment.lhs)

    @annotate_xml
    def visit_alias(self, alias):
        return E('Alias',
                 E("MathInline", alias.rhs),
                 name=alias.lhs)

    @annotate_xml
    def visit_timederivative(self, time_derivative):
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
        return E('Trigger', E("MathInline", condition.rhs))

    @annotate_xml
    def visit_onevent(self, on_event):
        elements = ([p.accept_visitor(self)
                     for p in on_event.state_assignments] +
                    [p.accept_visitor(self) for p in on_event.event_outputs])
        kwargs = {'port': on_event.src_port_name}
        if on_event.target_regime:
            kwargs['target_regime'] = on_event.target_regime.name
        return E('OnEvent', *elements, **kwargs)
        assert False
