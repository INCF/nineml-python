# ./abstraction/connectionrule/base.py
def serialize(self, node, **option):  # @UnusedVariable
    self.standardize_unit_dimensions()
    self.validate()
    return ConnectionRuleXMLWriter(document, E, **kwargs).visit(self)


# ./abstraction/dynamics/base.py
def serialize(self, node, **option):  # @UnusedVariable
    self.standardize_unit_dimensions()
    self.validate()
    return DynamicsXMLWriter(document=document, E=E, **kwargs).visit(self,
                                                                     E=E)


# ./abstraction/randomdistribution/base.py
def serialize(self, node, **option):  # @UnusedVariable
    self.standardize_unit_dimensions()
    self.validate()
    return RandomDistributionXMLWriter(document, E, **kwargs).visit(self)


# ./annotations.py
def serialize(self, node, **option):  # @UnusedVariable
    # Strip validate_dimensions annotation if True (to clean up
    # written files) as this is the default so can be
    # ignored and avoid cluttering the written file
    #                         if obj.annotations.get((VALIDATION, PY9ML_NS),
    #                                            DIMENSIONALITY) == 'True':
    #                         obj.annotations.delete((VALIDATION, PY9ML_NS),
    #                                                DIMENSIONALITY)
    return E(self.nineml_type, *self._sub_branches_to_xml(**kwargs))


# ./annotations.py
def serialize(self, node, **option):  # @UnusedVariable
    E = ElementMaker(namespace=self.ns)
    members = self._sub_branches_to_xml(**kwargs)
    if self.text is not None:
        members.append(self.text)
    return E(self.name, *members, **self._attr)


# ./document.py
def serialize(self, node, **option):  # @UnusedVariable
    self.standardize_units()
    self._added_in_write = []  # Initialise added_in_write
    elements = [e.to_xml(self, E=E, as_ref=False, **kwargs)
                for e in self.sorted_elements()]
    self.standardize_units()
    elements.extend(e.to_xml(self, E=E, as_ref=False, **kwargs)
                    for e in self._added_in_write)
    self._added_in_write = None
    return E(self.nineml_type, *elements)


# ./reference.py
def serialize(self, node, **option):  # @UnusedVariable
    name = self._referred_to.name
    if E._namespace == NINEMLv1:
        attrs = {}
        body = [name]
    else:
        attrs = {'name': name}
        body = []
    if self.url is not None and self.url != document.url:
        attrs['url'] = self.url
    element = E(self.nineml_type, *body, **attrs)
    return element


# ./units.py
def serialize(self, node, **option):  # @UnusedVariable
    kwargs = {'name': self.name}
    kwargs.update(dict(
        (n, str(p))
        for n, p in zip(self.dimension_symbols, self._dims) if abs(p) > 0))
    return E(self.nineml_type, **kwargs)


# ./units.py
def serialize(self, node, **option):  # @UnusedVariable
    kwargs = {'symbol': self.name, 'dimension': self.dimension.name,
              'power': str(self.power)}
    if self.offset:
        kwargs['offset'] = str(self.offset)
    return E(self.nineml_type,
             **kwargs)


# ./units.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type,
             self._value.to_xml(document, E=E, **kwargs),
             units=self.units.name)


# ./user/component.py
def serialize(self, node, **option):  # @UnusedVariable
    if self.url is None:
        # If definition was created in Python, add component class
        # reference to document argument before writing definition
        try:
            doc_obj = document[self._referred_to.name]
            if doc_obj != self._referred_to:
                raise NineMLRuntimeError(
                    "Cannot create reference for '{}' {} in the provided "
                    "document due to name clash with existing {} object"
                    .format(self._referred_to.name,
                            type(self._referred_to), type(doc_obj)))
        except NineMLNameError:
            document.add(self._referred_to, **kwargs)
    return super(Definition, self).to_xml(document, E=E, **kwargs)


# ./user/component.py
def serialize(self, node, **option):  # @UnusedVariable
    """
    docstring missing, although since the decorators don't
    preserve the docstring, it doesn't matter at the moment.
    """
    if E._namespace == NINEMLv1:
        tag = self.v1_nineml_type
    else:
        tag = self.nineml_type
    element = E(tag, self._definition.to_xml(document, E=E, **kwargs),
                *(p.to_xml(document, E=E, **kwargs)
                  for p in self.sorted_elements(local=True)),
                  name=self.name)
    return element


# ./user/component.py
def serialize(self, node, **option):  # @UnusedVariable
    if E._namespace == NINEMLv1:
        xml = E(self.nineml_type,
                self.value.to_xml(document, E=E, **kwargs),
                name=self.name,
                units=self.units.name)
    else:
        xml = E(self.nineml_type,
                self._quantity.to_xml(document, E=E, **kwargs),
                name=self.name)
    return xml


# ./user/multi/dynamics.py
def serialize(self, node, **option):  # @UnusedVariable
    members = [c.to_xml(document, E=E, **kwargs)
               for c in self.sub_components]
    members.extend(pe.to_xml(document, E=E, **kwargs)
                    for pe in self.port_exposures)
    members.extend(pc.to_xml(document, E=E, **kwargs)
                   for pc in self.port_connections)
    return E(self.nineml_type, *members, name=self.name)


