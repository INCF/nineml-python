"""
Definitions for the ComponentQuery Class

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from itertools import chain
from nineml.utils import filter_expect_single
from ...componentclass.utils.queryer import ComponentQueryer


class DynamicsQueryer(ComponentQueryer):

    """
    DynamicsQueryer provides a way of adding methods to query a
    ComponentClass object, without polluting the class
    """

    def __init__(self, component_class):
        """Constructor for the DynamicsQueryer"""
        self.component_class = component_class

    @property
    def ports(self):
        """Return an iterator over all the port (Event & Analog) in the
        component_class"""
        return chain(super(DynamicsQueryer, self).ports,
                     self.component_class.analog_ports,
                     self.component_class.event_ports)

    # Find basic properties by name
    def regime(self, name=None,):
        """Find a regime in the component_class by name"""
        assert isinstance(name, basestring)

        return filter_expect_single(self.component_class.regimes,
                                    lambda r: r.name == name)

    # Query Ports:
    @property
    def event_send_ports(self):
        """Get the ``send`` EventPorts"""
        return sorted(self.component_class.event_send_ports,
                      key=lambda p: p.name)

    @property
    def event_recv_ports(self):
        """Get the ``recv`` EventPorts"""
        return sorted(self.component_class.event_receive_ports,
                      key=lambda p: p.name)

    @property
    def analog_reduce_ports(self):
        """Get the ``reduce`` AnalogPorts"""
        return sorted(self.component_class.analog_reduce_ports,
                      key=lambda p: p.name)

    @property
    def analog_send_ports(self):
        """Get the ``send`` AnalogPorts"""
        return sorted(self.component_class.analog_send_ports,
                      key=lambda p: p.name)

    @property
    def analog_recv_ports(self):
        """Get the ``recv`` AnalogPorts"""
        return sorted(self.component_class.analog_receive_ports,
                      key=lambda p: p.name)

    @property
    def analog_ports_map(self):
        """Returns a map of names to |AnalogPort| objects"""
        return dict([(p.name, p) for p in self.component_class.analog_ports])

    @property
    def event_ports_map(self):
        """Returns a map of names to |EventPort| objects"""
        return dict([(p.name, p) for p in self.component_class.event_ports])

    @property
    def recurse_all_components(self):
        """
        Returns an iterator over this component_class and all subcomponents
        """
        yield self.component_class
        for subcomponent in self.component_class.subnodes.values():
            for subcomp in subcomponent.query.recurse_all_components:
                yield subcomp
