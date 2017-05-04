# parameter
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return cls(name=node.attr('name', **options),
                     dimension=node.visitor.document[
                         node.attr('dimension', **options)])


# alias
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    name = node.attr('name', **options)
    rhs = node.attr('MathInline', in_body=True, dtype=Expression, **options)
    return cls(lhs=name, rhs=rhs)


# constant
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    if node.later_version(2.0, equal=True):
        value = node.attr('value', dtype=float, **options)
    else:
        value = node.body(dtype=float, **options)
    return cls(
        name=node.attr('name', **options),
        value=value,
        units=node.visitor.document[
            node.attr('units', **options)])


# dynamics
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    if node.later_version(2.0, equal=True):
        dyn_within = None
    else:
        dyn_within = 'Dynamics'
    return cls(
        name=node.attr('name', **options),
        parameters=node.children(Parameter, **options),
        analog_ports=node.children([AnalogSendPort, AnalogReceivePort,
                                    AnalogReducePort], **options),
        event_ports=node.children([EventSendPort, EventReceivePort],
                                  **options),
        regimes=node.children(Regime, within=dyn_within, **options),
        aliases=node.children(Alias, within=dyn_within, **options),
        state_variables=node.children(StateVariable, within=dyn_within,
                                      **options),
        constants=node.children(Constant, within=dyn_within, **options),
        document=node.visitor.document)


# eventsendport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return cls(name=node.attr('name', **options))


# eventreceiveport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return cls(name=node.attr('name', **options))


# analogsendport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return cls(
        name=node.attr('name', **options),
        dimension=node.visitor.document[node.attr('dimension', **options)])


# analogreceiveport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return cls(
        name=node.attr('name', **options),
        dimension=node.visitor.document[node.attr('dimension', **options)])


# analogreduceport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return cls(
        name=node.attr('name', **options),
        dimension=node.visitor.document[node.attr('dimension', **options)],
        operator=node.attr('operator', **options))


# regime
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable 
    return cls(name=node.attr('name', **options),
                  time_derivatives=node.children(TimeDerivative, **options),
                  transitions=(node.children(OnEvent, **options) +
                               node.children(OnCondition, **options)),
                  aliases=node.children(Alias, **options))


# statevariable
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    name = node.attr('name', **options)
    dimension = node.visitor.document[node.attr('dimension', **options)]
    return cls(name=name, dimension=dimension)


# timederivative
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    variable = node.attr('variable', **options)
    expr = node.attr('MathInline', in_body=True, dtype=Expression, **options)
    return cls(variable=variable, rhs=expr)


# oncondition
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    target_regime = node.attr('target_regime', **options)
    trigger = expect_single(node.children(Trigger, **options))
    return cls(trigger=trigger,
                       state_assignments=node.children(StateAssignment,
                                                       **options),
                       output_events=node.children(OutputEvent, **options),
                       target_regime=target_regime)


# onevent
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    target_regime = node.attr('target_regime', **options)
    return cls(src_port_name=node.attr('port', **options),
                   state_assignments=node.children(StateAssignment, **options),
                   output_events=node.children(OutputEvent, **options),
                   target_regime=target_regime)


# trigger
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return cls(node.attr('MathInline', in_body=True, dtype=Expression,
                         **options))


# stateassignment
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    lhs = node.attr('variable', **options)
    rhs = node.attr('MathInline', in_body=True, dtype=Expression, **options)
    return cls(lhs=lhs, rhs=rhs)


# outputevent
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    port_name = node.attr('port', **options)
    return cls(port_name=port_name)


# connectionruleclass
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    if node.later_version(2.0, equal=True):
        lib_elem = element
    else:
        cr_elem = node.visitor.get_single_child(node.serial_element,
                                                'RandomDistribution',
                                                **options)
        if node.visitor.get_children(cr_elem):
            raise NineMLSerializationError(
                "Not expecting {} blocks within 'RandomDistribution' block"
                .format(', '.join(node.visitor.get_children(cr_elem))))
        standard_library = node.visitor.get_attr(cr_elem, 'standard_library',
                                                 **options)
    return cls(
        name=node.attr('name', **options),
        standard_library=standard_library,
        parameters=node.children(Parameter, **options),
        document=node.visitor.document)


# randomdistributionclass
@classmethod
def unserialize(cls, node, **options):
    xmlns = extract_xmlns(element.tag)
    if node.later_version(2.0, equal=True):
        standard_library = node.attr('standard_library', **options)
    else:
        rd_elem = node.visitor.get_single_child(node.serial_element,
                                                'RandomDistribution',
                                                **options)
        if node.visitor.get_children(rd_elem):
            raise NineMLSerializationError(
                "Not expecting {} blocks within 'RandomDistribution' block"
                .format(', '.join(node.visitor.get_children(rd_elem))))
        standard_library = node.visitor.get_attr(rd_elem, 'standard_library',
                                                 **options)
    return cls(
        name=node.attr('name', **options),
        standard_library=standard_library,
        parameters=node.children(Parameter, **options),
        document=node.visitor.document)