# ./user/multi/dynamics.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type,
             self._component.to_xml(document, E=E, **kwargs),
             name=self.name)


# ./user/multi/dynamics.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type,
             self._component_class.to_xml(document, E=E, **kwargs),
             name=self.name)


# ./user/multi/dynamics.py
def serialize(self, node, **option):  # @UnusedVariable
    members = [c.to_xml(document, E=E, **kwargs)
               for c in self.sub_components]
    members.extend(pe.to_xml(document, E=E, **kwargs)
                    for pe in self.port_exposures)
    members.extend(pc.to_xml(document, E=E, **kwargs)
                   for pc in self.port_connections)
    return E(self.nineml_type, *members, name=self.name)


# ./user/multi/port_exposures.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type,
             name=self.name,
             sub_component=self.sub_component_name,
             port=self.port_name)


# ./user/network.py
def serialize(self, node, **option):  # @UnusedVariable
    member_elems = []
    for member in chain(self.populations, self.selections,
                        self.projections):
        member_elems.append(member.to_xml(
            document, E=E, as_ref=True, **kwargs))
    return E(self.nineml_type, name=self.name, *member_elems)


# ./user/network.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type,
             E.Size(str(self.size)),
             self.dynamics_properties.to_xml(document, E=E, **kwargs),
             name=self.name)


# ./user/network.py
def serialize(self, node, **option):  # @UnusedVariable
    members = [
        E.Source(self.source.to_xml(document, E=E, **kwargs),
                 port=self.source_port),
        E.Destination(self.destination.to_xml(document, E=E, **kwargs),
                      port=self.destination_port),
        E.Connectivity(self.connectivity.rule_properties.to_xml(
            document, E=E, **kwargs))]
    if self.delay is not None:
        members.append(E.Delay(self.delay.to_xml(document, E=E, **kwargs)))
    xml = E(self.nineml_type,
            *members,
            name=self.name)
    return xml


# ./user/population.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type,
             E.Size(str(self.size)),
             E.Cell(self.cell.to_xml(document, E=E, **kwargs)),
             name=self.name)


# ./user/port_connections.py
def serialize(self, node, **option):  # @UnusedVariable
    attribs = {}
    try:
        attribs['sender_role'] = self.sender_role
    except NineMLRuntimeError:
        attribs['sender_name'] = self.sender_name
    try:
        attribs['receiver_role'] = self.receiver_role
    except NineMLRuntimeError:
        attribs['receiver_name'] = self.receiver_name
    return E(
        self.nineml_type,
        send_port=self.send_port_name, receive_port=self.receive_port_name,
        **attribs)


# ./user/projection.py
def serialize(self, node, **option):  # @UnusedVariable
    if E._namespace == NINEMLv1:
        pcs = defaultdict(list)
        for pc in self.port_connections:
            pcs[pc.receiver_role].append(
                E('From' + self.v2tov1[pc.sender_role],
                  send_port=pc.send_port_name,
                  receive_port=pc.receive_port_name))
        args = [E.Source(self.pre.to_xml(document, E=E, as_ref=True,
                                         **kwargs), *pcs['pre']),
                E.Destination(self.post.to_xml(document, E=E, as_ref=True,
                                               **kwargs), *pcs['post']),
                E.Response(self.response.to_xml(document, E=E, **kwargs),
                           *pcs['response']),
                E.Connectivity(
                    self.connectivity.rule_properties.to_xml(document, E=E,
                                                             **kwargs))]
        if self.plasticity:
            args.append(E.Plasticity(
                self.plasticity.to_xml(document, E=E, **kwargs),
                *pcs['plasticity']))


# ./user/selection.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type,
             self.operation.to_xml(document, E=E, **kwargs),
             name=self.name)


# ./user/selection.py
def serialize(self, node, **option):  # @UnusedVariable
    def item_to_xml(item):
        if isinstance(item, Reference):
            return item.to_xml(document, E=E, **kwargs)
        elif E._namespace == NINEMLv1:
            return E.Reference(item.name)
        else:
            return E.Reference(name=item.name)
    return E(self.nineml_type,
             *[E.Item(item_to_xml(item), index=str(i))
               for i, item in enumerate(self.items)])


# ./values.py
def serialize(self, node, **option):  # @UnusedVariable
    pass


# ./values.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type, repr(self.value))


# ./values.py
def serialize(self, node, **option):  # @UnusedVariable
    if self._datafile is None:
        return E.ArrayValue(
            *[E.ArrayValueRow(index=str(i), value=repr(v))
              for i, v in enumerate(self._values)])
    else:
        raise NotImplementedError(
            "TODO: Need to implement code to save data to external file")
        return E.ExternalArrayValue(
            url=self.url, mimetype=self.mimetype,
            columnName=self.columnName)


# ./values.py
def serialize(self, node, **option):  # @UnusedVariable
    return E(self.nineml_type,
             self.distribution.to_xml(document, E=E, **kwargs))
