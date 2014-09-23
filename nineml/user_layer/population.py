import re
from .base import BaseULObject, NINEML, E
from .utility import check_tag
from .dynamics import SpikingNodeType, get_or_create_prototype
from .components import BaseComponent, get_or_create_component, StringValue
import nineml.user_layer.containers


class Population(BaseULObject):

    """
    A collection of network nodes all of the same type. Nodes may either be
    individual spiking nodes (neurons) or groups (motifs, microcircuits,
    columns, etc.)
    """
    element_name = "population"
    defining_attributes = ("name", "number", "prototype", "positions")

    def __init__(self, name, number, prototype, positions=None):
        self.name = name
        self.number = number
        assert isinstance(prototype, (SpikingNodeType,
                                      nineml.user_layer.containers.Group))
        self.prototype = prototype
        if positions is not None:
            assert isinstance(positions, PositionList)
        self.positions = positions

    def __str__(self):
        return ('Population "%s": %dx"%s" %s' %
                (self.name, self.number, self.prototype.name, self.positions))

    def get_components(self):
        components = []
        if self.prototype:
            if isinstance(self.prototype, SpikingNodeType):
                components.append(self.prototype)
                components.extend(self.prototype.parameters.get_random_distributions())
                components.extend(self.prototype.initial_values.get_random_distributions())
            elif isinstance(self.prototype,
                            nineml.user_layer.containers.Group):
                components.extend(self.prototype.get_components())
        if self.positions is not None:
            components.extend(self.positions.get_components())
        return components

    def to_xml(self):
        if self.positions is None:
            return E(self.element_name,
                     E.number(str(self.number)),
                     E.prototype(self.prototype.name),
                     name=self.name)
        else:
            return E(self.element_name,
                     E.number(str(self.number)),
                     E.prototype(self.prototype.name),
                     self.positions.to_xml(),
                     name=self.name)

    @classmethod
    def from_xml(cls, element, components, groups):
        check_tag(element, cls)
        prototype_ref = element.find(NINEML + 'prototype').text
        return cls(name=element.attrib['name'],
                   number=int(element.find(NINEML + 'number').text),
                   prototype=get_or_create_prototype(prototype_ref, components,
                                                     groups),
                   positions=PositionList.from_xml(element.find(NINEML +
                                                                PositionList.\
                                                                 element_name),
                                                   components))


class PositionList(BaseULObject):

    """
    Represents a list of network node positions. May contain either an
    explicit list of positions or a Structure instance that can be used to
    generate positions.
    """
    element_name = "positions"
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
    def from_xml(cls, element, components):
        if element is None:
            return None
        else:
            check_tag(element, cls)
            structure_element = element.find(NINEML + 'structure')
            if structure_element is not None:
                return cls(structure=get_or_create_component(
                                                        structure_element.text,
                                                        Structure, components))
            else:
                positions = [(float(p.attrib['x']), float(p.attrib['y']),
                              float(p.attrib['z']))
                             for p in element.findall(NINEML + 'position')]
                return cls(positions=positions)


class Operator(BaseULObject):
    defining_attributes = ("operands",)
    children = ("operands",)

    def __init__(self, *operands):
        self.operands = operands

    def to_xml(self):
        operand_elements = []
        for c in self.operands:
            if isinstance(c, (basestring, float, int)):
                operand_elements.append(E(StringValue.element_name, str(c)))
            else:
                operand_elements.append(c.to_xml())
        return E(self.element_name,
                 *operand_elements)

    @classmethod
    def from_xml(cls, element):
        if hasattr(cls, "element_name") and element.tag == (NINEML +
                                                            cls.element_name):
            dispatch = {
                NINEML + StringValue.element_name: StringValue.from_xml,
                NINEML + Eq.element_name: Eq.from_xml,
                NINEML + Any.element_name: Any.from_xml,
                NINEML + All.element_name: All.from_xml,
                NINEML + Not.element_name: Not.from_xml,
                NINEML + In.element_name: In.from_xml,
            }
            operands = []
            for child in element.iterchildren():
                operands.append(dispatch[element.tag](child))
            return cls(*operands)
        else:
            return {
                NINEML + Eq.element_name: Eq,
                NINEML + Any.element_name: Any,
                NINEML + All.element_name: All,
                NINEML + Not.element_name: Not,
                NINEML + StringValue.element_name: StringValue,
                NINEML + In.element_name: In,
            }[element.tag].from_xml(element)


