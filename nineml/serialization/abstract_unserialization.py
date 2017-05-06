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



# randomdistributionclass

