

# parameter
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E(Parameter.nineml_type,
                  name=parameter.name,
                  dimension=parameter.dimension.name)


# alias
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E(Alias.nineml_type,
                  self.E("MathInline", alias.rhs_xml),
                  name=alias.lhs)


# constant
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    if self.xmlns == NINEMLv1:
        xml = self.E(Constant.nineml_type,
                     repr(constant.value),
                     name=constant.name,
                     units=constant.units.name)
    else:
        xml = self.E(Constant.nineml_type,
                     name=constant.name,
                     value=repr(constant.value),
                     units=constant.units.name)
    return xml


# componentclass
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable @IgnorePep8
    child_elems = [
        e.accept_visitor(self)
        for e in component_class.sorted_elements(
            class_map=self.class_to_visit.class_to_member)]
    if self.xmlns == NINEMLv1:
        v1_elems = [e for e in child_elems
                    if e.tag[len(NINEMLv1):] not in version1_main]
        v1_elems.append(
            self.E('Dynamics',
                   *(e for e in child_elems
                     if e.tag[len(NINEMLv1):] in version1_main)))
        xml = self.E(component_class.v1_nineml_type,
                     *v1_elems, name=component_class.name)
    else:
        xml = self.E(component_class.nineml_type,
                     *child_elems,
                     name=component_class.name)
    return xml


# regime
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('Regime', name=regime.name,
                  *(e.accept_visitor(self)
                    for e in regime.sorted_elements()))


# statevariable
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('StateVariable',
                  name=state_variable.name,
                  dimension=state_variable.dimension.name)


# outputevent
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('OutputEvent',
                  port=event_out.port_name)


# analogreceiveport
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('AnalogReceivePort', name=port.name,
                  dimension=port.dimension.name)


# analogreduceport
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('AnalogReducePort', name=port.name,
                  dimension=port.dimension.name, operator=port.operator)


# analogsendport
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('AnalogSendPort', name=port.name,
                  dimension=port.dimension.name)


# eventsendport
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('EventSendPort', name=port.name)


# eventreceiveport
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('EventReceivePort', name=port.name)


# stateassignment
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('StateAssignment',
                  self.E("MathInline", assignment.rhs_xml),
                  variable=assignment.lhs)


# timederivative
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable @IgnorePep8
    return self.E('TimeDerivative',
                  self.E("MathInline", time_derivative.rhs_xml),
                  variable=time_derivative.variable)


# oncondition
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('OnCondition', on_condition.trigger.accept_visitor(self),
                  target_regime=on_condition._target_regime.name,
                  *(e.accept_visitor(self)
                    for e in on_condition.sorted_elements()))


# trigger
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('Trigger', self.E("MathInline", trigger.rhs_xml))


# onevent
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable
    return self.E('OnEvent', port=on_event.src_port_name,
                  target_regime=on_event.target_regime.name,
                  *(e.accept_visitor(self)
                    for e in on_event.sorted_elements()))

# componentclass
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable @IgnorePep8
    if self.xmlns == NINEMLv1:
        elems = [e.accept_visitor(self)
                    for e in component_class.sorted_elements()]
        elems.append(
            self.E('ConnectionRule',
                   standard_library=component_class.standard_library))
        xml = self.E('ComponentClass', *elems, name=component_class.name)
    else:
        xml = self.E(component_class.nineml_type,
                     *(e.accept_visitor(self)
                       for e in component_class.sorted_elements()),
                     name=component_class.name,
                     standard_library=component_class.standard_library)
    return xml


# componentclass
@classmethod
def serialize(cls, node, **options):  # @UnusedVariable @IgnorePep8
    if self.xmlns == NINEMLv1:
        elems = [e.accept_visitor(self)
                    for e in component_class.sorted_elements()]
        elems.append(
            self.E('RandomDistribution',
                   standard_library=component_class.standard_library))
        xml = self.E('ComponentClass', *elems, name=component_class.name)
    else:
        xml = self.E(component_class.nineml_type,
                     *(e.accept_visitor(self)
                       for e in component_class.sorted_elements()),
                     standard_library=component_class.standard_library,
                     name=component_class.name)
    return xml