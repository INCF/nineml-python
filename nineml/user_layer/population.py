import re
from .base import BaseULObject, NINEML, E
from .utility import check_tag
from .components import BaseComponent, StringValue
from ..utility import expect_single
from nineml.base import annotate_xml, read_annotations


class Population(BaseULObject):

    """
    A collection of network nodes all of the same type. Nodes may either be
    individual spiking nodes (neurons) or groups (motifs, microcircuits,
    columns, etc.)
    """
    element_name = "Population"
    defining_attributes = ("name", "number", "cell", "positions")

    def __init__(self, name, number, cell, positions=None):
        self.name = name
        self.number = number
        self.cell = cell
        if positions is not None:
            assert isinstance(positions, PositionList)
        self.positions = positions

    def __str__(self):
        return ('Population "%s": %dx"%s" %s' %
                (self.name, self.number, self.cell.name, self.positions))

    def __repr__(self):
        return ("Population(name='{}', number={}, cell={}{})"
                .format(self.name, self.number, self.cell.name,
                        'positions={}'.format(self.positions)
                        if self.positions else ''))

    def get_components(self):
        components = []
        if self.cell:
            components.append(self.cell)
            components.extend(self.cell.properties.get_random_distributions())
            components.extend(self.cell.initial_values.\
                                                    get_random_distributions())
        if self.positions is not None:
            components.extend(self.positions.get_components())
        return components

    @annotate_xml
    def to_xml(self):
        positions = [self.positions.to_xml()] if self.positions else []
        return E(self.element_name,
                 E.Number(str(self.number)),
                 E.Cell(self.cell.to_xml()),
                 *positions,
                 name=self.name)

    @classmethod
    @read_annotations
    def from_xml(cls, element, context):
        check_tag(element, cls)
        layout_elem = element.find(NINEML + 'Layout')
        kwargs = {}
        if layout_elem:
            kwargs['positions'] = context.resolve_ref(layout_elem,
                                                      BaseComponent)
        return cls(name=element.attrib['name'],
                   number=int(expect_single(
                                    element.findall(NINEML + 'Number')).text),
                   cell=context.resolve_ref(
                               expect_single(element.findall(NINEML + 'Cell')),
                               BaseComponent),
                   **kwargs)


class PositionList(BaseULObject):

    """
    Represents a list of network node positions. May contain either an
    explicit list of positions or a Structure instance that can be used to
    generate positions.
    """
    element_name = "Layout"
    defining_attributes = []

    def __init__(self, positions=[], structure=None):
        """
        Create a new PositionList.

        Either `positions` or `structure` should be provided. Providing both
        will raise an Exception.

        `positions` should be a list of (x,y,z) tuples or a 3xN (Nx3?) numpy
                    array.
        `structure` should be a Structure component.
        """
        if positions and structure:
            raise Exception("Please provide either positions or structure, "
                            "not both.")
        assert not isinstance(positions, Structure)
        self._positions = positions
        if isinstance(structure, Structure):
            self.structure = structure
        elif structure is None:
            self.structure = None
        else:
            raise Exception("structure is", structure)

    def __eq__(self, other):
        if self._positions:
            return self._positions == other._positions
        else:
            return self.structure == other.structure

    def __str__(self):
        if self.structure:
            return "positioned according to '%s'" % self.structure.name
        else:
            return "with explicit position list"

    def get_positions(self, population):
        """
        Return a list or 1D numpy array of (x,y,z) positions.
        """
        if self._positions:
            assert len(self._positions) == population.number
            return self._positions
        elif self.structure:
            return self.structure.generate_positions(population.number)
        else:
            raise Exception("Neither positions nor structure is set.")

    def get_components(self):
        if self.structure:
            return [self.structure]
        else:
            return []

    @annotate_xml
    def to_xml(self):
        element = E(self.element_name)
        if self._positions:
            for pos in self._positions:
                x, y, z = pos
                element.append(E.position(x=str(x), y=str(y), z=str(z),
                                          unit="um"))
        elif self.structure:
            element.append(E.structure(self.structure.name))
        else:
            raise Exception("Neither positions nor structure is set.")
        return element

    @classmethod
    @read_annotations
    def from_xml(cls, element, context):
        if element is None:
            return None
        else:
            check_tag(element, cls)
            structure_element = element.find(NINEML + 'structure')
            if structure_element is not None:
                return cls(structure=context.resolve_ref(structure_element,
                                                         Structure))
            else:
                positions = [(float(p.attrib['x']), float(p.attrib['y']),
                              float(p.attrib['z']))
                             for p in element.findall(NINEML + 'position')]
                return cls(positions=positions)


def qstr(obj):
    if isinstance(obj, basestring):
        return '"%s"' % obj
    else:
        return obj.__str__()


class Structure(BaseComponent):

    """
    Component representing the structure of a network, e.g. 2D grid, random
    distribution within a sphere, etc.
    """
    abstraction_layer_module = 'Structure'

    def generate_positions(self, number):
        """
        Generate a number of node positions according to the network structure.
        """
        raise NotImplementedError

    @property
    def is_csa(self):
        return self.get_definition().__module__ == 'csa.geometry'  # probably need a better test @IgnorePep8

    def to_csa(self):
        if self.is_csa:
            return self.get_definition()  # e.g. lambda size: csa.random2d(size, *self.properties) @IgnorePep8
        else:
            raise Exception("Structure cannot be transformed to CSA geometry "
                            "function")
