

# ./units.py
def serialize_node(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name)
    for n, p in zip(self.dimension_symbols, self._dims):
        if abs(p) > 0:
            node.attr(n, p)


# ./units.py
def serialize_node(self, node, **options):  # @UnusedVariable
    node.attr('symbol', self.name)
    node.attr('dimension', self.dimension.name)
    node.attr('power', self.power)
    if self.offset:
        node.attr('offset', self.offset)


# ./units.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type,
             self._value.to_xml(document, E=E, **kwargs),
             node.attr('units', self.units.name, **options))


# ./user/component.py
def serialize_node(self, node, **options):  # @UnusedVariable
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
def serialize_node(self, node, **options):  # @UnusedVariable
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
                  node.attr('name', self.name, **options))
    return element


# ./user/component.py
def serialize_node(self, node, **options):  # @UnusedVariable
    if E._namespace == NINEMLv1:
        xml = E(self.nineml_type,
                self.value.to_xml(document, E=E, **kwargs),
                node.attr('name', self.name, **options),
                node.attr('units', self.units.name, **options))
    else:
        xml = E(self.nineml_type,
                self._quantity.to_xml(document, E=E, **kwargs),
                node.attr('name', self.name, **options))
    return xml


# ./user/multi/dynamics.py
def serialize_node(self, node, **options):  # @UnusedVariable
    members = [c.to_xml(document, E=E, **kwargs)
               for c in self.sub_components]
    members.extend(pe.to_xml(document, E=E, **kwargs)
                    for pe in self.port_exposures)
    members.extend(pc.to_xml(document, E=E, **kwargs)
                   for pc in self.port_connections)
    return E(self.nineml_type, *members, node.attr('name', self.name, **options))


# ./user/multi/dynamics.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type,
             self._component.to_xml(document, E=E, **kwargs),
             node.attr('name', self.name, **options))


# ./user/multi/dynamics.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type,
             self._component_class.to_xml(document, E=E, **kwargs),
             node.attr('name', self.name, **options))


# ./user/multi/dynamics.py
def serialize_node(self, node, **options):  # @UnusedVariable
    members = [c.to_xml(document, E=E, **kwargs)
               for c in self.sub_components]
    members.extend(pe.to_xml(document, E=E, **kwargs)
                    for pe in self.port_exposures)
    members.extend(pc.to_xml(document, E=E, **kwargs)
                   for pc in self.port_connections)
    return E(self.nineml_type, *members, node.attr('name', self.name, **options))


# ./user/multi/port_exposures.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type,
             node.attr('name', self.name, **options),
             node.attr('sub_component', self.sub_component_name, **options),
             node.attr('port', self.port_name, **options))


# ./user/network.py
def serialize_node(self, node, **options):  # @UnusedVariable
    member_elems = []
    for member in chain(self.populations, self.selections,
                        self.projections):
        member_elems.append(member.to_xml(
            document, E=E, as_ref=True, **kwargs))
    return E(self.nineml_type, node.attr('name', self.name, **options), *member_elems)


# ./user/network.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type,
             E.Size(str(self.size)),
             self.dynamics_properties.to_xml(document, E=E, **kwargs),
             node.attr('name', self.name, **options))


# ./user/network.py
def serialize_node(self, node, **options):  # @UnusedVariable
    node.child(self.source, within='Source',
               within_attrs={'port': self.source_port})
    node.child(self.destination, within='Destination',
               within_attrs={'port': self.destination_port})
    node.child(self.connectivity.rule_properties, within='Connectivity')
    if self.delay is not None:
        node.child(self.delay, within='Delay')
    node.attr('name', self.name)


# ./user/population.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type,
             E.Size(str(self.size)),
             node.child(self.cell, within='Cell')
             node.attr('name', self.name, **options))


# ./user/port_connections.py
def serialize_node(self, node, **options):  # @UnusedVariable
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
        node.attr('send_port', self.send_port_name, **options), node.attr('receive_port', self.receive_port_name, **options),
        **attribs)


# ./user/projection.py
def serialize_node(self, node, **options):  # @UnusedVariable
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
                node.child(self.response, within='Response')
                           *pcs['response']),
                E.Connectivity(
                    self.connectivity.rule_properties.to_xml(document, E=E,
                                                             **kwargs))]
        if self.plasticity:
            args.append(E.Plasticity(
                self.plasticity.to_xml(document, E=E, **kwargs),
                *pcs['plasticity']))


# ./user/selection.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type,
             self.operation.to_xml(document, E=E, **kwargs),
             node.attr('name', self.name, **options))


# ./user/selection.py
def serialize_node(self, node, **options):  # @UnusedVariable
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
def serialize_node(self, node, **options):  # @UnusedVariable
    pass


# ./values.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type, repr(self.value))


# ./values.py
def serialize_node(self, node, **options):  # @UnusedVariable
    if self._datafile is None:
        return E.ArrayValue(
            *[E.ArrayValueRow(index=str(i), value=repr(v))
              for i, v in enumerate(self._values)])
    else:
        raise NotImplementedError(
            "TODO: Need to implement code to save data to external file")
        return E.ExternalArrayValue(
            node.attr('url', self.url, **options), node.attr('mimetype', self.mimetype, **options),
            node.attr('columnName', self.columnName, **options))


# ./values.py
def serialize_node(self, node, **options):  # @UnusedVariable
    return E(self.nineml_type,
             self.distribution.to_xml(document, E=E, **kwargs))
