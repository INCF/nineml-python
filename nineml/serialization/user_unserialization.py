
# ./units.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    name = node.attr('name', **options)
    # Get the attributes corresponding to the dimension symbols
    dim_args = dict((s, node.attr(s, default=0, dtype=int, **options))
                     for s in cls.dimension_symbols)
    return cls(name, document=node.visitor.document, **dim_args)



# ./units.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    name = node.attr('symbol', **options)
    dimension = document[node.attr('dimension', **options)]
    power = node.attr('power', dtype=int, default=0, **kwargs)
    offset = node.attr('offset', dtype=float, default=0.0, **kwargs)
    return cls(name, dimension, power, offset=offset, document=document)



# ./units.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    value = BaseValue.from_parent_xml(element, document, **kwargs)
    try:
        units_str = node.attr('units', **options)
    except KeyError:
        raise NineMLRuntimeError(
            "{} element '{}' is missing 'units' attribute (found '{}')"
            .format(element.tag, element.get('name', ''),
                    "', '".join(element.attrib.iterkeys())))
    try:
        units = document[units_str]
    except KeyError:
        raise NineMLNameError(
            "Did not find definition of '{}' units in the current "
            "document.".format(units_str))
    return cls(value=value, units=units)



# ./user/component.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    name = node.attr('name', **kwargs)
    definition = node.child((Definition, Prototype), **options)
    properties = node.children(Property, **options)
    if name in document:
        doc = document
    else:
        doc = None
    return cls(name, definition, properties=properties, document=doc)



# ./user/component.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    name = node.attr('name', **options)
    if node.later_version(2.0, equal=True):
        quantity = node.child(Quantity, **options)
    else:
        value = node.child((SingleValue, ArrayValue, RandomValue), **options)
        units = document[node.attr('units', **options)]
        quantity = Quantity(value, units)
    return cls(name=name, quantity=quantity)



# ./user/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    name = node.attr('name', **kwargs)
    definition = node.child((Definition, Prototype), **options)
    properties = node.children(Property, **options)
    initial_values = node.children(Initial, **options)
    return cls(name, definition, properties=properties,
               initial_values=initial_values, document=document)



# ./user/multi/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):
    sub_component_properties = node.children(SubDynamicsProperties, **options)
    port_exposures = node.children((AnalogSendPortExposure, AnalogReceivePortExposure, AnalogReducePortExposure, EventSendPortExposure, EventReceivePortExposure), **options)
    port_connections = node.children((AnalogPortConnection, EventPortConnection), **options)
    return cls(name=node.attr('name', **options),
               sub_components=sub_component_properties,
               port_exposures=port_exposures,
               port_connections=port_connections,
               document=document)


# ./user/multi/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):
    dynamics_properties = node.child((DynamicsProperties, MultiDynamicsProperties), **options)
    return cls(node.attr('name', **options),
               dynamics_properties)


# ./user/multi/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):
    dynamics = node.child((Dynamics, MultiDynamics), **options)
    return cls(node.attr('name', **options),
               dynamics)


# ./user/multi/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):
    sub_components = node.children(SubDynamics, document, **options)
    port_exposures = node.children(
        (AnalogSendPortExposure, AnalogReceivePortExposure,
         AnalogReducePortExposure, EventSendPortExposure,
         EventReceivePortExposure), **options)
    port_connections = node.children(
        (AnalogPortConnection, EventPortConnection), **options)
    return cls(name=node.attr('name', **options),
               sub_components=sub_components,
               port_exposures=port_exposures,
               port_connections=port_connections)


# ./user/multi/port_exposures.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    return cls(name=node.attr('name', **options),
               component=node.attr('sub_component', **options),
               port=node.attr('port', **options))


# ./user/network.py
@classmethod
def unserialize_node(cls, node, **options):
    populations = node.children(Population, reference=True, **options)
    projections = node.children(Projection, reference=True, **options)
    selections = node.children(Selection, reference=True, **options)
    network = cls(name=node.attr('name', **options),
                  populations=populations, projections=projections,
                  selections=selections, document=document)
    return network


# ./user/network.py
@classmethod
def unserialize_node(cls, node, **options):
    dynamics_properties = node.child(DynamicsProperties, **options)
    return cls(name=node.attr('name', **options),
               size=node.attr('Size', in_body=True, dtype=int, **kwargs),
               dynamics_properties=dynamics_properties, document=document)


# ./user/network.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    # Get Name
    name = node.attr('name', **options)
    connectivity = node.child(ConnectionRuleProperties, within='Connectivity', **options)
    source = node.child(ComponentArray, within='Source', allowed_attrib=['port'], **options)
    destination = node.child(ComponentArray, within='Destination', allowed_attrib=['port'], **options)
    source_port = node.attr('port', within='Source', **kwargs)
    destination_port = node.attr('port', within='Destination', **kwargs)
    delay = node.child(Quantity, within='Delay', allow_none=True, **options)
    return cls(name=name, source=source, destination=destination,
               source_port=source_port, destination_port=destination_port,
               connectivity=connectivity, delay=delay, document=None)


# ./user/population.py
@classmethod
def unserialize_node(cls, node, **options):
    cell = node.child((DynamicsProperties, nineml.user.MultiDynamicsProperties), within='Cell', **options)
    return cls(name=node.attr('name', **options),
               size=node.attr('Size', in_body=True, dtype=int, **kwargs),
               cell=cell, document=document)


