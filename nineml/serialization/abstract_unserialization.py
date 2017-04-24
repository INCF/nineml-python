

def load_parameter(self, element, **kwargs):  # @UnusedVariable
    return Parameter(name=get_xml_attr(element, 'name', self.document,
                                       **kwargs),
                     dimension=self.document[
                         get_xml_attr(element, 'dimension', self.document,
                                      **kwargs)])


def load_alias(self, element, **kwargs):  # @UnusedVariable
    name = get_xml_attr(element, 'name', self.document, **kwargs)
    rhs = self.load_expression(element, **kwargs)
    return Alias(lhs=name, rhs=rhs)


def load_constant(self, element, **kwargs):  # @UnusedVariable
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


def load_expression(self, element, **kwargs):
    return get_xml_attr(element, 'MathInline', self.document,
                        in_block=True, dtype=Expression, **kwargs)


def _load_blocks(self, element, block_names, unprocessed=None,
                 prev_block_names={}, ignore=[], **kwargs):  # @UnusedVariable @IgnorePep8
    """
    Creates a dictionary that maps class-types to instantiated objects
    """
    # Get the XML namespace (i.e. NineML version)
    xmlns = extract_xmlns(element.tag)
    assert xmlns in ALL_NINEML
    # Initialise loaded objects with empty lists
    loaded_objects = dict((block, []) for block in block_names)
    for t in element.iterchildren(tag=etree.Element):
        # Used in unprocessed_xml decorator
        if unprocessed:
            unprocessed[0].discard(t)
        # Strip namespace
        tag = (t.tag[len(xmlns):]
               if t.tag.startswith(xmlns) else t.tag)
        if (xmlns, tag) not in ignore:
            if tag not in block_names:
                raise NineMLXMLBlockError(
                    "Unexpected block {} within {} in '{}', expected: {}"
                    .format(tag, identify_element(element),
                            self.document.url, ', '.join(block_names)))
            loaded_objects[tag].append(self.tag_to_loader[tag](self, t))
    return loaded_objects


def load_dynamics(self, element, **kwargs):  # @UnusedVariable
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



def load_eventsendport(self, element, **kwargs):  # @UnusedVariable
    return EventSendPort(name=get_xml_attr(element, 'name', self.document,
                                           **kwargs))


def load_eventreceiveport(self, element, **kwargs):  # @UnusedVariable
    return EventReceivePort(name=get_xml_attr(element, 'name',
                                              self.document, **kwargs))


def load_analogsendport(self, element, **kwargs):  # @UnusedVariable
    return AnalogSendPort(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        dimension=self.document[get_xml_attr(element, 'dimension',
                                             self.document, **kwargs)])


def load_analogreceiveport(self, element, **kwargs):  # @UnusedVariable
    return AnalogReceivePort(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        dimension=self.document[get_xml_attr(element, 'dimension',
                                             self.document, **kwargs)])


def load_analogreduceport(self, element, **kwargs):  # @UnusedVariable
    return AnalogReducePort(
        name=get_xml_attr(element, 'name', self.document, **kwargs),
        dimension=self.document[get_xml_attr(element, 'dimension',
                                             self.document, **kwargs)],
        operator=get_xml_attr(element, 'operator', self.document,
                              **kwargs))


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


def load_statevariable(self, element, **kwargs):  # @UnusedVariable
    name = get_xml_attr(element, 'name', self.document, **kwargs)
    dimension = self.document[get_xml_attr(element, 'dimension',
                                           self.document, **kwargs)]
    return StateVariable(name=name, dimension=dimension)


def load_timederivative(self, element, **kwargs):  # @UnusedVariable
    variable = get_xml_attr(element, 'variable', self.document, **kwargs)
    expr = self.load_expression(element, **kwargs)
    return TimeDerivative(variable=variable,
                          rhs=expr)


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


def load_trigger(self, element, **kwargs):  # @UnusedVariable
    return Trigger(self.load_expression(element, **kwargs))


def load_stateassignment(self, element, **kwargs):  # @UnusedVariable
    lhs = get_xml_attr(element, 'variable', self.document, **kwargs)
    rhs = self.load_expression(element, **kwargs)
    return StateAssignment(lhs=lhs, rhs=rhs)


def load_outputevent(self, element, **kwargs):  # @UnusedVariable
    port_name = get_xml_attr(element, 'port', self.document, **kwargs)
    return OutputEvent(port_name=port_name)


def load_connectionruleclass(self, element, **kwargs):  # @UnusedVariable
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


def load_randomdistributionclass(self, element, **kwargs):
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
