from operator import and_
from .base import BaseULObject, E, NINEML
from .components import BaseComponent
from . import Reference
from .utility import check_tag
from ..utility import expect_single


class Projection(BaseULObject):

    """
    A collection of connections between two Populations.

    """
    element_name = "Projection"
    defining_attributes = ("name", "source", "destination", "connectivity",
                           "response", "plasticity")

    _comp_names = set(['source', 'destination', 'plasticity', 'response'])

    def __init__(self, name, source, destination, response,
                 plasticity, connectivity, port_connections):
        """
        Create a new projection.

        name             - a name for this Projection
        source           - the presynaptic Population
        destination      - the postsynaptic Population
        connectivity     - a Component>ConnectionRule instance, encapsulating
                           an algorithm for wiring up the connections.
        response         - a PostSynapticResponse instance that will be used
                            by all connections.
        port_connections - a list of `PortConnection` tuples
                           (sender, receiver, send_port, receive_port) that
                           define the connections between the 4 components
                           of the projection, 'source', 'destination',
                           'response', 'plasticity'. 'sender' and 'receiver'
                           must be one of these 4 component names and
                           'send_port' and 'receive_port' must be the name of
                           one of the ports in the corresponding components.
        """
        self.name = name
        self.source = source
        self.destination = destination
        self.connectivity = connectivity
        self.response = response
        self.plasticity = plasticity
        self.port_connections = port_connections
        for pc in self.port_connections:
            pc.set_projection(self)
        self._check_port_connections()

    def __eq__(self, other):
        test_attributes = ["name", "source", "destination",
                           "connectivity", "response", "plasticity",
                           "port_connections"]
        return reduce(and_, (getattr(self, attr) == getattr(other, attr)
                             for attr in test_attributes))

    def _check_port_connections(self):
        for pc in self.port_connections:
            try:
                pc.sender.analog_send_ports[pc.send_port]
                try:
                    pc.receiver.analog_receive_ports[pc.receive_port]
                except KeyError:
                    raise KeyError("No analog receive port named '{}' in {} "
                                   "component, '{}'."
                                   .format(pc.receive_port, pc.receiver_role,
                                           pc.receiver.name))
            except KeyError:
                try:
                    pc.sender.event_send_ports[pc.send_port]
                    try:
                        pc.receiver.event_receive_ports[pc.receive_port]
                    except KeyError:
                        raise KeyError("No analog receive port named '{}' in "
                                       "{} component, '{}'."
                                       .format(pc.receive_port,
                                               pc.receiver_role,
                                               pc.receiver.name))
                except KeyError:
                    raise KeyError("'{}' send port was not found in {} "
                                   "component, '{}'"
                                   .format(pc.send_port, pc.sender_role,
                                           pc.sender.name))

    def get_components(self):
        components = []
        for name in ('connectivity', 'response', 'plasticity'):
            component = getattr(self, name)
            if component is not None:
                components.append(component)
        return components

    def to_xml(self):
        return E(self.element_name,
                 E.Source(self.source.to_xml()),
                 E.Destination(self.destination.to_xml()),
                 E.Connectivity(self.connectivity.to_xml()),
                 E.Response(self.response.to_xml()),
                 E.Plasticity(self.plasticity.to_xml()),
                 E.response_ports(*[E.port_connection(port1=a, port2=b)
                                    for a, b in self.response_ports]),
                 E.connection_ports(*[E.port_connection(port1=a, port2=b)
                                      for a, b in self.connection_ports]),
                 name=self.name)

    @classmethod
    def from_xml(cls, element, context):
        check_tag(element, cls)
        comps = {}
        port_connections = []
        # Loop through Source, Destination, Response, Plasticity tags resolve
        # references and extract port connections
        for name in cls._comp_names:
            # Get element for component name
            child = expect_single(element.findall(NINEML + name.capitalize()))
            # Get component reference
            comps[name] = Reference.from_xml(child.find(NINEML + 'Reference'),
                                             context)
            # Loop through all incoming port connections and add them to list
            for sender in cls._comp_names - set([name]):
                for pc in child.findall(NINEML + 'From' + sender.capitalize()):
                    port_connections.append(
                                 PortConnection(sender, name, pc.get('sender'),
                                                pc.get('receiver')))
        return cls(name=element.attrib["name"],
                   connectivity=context.resolve_ref(
                                          element.find(NINEML + "Connecivity"),
                                          BaseComponent),
                   port_connections=port_connections,
                   **comps)


class PortConnection(object):
    """
    Specifies the connection of a send port with a receive port between two
    components in the projection
    """

    def __init__(self, sender_role, receiver_role, send_port, receive_port):
        """
        sender_role   -- one of 'source', 'destination', 'plasticity' or
                         'response'
        receiver_role -- one of 'source', 'destination', 'plasticity' or
                         'response'
        send_port     -- A port name of a send port in the sender component
        receive_port  -- A port name of a send port in the receiver component
        """
        if sender_role not in Projection._comp_names:
            raise Exception("Sender must be one of '{}'"
                            .format("', '".join(Projection._comp_names)))
        if receiver_role not in Projection._comp_names:
            raise Exception("Receiver must be one of '{}'"
                            .format("', '".join(Projection._comp_names)))
        if sender_role == receiver_role:
            raise Exception("Sender and Receiver cannot be the same ('{}')"
                            .format(sender_role))
        self.sender_role = sender_role
        self.receiver_role = receiver_role
        self.send_port = send_port
        self.receive_port = receive_port
        self.sender = None
        self.receiver = None

    def set_projection(self, projection):
        self.sender = getattr(projection, self.sender_role)
        self.receiver = getattr(projection, self.receiver_role)