def qstr(obj):
    if isinstance(obj, basestring):
        return '"%s"' % obj
    else:
        return obj.__str__()


class SelectionOperator(Operator):
    pass


class Any(SelectionOperator):
    element_name = "any"

    def __str__(self):
        return "(" + ") or (".join(qstr(op) for op in self.operands) + ")"


class All(SelectionOperator):
    element_name = "all"

    def __str__(self):
        return "(" + ") and (".join(qstr(op) for op in self.operands) + ")"


class Not(SelectionOperator):
    element_name = "not"

    def __init__(self, *operands):
        assert len(operands) == 1
        SelectionOperator.__init__(self, *operands)


class Comparison(Operator):

    def __init__(self, value1, value2):
        Operator.__init__(self, value1, value2)


class Eq(Comparison):
    element_name = "equal"

    def __str__(self):
        return "(%s) == (%s)" % tuple(qstr(op) for op in self.operands)


class In(Comparison):
    element_name = "in"

    def __init__(self, item, sequence):
        Operator.__init__(self, item, sequence)

    def __str__(self):
        return "%s in %s" % tuple(qstr(op) for op in self.operands)


class Selection(BaseULObject):

    """
    A set of network nodes selected from existing populations within the Group.
    """
    element_name = "set"
    defining_attributes = ("name", "condition")

    def __init__(self, name, condition):
        """
        condition - instance of an Operator subclass
        """
        assert isinstance(condition, Operator)
        self.name = name
        self.condition = condition
        self.populations = []
        self.evaluated = False

    def to_xml(self):
        return E(self.element_name,
                 E.select(self.condition.to_xml()),
                 name=self.name)

    @classmethod
    def from_xml(cls, element, components):
        check_tag(element, cls)
        select_element = element.find(NINEML + 'select')
        assert len(select_element) == 1
        return cls(element.attrib["name"],
                   Operator.from_xml(select_element.getchildren()[0]))

    def evaluate(self, group):
        if not self.evaluated:
            selection = str(self.condition)
            # look away now, this isn't pretty
            subnet_pattern = re.compile(r'\(\("population\[@name\]"\) == '
                                        r'\("(?P<name>[\w ]+)"\)\) and '
                                        r'\("population\[@id\]" in '
                                        r'"(?P<slice>\d*:\d*:\d*)"\)')
            assembly_pattern = re.compile(r'\(\("population\[@name\]"\) == '
                                          r'\("(?P<name1>[\w ]+)"\)\) or '
                                          r'\(\("population\[@name\]"\) == '
                                          r'\("(?P<name2>[\w ]+)"\)\)')
            # this should be replaced by the use of ply, or similar
            match = subnet_pattern.match(selection)
            if match:
                name = match.groupdict()["name"]
                slice = match.groupdict()["slice"]
                self.populations.append((group.populations[name], slice))
            else:
                match = assembly_pattern.match(selection)
                if match:
                    name1 = match.groupdict()["name1"]
                    name2 = match.groupdict()["name2"]
                    self.populations.append((group.populations[name1], None))
                    self.populations.append((group.populations[name2], None))
                else:
                    raise Exception("Can't evaluate selection")
            self.evaluated = True


class Structure(BaseComponent):

    """
    Component representing the structure of a network, e.g. 2D grid, random
    distribution within a sphere, etc.
    """
    abstraction_layer_module = 'structure'

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
            return self.get_definition()  # e.g. lambda size: csa.random2d(size, *self.parameters) @IgnorePep8
        else:
            raise Exception("Structure cannot be transformed to CSA geometry "
                            "function")


# this approach is crying out for a class factory
