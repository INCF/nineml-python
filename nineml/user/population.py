from itertools import chain
from . import BaseULObject
from .component import resolve_reference, write_reference
from .dynamics import DynamicsProperties
from nineml.base import DocumentLevelObject, DynamicPortsObject
from nineml.xml import (
    E, unprocessed_xml, from_child_xml, get_xml_attr)
from nineml.annotations import annotate_xml, read_annotations
from nineml.utils import ensure_valid_identifier


class Population(BaseULObject, DocumentLevelObject, DynamicPortsObject):
    """
    A collection of spiking neurons all of the same type.

    **Arguments**:
        *name*
            a name for the population.
        *size*
            an integer, the size of neurons in the population
        *cell*
            a :class:`Component`, or :class:`Reference` to a component defining
            the cell type (i.e. the mathematical model and its
            parameterisation).
    """
    nineml_type = "Population"
    defining_attributes = ('_name', '_size', '_cell')

    def __init__(self, name, size, cell, document=None):
        ensure_valid_identifier(name)
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
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

    def get_components(self):
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
        return chain(*[c.attributes_with_units for c in self.get_components()])

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):
        return E(self.nineml_type,
                 E.Size(str(self.size)),
                 E.Cell(self.cell.to_xml(document, E=E, **kwargs)),
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):
        cell = from_child_xml(element, DynamicsProperties, document,
                              allow_reference=True, within='Cell', **kwargs)
        return cls(name=get_xml_attr(element, 'name', document, **kwargs),
                   size=get_xml_attr(element, 'Size', document, in_block=True,
                                     dtype=int, **kwargs),
                   cell=cell, document=document)

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
