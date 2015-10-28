from itertools import chain
from . import BaseULObject
from .component import (
    resolve_reference, write_reference, DynamicsProperties)
from nineml.base import DocumentLevelObject
from nineml.xml import (
    E, unprocessed_xml, from_child_xml, get_xml_attr, extract_xmlns, NINEMLv1)
from nineml.annotations import annotate_xml, read_annotations


class Population(BaseULObject, DocumentLevelObject):
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
    element_name = "Population"
    defining_attributes = ("name", "size", "cell")

    def __init__(self, name, size, cell, url=None):
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, url)
        self.name = name
        self.size = size
        self.cell = cell

    def __str__(self):
        return ("Population '{}' of size {} with dynamics '{}'"
                .format(self.name, self.size, self.cell.name))

    def __repr__(self):
        return ("Population(name='{}', size={}, cell={})"
                .format(self.name, self.size, self.cell.name))

    @property
    def component_class(self):
        return self.cell.component_class

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
        return E(self.element_name,
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
                   cell=cell, url=document.url)

    def port(self, name):
        return self.cell.port(name)

    @property
    def ports(self):
        return self.cell.ports

    @property
    def port_names(self):
        return self.cell.port_names

    @property
    def num_ports(self):
        return self.cell.num_ports

    def receive_port(self, name):
        return self.cell.receive_port(name)

    @property
    def receive_ports(self):
        return self.cell.receive_ports

    @property
    def receive_port_names(self):
        return self.cell.receive_port_names

    @property
    def num_receive_ports(self):
        return self.cell.num_receive_ports

    def send_port(self, name):
        return self.cell.send_port(name)

    @property
    def send_ports(self):
        return self.cell.send_ports

    @property
    def send_port_names(self):
        return self.cell.send_port_names

    @property
    def num_send_ports(self):
        return self.cell.num_send_ports

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


def qstr(obj):
    if isinstance(obj, basestring):
        return '"%s"' % obj
    else:
        return obj.__str__()