# ./user/port_connections.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    return cls(send_port=node.attr('send_port', **options),
               receive_port=node.attr('receive_port', **options),
               sender_role=node.attr('sender_role', default=None, **options),
               receiver_role=node.attr('receiver_role', default=None, **options),
               sender_name=node.attr('sender_name', default=None, **options),
               receiver_name=node.attr('receiver_name', default=None, **options))


# ./user/projection.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    # Get Name
    name = node.attr('name', **options)
    if node.later_version(2.0, equal=True):
        pre_within = 'Pre'
        post_within = 'Post'
        multiple_within = False
        delay = node.child(Quantity, within='Delay', **options)
    else:
        pre_within = 'Source'
        post_within = 'Destination'
        multiple_within = True
        # Get Delay
        delay_elem = node.visitor.get_single_child('Delay')
        units = node.visitor.document[
            node.visitor.get_attr(delay_elem, 'units', **options)]
        nineml_type, value_elem = node.visitor.get_single_child(
            delay_elem, ('SingleValue', 'ArrayValue', 'RandomValue'),
            **options)
        value = node.visitor.visit(
            value_elem,
            node.visitor._get_nineml_class(nineml_type, value_elem), **options)
        delay = Quantity(value, units)
    # Get Pre
    pre = node.child(
        (Population, Selection), reference=True, within=pre_within, **options)
    post = node.child(
        (Population, Selection), reference=True, within=post_within, **options)
    response = node.child(DynamicsProperties, within='Response', **options)
    plasticity = node.child(
        DynamicsProperties, reference=True, within='Plasticity',
        allow_none=True, **options)
    connection_rule_props = node.child(
        ConnectionRuleProperties, within='Connectivity', **options)
    if node.later_version(2.0, equal=True):
        port_connections = node.children(
            (AnalogPortConnection, EventPortConnection), **options)
    else:
        port_connections = []
        for receive_name in cls.version1_nodes:
            try:
                receive_elem = expect_single(
                    element.findall(NINEMLv1 + receive_name))
            except NineMLRuntimeError:
                if receive_name == 'Plasticity':
                    continue
                else:
                    raise
            receiver = eval(cls.v1tov2[receive_name])
            for send_name in cls.version1_nodes:
                for from_elem in receive_elem.findall(NINEMLv1 + 'From' +
                                                      send_name):
                    send_port_name = get_xml_attr(
                        from_elem, 'send_port', document, **kwargs)
                    receive_port_name = get_xml_attr(
                        from_elem, 'receive_port', document, **kwargs)
                    receive_port = receiver.port(receive_port_name)
                    if isinstance(receive_port, EventReceivePort):
                        pc_cls = EventPortConnection
                    else:
                        pc_cls = AnalogPortConnection
                    port_connections.append(pc_cls(
                        receiver_role=cls.v1tov2[receive_name],
                        sender_role=cls.v1tov2[send_name],
                        send_port=send_port_name,
                        receive_port=receive_port_name))
    return cls(name=name,
               pre=pre,
               post=post,
               response=response,
               plasticity=plasticity,
               connectivity=connection_rule_props,
               delay=delay,
               port_connections=port_connections,
               document=node.visitor.document)


# ./user/selection.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    # The only supported op at this stage
    op = node.child(Concatenate, **options)
    return cls(node.attr('name', **options), op,
               document=node.visitor.document)


# ./user/selection.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    items = []
    # Load references and indices from xml
    for it_elem in element.findall(extract_xmlns(element.tag) + 'Item'):
        items.append((
            node.attr('index', dtype=int, **options),
            from_child_xml(it_elem, Population, document, reference=True, **kwargs)))
        try:
            kwargs['unprocessed'][0].discard(it_elem)
        except KeyError:
            pass
    # Sort by 'index' attribute
    indices, items = zip(*sorted(items, key=itemgetter(0)))
    indices = [int(i) for i in indices]
    if len(indices) != len(set(indices)):
        raise ValueError("Duplicate indices found in Concatenate list ({})"
                         .format(indices))
    if indices[0] != 0:
        raise ValueError("Indices of Concatenate items must start from 0 "
                         "({})".format(indices))
    if indices[-1] != len(indices) - 1:
        raise ValueError("Missing indices in Concatenate items ({}), list "
                         "must be contiguous.".format(indices))
    return cls(*items)  # Strip off indices used to sort elements


# ./values.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    return cls(node.body(dtype=int))


# ./values.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    if element.tag == 'ExternalArrayValue':
        url = node.attr('url', **options)
        with contextlib.closing(urlopen(url)) as f:
            # FIXME: Should use a non-numpy version of this load function
            values = numpy.loadtxt(f)
        return cls(values, (node.attr('url', **options),
                            node.attr('mimetype', **options),
                            node.attr('columnName', **options)))
    else:
        rows = [(node.attr('index', dtype=int, **options),
                 node.attr('value', dtype=float, **options))
                for e in get_subblocks(element, 'ArrayValueRow', **kwargs)]
        sorted_rows = sorted(rows, key=itemgetter(0))
        indices, values = zip(*sorted_rows)
        if indices[0] < 0:
            raise NineMLSerializationError(
                "Negative indices found in array rows")
        if len(list(itertools.groupby(indices))) != len(indices):
            groups = [list(g) for g in itertools.groupby(indices)]
            raise NineMLSerializationError(
                "Duplicate indices ({}) found in array rows".format(
                    ', '.join(str(g[0]) for g in groups if len(g) > 1)))
        if indices[-1] >= len(indices):
            raise NineMLSerializationError(
                "Indices greater or equal to the number of array rows")
        return cls(values)


# ./values.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    distribution = node.child(nineml.user.RandomDistributionProperties, **options)
    return cls(distribution)
