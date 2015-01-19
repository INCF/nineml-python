"""
This file defines the Port classes used in NineML

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.utility import ensure_valid_identifier  # , curry
from nineml.exceptions import NineMLRuntimeError
from abc import ABCMeta
from operator import and_
from ..base import BaseALObject
from ...units import dimensionless


class AnalogPort(Port):
    """AnalogPort

    An |AnalogPort| represents a continuous input or output to/from a
    Component. For example, this could be the membrane-voltage into a synapse
    component, or the current provided by a ion-channel.
    """

    defining_attributes = ('name', 'dimension')

    __metaclass__ = ABCMeta  # Ensure abstract base class isn't instantiated

    def __init__(self, name, dimension=None):
        super(AnalogPort, self).__init__(name)
        self._dimension = dimension if dimension is not None else dimensionless # TODO: This needs checking @IgnorePep8

    @property
    def dimension(self):
        """The dimension of the port"""
        return self._dimension

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        classstring = self.__class__.__name__
        return "{}('{}', dimension='{}')".format(classstring, self.name,
                                                 self.dimension)


class EventPort(Port):
    """EventPort

    An |EventPort| is a port that can transmit and receive discrete events at
    points in time. For example, an integrate-and-fire could 'send' events to
    notify other components that it had fired; or synapses could receive events
    to notify them to provide current to a post-synaptic neuron.
    """
    __metaclass__ = ABCMeta  # Ensure abstract base class isn't instantiated

    defining_attributes = ('name',)

    def __repr__(self):
        classstring = self.__class__.__name__
        return "{}('{}')".format(classstring, self.name)


class AnalogSendPort(AnalogPort):
    """AnalogSendPort

    An |AnalogSendPort| represents a continuous output from a
    Component. For example, this could be the membrane-voltage into a synapse
    component, or the current provided by a ion-channel.

    """
    mode = "send"

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_analogsendport(self, **kwargs)

    def is_incoming(self):
        return False


class AnalogReceivePort(AnalogPort):
    """AnalogReceivePort

    An |AnalogReceivePort| represents a continuous input to a
    Component. For example, this could be the membrane-voltage into a synapse
    component, or the current provided by a ion-channel.

    """
    mode = "recv"

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_analogreceiveport(self, **kwargs)

    def is_incoming(self):
        return True


class EventSendPort(EventPort):
    """EventSendPort

    An |EventSendPort| is a port that can transmit discrete events at
    points in time. For example, an integrate-and-fire could 'send' events to
    notify other components that it had fired.
    """
    mode = "send"

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_eventsendport(self, **kwargs)

    def is_incoming(self):
        return False


class EventReceivePort(EventPort):
    """EventReceivePort

    An |EventReceivePort| is a port that can receive discrete events at
    points in time. For example, synapses could receive events
    to notify them to provide current to a post-synaptic neuron.
    """
    mode = "recv"

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_eventreceiveport(self, **kwargs)

    def is_incoming(self):
        return True


class AnalogReducePort(AnalogPort):
    """AnalogReducePort

    An |AnalogReducePort| represents a collection of continuous inputs to a
    Component from a common type of input that can be reduced into a single
    input. For example, or the currents provided by a collection of
    ion-channels.

    .. note::

        Currently support ``reduce_op`` s are: ``+``.

    """
    mode = "reduce"
    _reduce_op_map = {'add': '+', '+': '+', }

    def __init__(self, name, dimension=None, reduce_op='+'):
        if reduce_op not in self._reduce_op_map.keys():
            err = ("%s('%s')" + "specified undefined reduce_op: '%s'") %\
                  (self.__class__.__name__, name, str(reduce_op))
            raise NineMLRuntimeError(err)
        super(AnalogReducePort, self).__init__(name, dimension)
        self._reduce_op = reduce_op

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_analogreduceport(self, **kwargs)

    @property
    def reduce_op(self):
        return self._reduce_op

    def __repr__(self):
        classstring = self.__class__.__name__
        return ("{}('{}', dimension='{}', op='{}')"
               .format(classstring, self.name, self.dimension, self.reduce_op))

    def is_incoming(self):
        return True
