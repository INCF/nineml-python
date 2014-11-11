from operator import and_
from .base import BaseULObject, E, NINEML
from collections import defaultdict
from .components import BaseComponent
from itertools import chain
import nineml.user_layer
from .utility import check_tag
from ..utility import expect_single, expect_none_or_single
from ..exceptions import NineMLRuntimeError


class Projection(BaseULObject):

    """
    A collection of connections between two Populations.

    """
    element_name = "Projection"
    defining_attributes = ("name", "source", "destination", "connectivity",
                           "response", "plasticity", "port_connections",
                           "delay")

    _component_roles = set(['source', 'destination', 'plasticity', 'response'])

    def __init__(self, name, source, destination, response,
                 plasticity, connectivity, delay, port_connections):
        """
        Create a new projection.

        name             -- a name for this Projection
        source           -- the presynaptic Population
        destination      -- the postsynaptic Population
        response         -- a Component>Dynamics that defines the post-synaptic
                            response of the connections
        plasticity       -- a Component>Dynamics that defines the plasticity
                            rule on the response synaptic response
        connectivity     -- a Component>ConnectionRule instance, encapsulating
                            an algorithm for wiring up the connections.
        delay            -- a Quantity object specifying the delay of the
                            connections
        port_connections -- a list of `PortConnection` tuples
                            (sender, receiver, send_port, receive_port) that
                            define the connections between the 4 components
                            of the projection, 'source', 'destination',
                            'response', 'plasticity'. 'sender' and 'receiver'
                            must be one of these 4 component names and
                            'send_port' and 'receive_port' must be the name of
                            one of the ports in the corresponding components.
        """
        super(Projection, self).__init__()
        self.name = name
        self.source = source
        self.destination = destination
        self.response = response
        self.plasticity = plasticity
        self.connectivity = connectivity
        self.delay = delay
        self.port_connections = sorted(port_connections,
                                       key=lambda x: (x._send_role,
                                                      x._receive_role,
                                                      x.send_port,
                                                      x.receive_port))
        for pc in self.port_connections:
            pc.set_projection(self)
        self._check_port_connections()

    def __repr__(self):
        return ('Projection(name="{}", source={}, destination={}, '
                'connectivity={}, response={}{}, delay={}, '
                'with {} port-connections)'
                .format(self.name, repr(self.source), repr(self.destination),
                        repr(self.connectivity), repr(self.response),
                        ('plasticity={}'.format(repr(self.plasticity))
                         if self.plasticity else ''), repr(self.delay),
                        len(self.port_connections)))

    def _check_port_connections(self):
        for pc in self.port_connections:
            if pc.send_port in (p.name
                                for p in pc.send_class.analog_send_ports):
                if (pc.receive_port not in
                    (p.name
                     for p in chain(pc.receive_class.analog_receive_ports,
                                    pc.receive_class.analog_reduce_ports))):
                    msg = ("No analog receive port named '{}' in {} component,"
                           " '{}'.".format(pc.receive_port, pc._receive_role,
                                           pc.receive_class.name))
                    raise NineMLRuntimeError(msg)
            elif pc.send_port in (p.name
                                for p in pc.send_class.event_send_ports):
                if (pc.receive_port not in
                    (p.name for p in pc.receive_class.event_receive_ports)):
                    msg = ("No event receive port named '{}' in {} component, "
                           "'{}'.".format(pc.receive_port, pc._receive_role,
                                           pc.receive_class.name))
                    raise NineMLRuntimeError(msg)
            else:
                msg = ("'{}' send port was not found in {} component, '{}'"
                       .format(pc.send_port, pc._send_role,
                               pc.send_class.name))
                raise NineMLRuntimeError(msg)

    def get_components(self):
        components = []
        for name in ('connectivity', 'response', 'plasticity'):
            component = getattr(self, name)
            if component is not None:
                components.append(component)
        return components

    def _to_xml(self):
        pcs = defaultdict(list)
        for pc in self.port_connections:
            pcs[pc._receive_role].append(
                                      E('From' + pc._send_role.capitalize(),
                                      send_port=pc.send_port,
                                      receive_port=pc.receive_port))
        args = [E.Source(self.source.to_xml(), *pcs['source']),
                 E.Destination(self.destination.to_xml(), *pcs['destination']),
                 E.Connectivity(self.connectivity.to_xml()),
                 E.Response(self.response.to_xml(), *pcs['response'])]
        if self.plasticity:
            args.append(E.Plasticity(self.plasticity.to_xml(),
                                     *pcs['plasticity']))
        args.append(E.Delay(self.delay.to_xml()))
        return E(self.element_name, *args, name=self.name)

    @classmethod
    def from_xml(cls, element, context):
        check_tag(element, cls)
        # Get Name
        name = element.get('name')
        # Get Source
        source_elem = expect_single(element.findall(NINEML + 'Source'))
        source = nineml.user_layer.Reference.from_xml(
                      expect_single(source_elem.findall(NINEML + 'Reference')),
                      context)
        # Get Destination
        dest_elem = expect_single(element.findall(NINEML + 'Destination'))
        destination = nineml.user_layer.Reference.from_xml(
                        expect_single(dest_elem.findall(NINEML + 'Reference')),
                        context)
        # Get Response
        response = context.resolve_ref(
                           expect_single(element.findall(NINEML + 'Response')),
                           BaseComponent)
        # Get Plasticity
        pl_elem = expect_none_or_single(element.findall(NINEML + 'Plasticity'))
        if pl_elem is not None:
            plasticity = context.resolve_ref(pl_elem, BaseComponent)
        else:
            plasticity = None
        # Get Connectivity
        connectivity = context.resolve_ref(
                                expect_single(element.findall(NINEML +
                                                              'Connectivity')),
                                BaseComponent)
        # Get Delay
        delay = nineml.user_layer.Quantity.from_xml(
                                 expect_single(element.find(NINEML + 'Delay')),
                                 context)
        # Get port connections by Loop through 'source', 'destination',
        # 'response', 'plasticity' tags and extracting the "From*" elements
        port_connections = []
        for receive_role in cls._component_roles:
            # Get element for component name
            comp_elem = element.find(NINEML + receive_role.capitalize())
            if comp_elem is not None:  # Plasticity is not required
                # Loop through all incoming port connections and add them to
                # list
                for sender_role in cls._component_roles:
                    pc_elems = comp_elem.findall(
                                    NINEML + 'From' + sender_role.capitalize())
                    if sender_role == receive_role and pc_elems:
                        msg = ("{} port connection receives from itself in "
                               "Projection '{}'".format(name, name))
                        raise NineMLRuntimeError(msg)
                    if (sender_role is 'plasticity' and plasticity is None and
                        len(pc_elems)):
                        msg = ("{} port connection receives from plasticity, "
                               "which wasn't provided for Projection '{}'"
                               .format(receive_role, name))
                        raise NineMLRuntimeError(msg)
                    for pc in pc_elems:
                        port_connections.append(
                                     PortConnection(sender_role, receive_role,
                                                    pc.get('send_port'),
                                                    pc.get('receive_port')))
        return cls(name=element.attrib["name"],
                   source=source,
                   destination=destination,
                   response=response,
                   plasticity=plasticity,
                   connectivity=connectivity,
                   delay=delay,
                   port_connections=port_connections)


