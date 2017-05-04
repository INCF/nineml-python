
# ./annotations.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable @IgnorePep8
    assert strip_xmlns(element.tag) == cls.nineml_type
    assert not element.attrib
    if element.text is not None:
        assert not element.text.strip()
    branches = defaultdict(list)
    for child in element.getchildren():
        branches[cls._extract_key(child)].append(
            _AnnotationsBranch.from_xml(child))
    return cls(branches, **kwargs)


# ./document.py from_xml(cls, element, url=None, **kwargs):
@classmethod
def unserialize_node(cls, node, **options):
    url = cls._standardise_url(url)
    xmlns = extract_xmlns(element.tag)
    if xmlns not in ALL_NINEML:
        raise NineMLXMLError(
            "Unrecognised XML namespace '{}', can be one of '{}'"
            .format(xmlns[1:-1],
                    "', '".join(ns[1:-1] for ns in ALL_NINEML)))
    if element.tag[len(xmlns):] != cls.nineml_type:
        raise NineMLXMLError("'{}' document does not have a NineML root "
                             "('{}')".format(url, element.tag))
    # Initialise the document
    elements = {}
    # Loop through child elements, determine the class needed to extract
    # them and add them to the dictionary
    annotations = None
    for child in element.getchildren():
        if isinstance(child, etree._Comment):
            continue
        if child.tag.startswith(xmlns):
            nineml_type = child.tag[len(xmlns):]
            if nineml_type == Annotations.nineml_type:
                assert annotations is None, \
                    "Multiple annotations tags found"
                annotations = Annotations.from_xml(child, **kwargs)
                continue
            try:
                child_cls = cls._get_class_from_type(nineml_type)
            except NineMLXMLTagError:
                child_cls = cls._get_class_from_v1(nineml_type, xmlns,
                                                   child, element, url)
        else:
            raise NotImplementedError(
                "Cannot load '{}' element (extensions not implemented)"
                .format(child.tag))
        # Units use 'symbol' as their unique identifier (from LEMS) all
        # other elements use 'name'
        try:
            try:
                name = child.attrib['name']
            except KeyError:
                name = child.attrib['symbol']
        except KeyError:
            raise NineMLXMLError(
                "Missing 'name' (or 'symbol') attribute from document "
                "level object '{}'".format(child))
        if name in elements:
            raise NineMLXMLError(
                "Duplicate identifier '{ob1}:{name}'in NineML file '{url}'"
                .format(name=name, ob1=elements[name].cls.nineml_type,
                        ob2=child_cls.nineml_type, url=url or ''))
        elements[name] = cls._Unloaded(name, child, child_cls, kwargs)
    document = cls(*elements.values(), url=url, annotations=annotations)
    return document


# ./reference.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    xmlns = extract_xmlns(element.tag)
    if xmlns == NINEMLv1:
        name = element.text
        if name is None:
            raise NineMLXMLAttributeError(
                "References require the element name provided in the XML "
                "element text")
    else:
        name = node.attr('name', **options)
    url = node.attr('url', default=None, **options)
    return cls(name=name, document=document, url=url)



# ./units.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    name = node.attr('name', **options)
    # Get the attributes corresponding to the dimension symbols
    dim_args = dict((s, get_xml_attr(element, s, document, default=0,
                                     dtype=int, **kwargs))
                     for s in cls.dimension_symbols)
    return cls(name, document=document, **dim_args)



# ./units.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    name = node.attr('symbol', **options)
    dimension = document[node.attr('dimension', **options)]
    power = get_xml_attr(element, 'power', document, dtype=int,
                         default=0, **kwargs)
    offset = get_xml_attr(element, 'offset', document, dtype=float,
                          default=0.0, **kwargs)
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
    """docstring missing"""
    name = get_xml_attr(element, "name", document, **kwargs)
    definition = from_child_xml(element, (Definition, Prototype), document,
                                **kwargs)
    properties = from_child_xml(element, Property, document, multiple=True,
                                allow_none=True, **kwargs)
    if name in document:
        doc = document
    else:
        doc = None
    return cls(name, definition, properties=properties, document=doc)



