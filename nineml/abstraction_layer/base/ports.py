"""
This file defines the Port classes used in NineML

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from abc import ABCMeta
from .base import BaseALObject
from ..units import dimensionless
from ...utility import ensure_valid_identifier


class Port(BaseALObject):

    """
    Base class for |PropertySendPort|, |PropertyReceivePort|, |IndexSendPort|,
    |IndexReceivePort| and |PropertyReducePort|.

    In general, a port has a ``name``, which can be used to reference it,
    and a ``mode``, which specifies whether it sends or receives information.

    Generally, a send port can be connected to receive port to allow different
    components to communicate.

    |PropertySendPort| and |IndexSendPort|s can be connected to any number of
    |PropertyReceivePort| and |IndexReceivePort|s respectively, but each
    |PropertyReceivePort| and |IndexReceivePort| can only be connected to a
    single |PropertySendPort| and |IndexSendPort| respectively.

    """
    __metaclass__ = ABCMeta  # Ensure abstract base class isn't instantiated

    def __init__(self, name):
        """ Port Constructor.

        `name` -- The name of the port, as a `string`
        """
        name = name.strip()
        ensure_valid_identifier(name)
        self._name = name

    @property
    def name(self):
        """The name of the port, local to the current component"""
        return self._name


class PropertyPort(Port):
    """PropertyPort

    An |PropertyPort| represents a input or output to/from a property of a
    Component. For example, this could be the source cell x-coordinate to be
    passed to a connection rule.
    """

    defining_attributes = ('name', 'dimension')

    __metaclass__ = ABCMeta

    def __init__(self, name, dimension=None):
        super(PropertyPort, self).__init__(name)
        self._dimension = dimension if dimension is not None else dimensionless

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


class IndexPort(Port):
    """IndexPort

    An |IndexPort| is a port that receives indices from the container or
    generates a dendritic tree.
    """
    __metaclass__ = ABCMeta

    defining_attributes = ('name',)

    def __repr__(self):
        classstring = self.__class__.__name__
        return "{}('{}')".format(classstring, self.name)


class PropertySendPort(PropertyPort):
    """PropertySendPort

    An |PropertySendPort| represents an output from a distribution class used
    to derive properties across a container (i.e. |Population|, |Projection| or
    |MultiCompartmental|)

    """
    mode = "send"

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_analogsendport(self, **kwargs)

    def is_incoming(self):
        return False


class PropertyReceivePort(PropertyPort):
    """PropertyReceivePort

    An |PropertyReceivePort| represents port to a property of a Component. For
    example, this could be the source cell x-coordinate to be passed to a
    connection rule.

    """
    mode = "recv"

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_analogreceiveport(self, **kwargs)

    def is_incoming(self):
        return True


class IndexSendPort(IndexPort):
    """IndexSendPort

    An |IndexSendPort| is a port that can be used to generate arrays of indices
    from |DistribtutionClass|es. This can be useful in mapping dendritic trees
    to dynamic domains in |Multicompartmental| models.
    """
    mode = "send"

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_eventsendport(self, **kwargs)

    def is_incoming(self):
        return False


class IndexReceivePort(IndexPort):
    """IndexReceivePort

    An |IndexReceivePort| is a port that receives indices from the container,
    such as the index of a source cell in a Projection to be used in a
    connection rule
    """
    mode = "recv"

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_eventreceiveport(self, **kwargs)

    def is_incoming(self):
        return True