class PortConnection(object):
    """
    Specifies the connection of a send port with a receive port between two
    components in the projection
    """

    def __init__(self, sender, receiver, send_port, receive_port):
        """
        sender_role   -- one of 'source', 'destination', 'plasticity' or
                         'response'
        receiver_role -- one of 'source', 'destination', 'plasticity' or
                         'response'
        send_port     -- A port name of a send port in the sender component
        receive_port  -- A port name of a send port in the receiver component
        """
        if sender not in Projection._component_roles:
            raise Exception("Sender must be one of '{}'"
                            .format("', '".join(Projection._component_roles)))
        if receiver not in Projection._component_roles:
            raise Exception("Receiver must be one of '{}'"
                            .format("', '".join(Projection._component_roles)))
        if sender == receiver:
            raise Exception("Sender and Receiver cannot be the same ('{}')"
                            .format(sender))
        if not isinstance(send_port, basestring):
            raise NineMLRuntimeError("invalid send port '{}'"
                                     .format(send_port))
        if not isinstance(receive_port, basestring):
            raise NineMLRuntimeError("invalid receive port '{}'"
                                     .format(receive_port))
        self._send_role = sender
        self._receive_role = receiver
        self.send_port = send_port
        self.receive_port = receive_port
        self._projection = None

    def __eq__(self, other):
        return  (self._send_role == other._send_role and
                 self._receive_role == other._receive_role and
                 self.send_port == other.send_port and
                 self.receive_port == other.receive_port)

    def set_projection(self, projection):
        self._projection = projection

    @property
    def sender(self):
        assert self._projection is not None, ("Projection not set on port "
                                              "connection")
        return getattr(self._projection, self._send_role)

    @property
    def receiver(self):
        assert self._projection is not None, ("Projection not set on port "
                                              "connection")
        return getattr(self._projection, self._receive_role)

    @property
    def send_class(self):
        return self._get_class(self.sender)

    @property
    def receive_class(self):
        return self._get_class(self.receiver)

    def _get_class(self, comp):
        # Resolve ref
        if isinstance(comp, nineml.user_layer.Reference):
            comp = comp.user_layer_object
        # Get component class
        if isinstance(comp, nineml.user_layer.Population):
            comp_class = comp.cell.component_class
        elif isinstance(comp, nineml.user_layer.Component):
            comp_class = comp.component_class
        elif isinstance(comp, nineml.user_layer.Selection):
            print ("Warning: port connections have not been check for '{}'"
                   "Selection".format(comp.name))
        else:
            assert False, ("Invalid '{}' object in port connection"
                           .format(type(comp)))
        return comp_class