# ./user/component.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    name = node.attr('name', **options)
    if extract_xmlns(element.tag) == NINEMLv1:
        value = from_child_xml(
            element,
            (SingleValue, ArrayValue, RandomValue),
            document, **kwargs)
        units = document[
            node.attr('units', **options)]
        quantity = Quantity(value, units)
    else:
        quantity = from_child_xml(
            element, Quantity, document, **kwargs)
    return cls(name=name, quantity=quantity)



# ./user/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    """docstring missing"""
    name = get_xml_attr(element, "name", document, **kwargs)
    definition = from_child_xml(element, (Definition, Prototype), document,
                                **kwargs)
    properties = from_child_xml(element, Property, document, multiple=True,
                                allow_none=True, **kwargs)
    initial_values = from_child_xml(element, Initial, document,
                                    multiple=True, allow_none=True,
                                    **kwargs)
    return cls(name, definition, properties=properties,
               initial_values=initial_values, document=document)



# ./user/multi/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):
    sub_component_properties = from_child_xml(
        element, SubDynamicsProperties, document, multiple=True,
        **kwargs)
    port_exposures = from_child_xml(
        element,
        (AnalogSendPortExposure, AnalogReceivePortExposure,
         AnalogReducePortExposure, EventSendPortExposure,
         EventReceivePortExposure), document, multiple=True,
        allow_none=True, **kwargs)
    port_connections = from_child_xml(
        element,
        (AnalogPortConnection, EventPortConnection), document,
        multiple=True, allow_none=True, **kwargs)
    return cls(name=node.attr('name', **options),
               sub_components=sub_component_properties,
               port_exposures=port_exposures,
               port_connections=port_connections,
               document=document)


# ./user/multi/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):
    dynamics_properties = from_child_xml(
        element, (DynamicsProperties, MultiDynamicsProperties), document,
        allow_reference=True, **kwargs)
    return cls(node.attr('name', **options),
               dynamics_properties)


# ./user/multi/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):
    dynamics = from_child_xml(
        element, (Dynamics, MultiDynamics), document,
        allow_reference=True, **kwargs)
    return cls(node.attr('name', **options),
               dynamics)


# ./user/multi/dynamics.py
@classmethod
def unserialize_node(cls, node, **options):
    sub_components = from_child_xml(
        element, SubDynamics, document, multiple=True,
        **kwargs)
    port_exposures = from_child_xml(
        element,
        (AnalogSendPortExposure, AnalogReceivePortExposure,
         AnalogReducePortExposure, EventSendPortExposure,
         EventReceivePortExposure), document, multiple=True,
        allow_none=True, **kwargs)
    port_connections = from_child_xml(
        element,
        (AnalogPortConnection, EventPortConnection), document,
        multiple=True, allow_none=True, **kwargs)
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
    populations = from_child_xml(element, Population, document,
                                 multiple=True, allow_reference='only',
                                 allow_none=True, **kwargs)
    projections = from_child_xml(element, Projection, document,
                                 multiple=True, allow_reference='only',
                                 allow_none=True, **kwargs)
    selections = from_child_xml(element, Selection, document,
                                multiple=True, allow_reference='only',
                                allow_none=True, **kwargs)
    network = cls(name=node.attr('name', **options),
                  populations=populations, projections=projections,
                  selections=selections, document=document)
    return network


# ./user/network.py
@classmethod
def unserialize_node(cls, node, **options):
    dynamics_properties = from_child_xml(
        element, DynamicsProperties, document,
        allow_reference=True, **kwargs)
    return cls(name=node.attr('name', **options),
               size=get_xml_attr(element, 'Size', document, in_block=True,
                                 dtype=int, **kwargs),
               dynamics_properties=dynamics_properties, document=document)


# ./user/network.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    # Get Name
    name = node.attr('name', **options)
    connectivity = from_child_xml(
        element, ConnectionRuleProperties, document, within='Connectivity',
        allow_reference=True, **kwargs)
    source = from_child_xml(
        element, ComponentArray, document, within='Source',
        allow_reference=True, allowed_attrib=['port'], **kwargs)
    destination = from_child_xml(
        element, ComponentArray, document, within='Destination',
        allow_reference=True, allowed_attrib=['port'], **kwargs)
    source_port = get_xml_attr(element, 'port', document,
                               within='Source', **kwargs)
    destination_port = get_xml_attr(element, 'port', document,
                                    within='Destination', **kwargs)
    delay = from_child_xml(element, Quantity, document, within='Delay',
                           allow_none=True, **kwargs)
    return cls(name=name, source=source, destination=destination,
               source_port=source_port, destination_port=destination_port,
               connectivity=connectivity, delay=delay, document=None)


