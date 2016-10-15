"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from collections import defaultdict
from .base import BaseValidator
from nineml.exceptions import NineMLRuntimeError
# from nineml.abstraction.componentclass.namespace import NamespaceAddress


class PortConnectionsComponentValidator(BaseValidator):

    """Check that all the port connections point to a port, and that
    each send & recv port only has a single connection.
    """

    def __init__(self, component_class):
        BaseValidator.__init__(self, require_explicit_overrides=False)

        self.ports = defaultdict(list)
        self.portconnections = list()

        self.visit(component_class)

        connected_recv_ports = set()

        # Check for duplicate connections in the
        # portconnections. This can only really happen in the
        # case of connecting 'send to reduce ports' more than once.
        seen_port_connections = set()
        for pc in self.portconnections:
            if pc in seen_port_connections:
                err = 'Duplicate Port Connection: %s -> %s' % (pc[0], pc[1])
                raise NineMLRuntimeError(err)
            seen_port_connections.add(pc)

        # Check each source and sink exist,
        # and that each recv port is connected at max once.
        for src, sink in self.portconnections:
            if src not in self.ports:
                raise NineMLRuntimeError(
                    'Unable to find port specified in connection: %s' %
                    (src))
            if self.ports[src].is_incoming():
                raise NineMLRuntimeError(
                    'Port was specified as a source, but is incoming: %s' %
                    (src))

            if sink not in self.ports:
                raise NineMLRuntimeError(
                    'Unable to find port specified in connection: %s' %
                    (sink))

            if not self.ports[sink].is_incoming():
                raise NineMLRuntimeError(
                    'Port was specified as a sink, but is not incoming: %s' %
                    (sink))

            if self.ports[sink].mode == 'recv':
                if self.ports[sink] in connected_recv_ports:
                    raise NineMLRuntimeError(
                        "Port was 'recv' and specified twice: %s" % (sink))
                connected_recv_ports.add(self.ports[sink])

    def _action_port(self, port):
        pass
#         port_address = NamespaceAddress.concat(namespace, port.name)
#         if port_address in self.ports:
#             raise NineMLRuntimeError(
#                 'Duplicated Name for port found: %s' % port_address)
#         self.ports[port_address] = port

    def action_componentclass(self, component_class):
        pass
#         for src, sink in component_class.port_connections:
#             # print 'Adding Port:',full_src
#             # print 'Adding Port:',full_sink
#             self.portconnections.append((src, sink))
