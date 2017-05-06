

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
    node.child(self._value, **options)
    node.attr('units', self.units.name, **options)

# 
# # ./user/component.py
# def serialize_node(self, node, **options):  # @UnusedVariable
#     if self.url is None:
#         # If definition was created in Python, add component class
#         # reference to document argument before writing definition
#         try:
#             doc_obj = self.visitor.document[self._referred_to.name]
#             if doc_obj != self._referred_to:
#                 raise NineMLRuntimeError(
#                     "Cannot create reference for '{}' {} in the provided "
#                     "document due to name clash with existing {} object"
#                     .format(self._referred_to.name,
#                             type(self._referred_to), type(doc_obj)))
#         except NineMLNameError:
#             document.add(self._referred_to, **kwargs)
#     return super(Definition, self).to_xml(document, E=E, **kwargs)


# ./user/component.py
def serialize_node(self, node, **options):  # @UnusedVariable
    node.child(self._definition, **options)
    node.children(self.properties, **options)
    node.attr('name', self.name, **options)


# property
def serialize_node(self, node, **options):  # @UnusedVariable
    node.attr('name', self.name, **options)
    if node.later_version(2.0, equal=True):
        node.child(self._quantity, **options)
    else:
        node.child(self.value, **options)
        node.attr('units', self.units.name, **options)


# ./user/multi/port_exposures.py


# ./user/network.py
def serialize_node(self, node, **options):  # @UnusedVariable
    node.children(self.populations, **options)
    node.children(self.selections, **options)
    node.children(self.projections, **options)
    node.attr('name', self.name, **options)


# component array
def serialize_node(self, node, **options):  # @UnusedVariable
    node.attr('Size', self.size, in_body=True, **options)
    node.child(self.dynamics_properties, **options)
    node.attr('name', self.name, **options)


# connection group
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
    node.attr('Size', self.size, in_body=True)
    node.child(self.cell, within='Cell')
    node.attr('name', self.name, **options)


# ./user/port_connections.py
def serialize_node(self, node, **options):  # @UnusedVariable
    try:
        node.attr('sender_role', self.sender_role)
    except NineMLRuntimeError:
        node.attr('sender_name', self.sender_name)
    try:
        node.attr('receiver_role', self.receiver_role)
    except NineMLRuntimeError:
        node.attr('receiver_name', self.receiver_name)
    node.attr('send_port', self.send_port_name, **options)
    node.attr('receive_port', self.receive_port_name, **options)


# ./user/projection.py
def serialize_node(self, node, **options):  # @UnusedVariable
    if node.later_version(2.0, equal=True):
        node.child(self.pre, reference=True, within='Pre', **options)
        node.child(self.post, reference=True, within='Post', **options)
        node.child(self.connectivity.rule_properties, within='Connectivity',
                   **options)
        node.child(self.response, within='Response', **options),
        if self.plasticity is not None:
            node.child(self.plasticity, within='Plasticity', **options)
        node.child(self.delay, within='Delay', **options)
        node.children(self.port_connections, **options)
    else:
        endpoints = {}
        endpoints['source'] = node.child(
            self.pre, within='Source', reference=True, **options)
        endpoints['destination'] = node.child(
            self.post, within='Destination', reference=True, **options)
        node.child(self.connectivity.rule_properties, within='Connectivity',
                   **options)
        endpoints['response'] = node.child(self.response, within='Response',
                                           **options)
        if self.plasticity:
            endpoints['plasticity'] = node.child(
                self.plasticity, within='Plasticity', **options)
        for pc in self.port_connections:
            pc_elem = node.visitor.create_elem(
                'From' + self.v2tov1[pc.sender_role],
                parent=endpoints[pc.receiver_role], multiple=True)
            node.visitor.set_attr(pc_elem, 'send_port', pc.send_port_name,
                                  **options)
            node.visitor.set_attr(pc_elem, 'receive_port',
                                  pc.receive_port_name, **options)
        delay_elem = node.child(self.delay._value, within='Delay', **options)
        node.visitor.set_attr(delay_elem, 'units', self.delay.units.name,
                              **options)


# ./user/selection.py
def serialize_node(self, node, **options):  # @UnusedVariable
    node.child(self.operation, **options)
    node.attr('name', self.name, **options)


# ./user/selection.py
def serialize_node(self, node, **options):  # @UnusedVariable
    for i, item in enumerate(self.items):
        item_elem = node.child(item, within='Item', multiple=True, **options)
        node.visitor.set_attr(item_elem, 'index', i)


# ./values.py
def serialize_node(self, node, **options):  # @UnusedVariable
    node.body(repr(self.value), **options)


# ./values.py
def serialize_node(self, node, **options):  # @UnusedVariable
    if self._datafile is None:
        for i, value in enumerate(self._values):
            row_elem = node.visitor.create_elem(
                'ArrayValueRow', parent=node.serial_element, multiple=True,
                **options)
            node.visitor.set_attr(row_elem, 'index', i)
            node.visitor.set_attr(row_elem, 'value', value)
    else:
        node.attr('url', self.url, **options)
        node.attr('mimetype', self.mimetype, **options)
        node.attr('columnName', self.columnName, **options)


# ./values.py
def serialize_node(self, node, **options):  # @UnusedVariable
    node.child(self.distribution, **options)
