# parameter
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return Parameter(name=get_xml_attr(element, 'name', self.document,
                                       **kwargs),
                     dimension=self.document[
                         get_xml_attr(element, 'dimension', self.document,
                                      **kwargs)])


# alias
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    name = get_xml_attr(element, 'name', self.document, **kwargs)
    rhs = self.load_expression(element, **kwargs)
    return Alias(lhs=name, rhs=rhs)


# constant
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    xmlns = extract_xmlns(element.tag)
    if xmlns == NINEMLv1:
        value = float(element.text)
    else:
        value = get_xml_attr(element, 'value', self.document,
                             dtype=float, **kwargs)
    return Constant(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        value=value,
        units=self.document[
            get_xml_attr(element, 'units', self.document, **kwargs)])


# expression
@classmethod
def unserialize(cls, node, **options):
    return get_xml_attr(element, 'MathInline', self.document,
                        in_block=True, dtype=Expression, **kwargs)


# dynamics
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    block_names = ('Parameter', 'AnalogSendPort', 'AnalogReceivePort',
                   'EventSendPort', 'EventReceivePort', 'AnalogReducePort',
                   'Regime', 'Alias', 'StateVariable', 'Constant')
    blocks = self._load_blocks(element, block_names=block_names,
                               ignore=[(NINEMLv1, 'Dynamics')], **kwargs)
    if extract_xmlns(element.tag) == NINEMLv1:
        if any(blocks[block_name] for block_name in version1_main):
            raise NineMLXMLBlockError(
                "{} blocks should be enclosed in a Dynamics block (i.e. "
                "not the outer ComponentClass block) in version 1.0 "
                "(they belong in the outer block in later versions)"
                .format(', '.join(n for n in version1_main if blocks[n])))
        dyn_elem = expect_single(element.findall(NINEMLv1 + 'Dynamics'))
        dyn_blocks = self._load_blocks(
            dyn_elem,
            block_names=version1_main,
            **kwargs)
        blocks.update(dyn_blocks)
    dyn_kwargs = dict((k, v) for k, v in kwargs.iteritems()
                      if k in ('validate_dimensions'))
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
        constants=blocks["Constant"],
        document=self.document,
        **dyn_kwargs)



# eventsendport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return EventSendPort(name=get_xml_attr(element, 'name', self.document,
                                           **kwargs))


# eventreceiveport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return EventReceivePort(name=get_xml_attr(element, 'name',
                                              self.document, **kwargs))


# analogsendport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return AnalogSendPort(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        dimension=self.document[get_xml_attr(element, 'dimension',
                                             self.document, **kwargs)])


# analogreceiveport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return AnalogReceivePort(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        dimension=self.document[get_xml_attr(element, 'dimension',
                                             self.document, **kwargs)])


# analogreduceport
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return AnalogReducePort(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        dimension=self.document[get_xml_attr(element, 'dimension',
                                             self.document, **kwargs)],
        operator=get_xml_attr(element, 'operator', self.document,
                              **kwargs))


# regime
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    block_names = ('TimeDerivative', 'OnCondition', 'OnEvent',
                   'Alias')
    blocks = self._load_blocks(element, block_names=block_names, **kwargs)
    transitions = blocks["OnEvent"] + blocks['OnCondition']
    return Regime(name=get_xml_attr(element, 'name', self.document,
                                    **kwargs),
                  time_derivatives=blocks["TimeDerivative"],
                  transitions=transitions,
                  aliases=blocks['Alias'])


# statevariable
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    name = get_xml_attr(element, 'name', self.document, **kwargs)
    dimension = self.document[get_xml_attr(element, 'dimension',
                                           self.document, **kwargs)]
    return StateVariable(name=name, dimension=dimension)


# timederivative
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    variable = get_xml_attr(element, 'variable', self.document, **kwargs)
    expr = self.load_expression(element, **kwargs)
    return TimeDerivative(variable=variable,
                          rhs=expr)


# oncondition
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    block_names = ('Trigger', 'StateAssignment', 'OutputEvent')
    blocks = self._load_blocks(element, block_names=block_names, **kwargs)
    target_regime = get_xml_attr(element, 'target_regime',
                                 self.document, **kwargs)
    trigger = expect_single(blocks["Trigger"])
    return OnCondition(trigger=trigger,
                       state_assignments=blocks["StateAssignment"],
                       output_events=blocks["OutputEvent"],
                       target_regime=target_regime)


# onevent
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    block_names = ('StateAssignment', 'OutputEvent')
    blocks = self._load_blocks(element, block_names=block_names, **kwargs)
    target_regime = get_xml_attr(element, 'target_regime',
                                 self.document, **kwargs)
    return OnEvent(src_port_name=get_xml_attr(element, 'port',
                                              self.document, **kwargs),
                   state_assignments=blocks["StateAssignment"],
                   output_events=blocks["OutputEvent"],
                   target_regime=target_regime)


# trigger
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    return Trigger(self.load_expression(element, **kwargs))


# stateassignment
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    lhs = get_xml_attr(element, 'variable', self.document, **kwargs)
    rhs = self.load_expression(element, **kwargs)
    return StateAssignment(lhs=lhs, rhs=rhs)


# outputevent
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    port_name = get_xml_attr(element, 'port', self.document, **kwargs)
    return OutputEvent(port_name=port_name)


# connectionruleclass
@classmethod
def unserialize(cls, node, **options):  # @UnusedVariable
    xmlns = extract_xmlns(element.tag)
    if xmlns == NINEMLv1:
        lib_elem = expect_single(element.findall(NINEMLv1 +
                                                 'ConnectionRule'))
        if lib_elem.getchildren():
            raise NineMLXMLBlockError(
                "Not expecting {} blocks within 'ConnectionRule' block"
                .format(', '.join(e.tag for e in lib_elem.getchildren())))
    else:
        lib_elem = element
    std_lib = get_xml_attr(lib_elem, 'standard_library', self.document,
                           **kwargs)
    blocks = self._load_blocks(
        element, block_names=('Parameter',),
        ignore=[(NINEMLv1, 'ConnectionRule')], **kwargs)
    return ConnectionRule(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        standard_library=std_lib,
        parameters=blocks["Parameter"],
        document=self.document)


# randomdistributionclass
@classmethod
def unserialize(cls, node, **options):
    xmlns = extract_xmlns(element.tag)
    if xmlns == NINEMLv1:
        lib_elem = expect_single(element.findall(NINEMLv1 +
                                                 'RandomDistribution'))
        if lib_elem.getchildren():
            raise NineMLXMLBlockError(
                "Not expecting {} blocks within 'RandomDistribution' block"
                .format(', '.join(e.tag for e in lib_elem.getchildren())))
    else:
        lib_elem = element
    blocks = self._load_blocks(
        element, block_names=('Parameter',),
        ignore=[(NINEMLv1, 'RandomDistribution')], **kwargs)
    return RandomDistribution(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        standard_library=get_xml_attr(lib_elem, 'standard_library',
                                      self.document, **kwargs),
        parameters=blocks["Parameter"],
        document=self.document)
