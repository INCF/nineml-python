"""
Definitions for the ComponentQuery Class

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from itertools import chain
from nineml.utility import filter_expect_single
from ...componentclass.utils.queryer import ComponentQueryer


class DynamicsQueryer(ComponentQueryer):

    """
    DynamicsQueryer provides a way of adding methods to query a
    ComponentClass object, without polluting the class
    """

    def __init__(self, componentclass):
        """Constructor for the ComponentQueryer"""
        self.component = componentclass

    @property
    def ports(self):
        """Return an iterator over all the port (Event & Analog) in the
        component"""
        return chain(self.component.analog_ports, self.component.event_ports)

    # Find basic properties by name
    def regime(self, name=None,):
        """Find a regime in the component by name"""
        assert isinstance(name, basestring)

        return filter_expect_single(self.component.regimes,
                                    lambda r: r.name == name)

    # Query Ports:
    @property
    def event_send_ports(self):
        """Get the ``send`` EventPorts"""
        return sorted(self.component.event_send_ports,
                      key=lambda p: p.name)

    @property
    def event_recv_ports(self):
        """Get the ``recv`` EventPorts"""
        return sorted(self.component.event_receive_ports,
                      key=lambda p: p.name)

    @property
    def analog_reduce_ports(self):
        """Get the ``reduce`` AnalogPorts"""
        return sorted(self.component.analog_reduce_ports,
                      key=lambda p: p.name)

    @property
    def analog_send_ports(self):
        """Get the ``send`` AnalogPorts"""
        return sorted(self.component.analog_send_ports,
                      key=lambda p: p.name)

    @property
    def analog_recv_ports(self):
        """Get the ``recv`` AnalogPorts"""
        return sorted(self.component.analog_receive_ports,
                      key=lambda p: p.name)

    @property
    def analog_ports_map(self):
        """Returns a map of names to |AnalogPort| objects"""
        return dict([(p.name, p) for p in self.component.analog_ports])

    @property
    def event_ports_map(self):
        """Returns a map of names to |EventPort| objects"""
        return dict([(p.name, p) for p in self.component.event_ports])

    @property
    def parameters_map(self):
        """Returns a map of names to |Parameter| objects"""
        return dict([(p.name, p) for p in self.component.parameters])

    # Used by the flattening code:
    def get_fully_qualified_port_connections(self):
        """Used by the flattening code.

        This method returns a list of tuples of the
        the fully-qualified port connections.
        For example,
        [("a.b.C","d.e.F"),("g.h.I","j.k.L"), ..., ("u.W","x.y.Z") ]
        but note that it is not ``string`` objects that are returned, but
        NamespaceAddress objects.
        """
        namespace = self.component.get_node_addr()
        conns = []
        for src, sink in self.component.portconnections:
            src_new = namespace.get_subns_addr(src)
            sink_new = namespace.get_subns_addr(sink)
            conns.append((src_new, sink_new))
        return conns

    @property
    def recurse_all_components(self):
        """Returns an iterator over this component and all subcomponents"""
        yield self.component
        for subcomponent in self.component.subnodes.values():
            for subcomp in subcomponent.query.recurse_all_components:
                yield subcomp