# ./user/population.py
@classmethod
def unserialize_node(cls, node, **options):
    cell = from_child_xml(element,
                          (DynamicsProperties,
                           nineml.user.MultiDynamicsProperties), document,
                          allow_reference=True, within='Cell', **kwargs)
    return cls(name=node.attr('name', **options),
               size=get_xml_attr(element, 'Size', document, in_block=True,
                                 dtype=int, **kwargs),
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
    xmlns = extract_xmlns(element.tag)
    if xmlns == NINEMLv1:
        pre_within = 'Source'
        post_within = 'Destination'
        multiple_within = True
        # Get Delay
        delay_elem = expect_single(element.findall(NINEMLv1 + 'Delay'))
        units = document[
            get_xml_attr(delay_elem, 'units', document, **kwargs)]
        value = from_child_xml(
            delay_elem,
            (SingleValue, ArrayValue, RandomValue),
            document, **kwargs)
        delay = Quantity(value, units)
        if 'unprocessed' in kwargs:
            kwargs['unprocessed'][0].discard(delay_elem)
    else:
        pre_within = 'Pre'
        post_within = 'Post'
        multiple_within = False
        delay = from_child_xml(element, Quantity, document, within='Delay',
                               **kwargs)
    # Get Pre
    pre = from_child_xml(element, (Population, Selection), document,
                         allow_reference='only', within=pre_within,
                         multiple_within=multiple_within, **kwargs)
    post = from_child_xml(element, (Population, Selection), document,
                          allow_reference='only', within=post_within,
                          multiple_within=multiple_within, **kwargs)
    response = from_child_xml(element, DynamicsProperties, document,
                              allow_reference=True, within='Response',
                              multiple_within=multiple_within, **kwargs)
    plasticity = from_child_xml(element, DynamicsProperties, document,
                                allow_reference=True, within='Plasticity',
                                multiple_within=multiple_within,
                                allow_none=True, **kwargs)
    connection_rule_props = from_child_xml(
        element, ConnectionRuleProperties, document, within='Connectivity',
        allow_reference=True, **kwargs)
    if xmlns == NINEMLv1:
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
    else:
        port_connections = from_child_xml(
            element, (AnalogPortConnection, EventPortConnection),
            document, multiple=True, allow_none=True, **kwargs)
    return cls(name=name,
               pre=pre,
               post=post,
               response=response,
               plasticity=plasticity,
               connectivity=connection_rule_props,
               delay=delay,
               port_connections=port_connections,
               document=document)


# ./user/selection.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    # The only supported op at this stage
    op = from_child_xml(
        element, Concatenate, document, **kwargs)
    return cls(node.attr('name', **options), op,
               document=document)


# ./user/selection.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    items = []
    # Load references and indices from xml
    for it_elem in element.findall(extract_xmlns(element.tag) + 'Item'):
        items.append((
            node.attr('index', dtype=int, **options),
            from_child_xml(it_elem, Population, document,
                           allow_reference='only', **kwargs)))
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
    return cls(float(element.text))


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
            raise NineMLRuntimeError(
                "Negative indices found in array rows")
        if len(list(itertools.groupby(indices))) != len(indices):
            groups = [list(g) for g in itertools.groupby(indices)]
            raise NineMLRuntimeError(
                "Duplicate indices ({}) found in array rows".format(
                    ', '.join(str(g[0]) for g in groups if len(g) > 1)))
        if indices[-1] >= len(indices):
            raise NineMLRuntimeError(
                "Indices greater or equal to the number of array rows")
        return cls(values)


# ./values.py
@classmethod
def unserialize_node(cls, node, **options):  # @UnusedVariable
    distribution = from_child_xml(
        element, nineml.user.RandomDistributionProperties,
        document, allow_reference=True, **kwargs)
    return cls(distribution)
