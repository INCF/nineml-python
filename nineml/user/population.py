from itertools import chain
from . import BaseULObject
from .dynamics import DynamicsProperties
import nineml.user
from nineml.base import DocumentLevelObject, DynamicPortsObject
from nineml.utils import validate_identifier


class Population(BaseULObject, DocumentLevelObject, DynamicPortsObject):
    """
    A collection of spiking neurons all of the same type.

    Parameters
    ----------
    name : str
        a name for the population.
    size : int
        the size of neurons in the population
    cell : DynamicsProperties | Reference->DynamicsProperties
        a :class:`Component`, or :class:`Reference` to a component defining
        the cell type (i.e. the mathematical model and its
        parameterisation).
    """
    nineml_type = "Population"
    nineml_attr = ('name', 'size')
    nineml_child = {'cell': None}

    def __init__(self, name, size, cell):
        self._name = validate_identifier(name)
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self)
        self.size = size
        self._cell = cell

    def __str__(self):
        return ("Population '{}' of size {} with dynamics '{}'"
                .format(self.name, self.size, self.cell.name))

    def __repr__(self):
        return ("Population(name='{}', size={}, cell={})"
                .format(self.name, self.size, self.cell.name))

    def __len__(self):
        return self.size

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = int(size)

    @property
    def cell(self):
        return self._cell

    @property
    def component_class(self):
        return self.cell.component_class

    @property
    def component_classes(self):
        """
        Returns the component class wrapped in an iterator for duck typing
        with Selection objects
        """
        return iter([self.component_class])

    def all_components(self):
        """
        Return a list of all components used by the population.
        """
        components = []
        if self.cell:
            components.append(self.cell)
            components.extend(
                self.cell.get_random_distributions())
            components.extend(
                self.cell.get_random_distributions())
        return components

    @property
    def attributes_with_units(self):
        return chain(*[c.attributes_with_units for c in self.all_components()])

    def serialize_node(self, node, **options):
        node.attr('name', self.name, **options)
        node.attr('Size', self.size, in_body=True, **options)
        node.child(self.cell, within='Cell', **options)

    @classmethod
    def unserialize_node(cls, node, **options):
        cell = node.child(
            (DynamicsProperties, nineml.user.MultiDynamicsProperties),
            within='Cell', allow_ref=True, **options)
        return cls(name=node.attr('name', **options),
                   size=node.attr('Size', in_body=True, dtype=int, **options),
                   cell=cell)

    def analog_receive_port(self, name):
        return self.cell.analog_receive_port(name)

    @property
    def analog_receive_ports(self):
        return self.cell.analog_receive_ports

    @property
    def analog_receive_port_names(self):
        return self.cell.analog_receive_port_names

    @property
    def num_analog_receive_ports(self):
        return self.cell.num_analog_receive_ports

    def analog_send_port(self, name):
        return self.cell.analog_send_port(name)

    @property
    def analog_send_ports(self):
        return self.cell.analog_send_ports

    @property
    def analog_send_port_names(self):
        return self.cell.analog_send_port_names

    @property
    def num_analog_send_ports(self):
        return self.cell.num_analog_send_ports

    def analog_reduce_port(self, name):
        return self.cell.analog_reduce_port(name)

    @property
    def analog_reduce_ports(self):
        return self.cell.analog_reduce_ports

    @property
    def analog_reduce_port_names(self):
        return self.cell.analog_reduce_port_names

    @property
    def num_analog_reduce_ports(self):
        return self.cell.num_analog_reduce_ports

    def event_receive_port(self, name):
        return self.cell.event_receive_port(name)

    @property
    def event_receive_ports(self):
        return self.cell.event_receive_ports

    @property
    def event_receive_port_names(self):
        return self.cell.event_receive_port_names

    @property
    def num_event_receive_ports(self):
        return self.cell.num_event_receive_ports

    def event_send_port(self, name):
        return self.cell.event_send_port(name)

    @property
    def event_send_ports(self):
        return self.cell.event_send_ports

    @property
    def event_send_port_names(self):
        return self.cell.event_send_port_names

    @property
    def num_event_send_ports(self):
        return self.cell.num_event_send_ports
