from collections import OrderedDict
from . import BaseULObject
from nineml.base import (
    DocumentLevelObject, ContainerObject, DynamicPortsObject)
from .population import Population
from nineml.exceptions import NineMLNameError, NineMLUsageError
from nineml.utils import validate_identifier
from .component_array import ComponentArray
from nineml.exceptions import name_error
from itertools import chain
from collections import defaultdict


def combined_port_accessor(population_accessor):
    def accessor(self, name):
        try:
            ports = [population_accessor(p, name) for p in self.populations]
        except NineMLNameError:
            raise NineMLNameError(
                "'{}' {} is not present in all populations '{}' of the "
                "selection"
                .format(name, population_accessor.__name__,
                        "', '".join(p.name for p in self.populations)))
        port = ports[0]
        if any(p != port for p in ports):
            raise NineMLNameError(
                "{} '{}' in populations '{}' are not equivalent"
                .format(population_accessor.__name__.capitalize(),
                        name, "', '".join(p.name for p in self.populations)))
        return port
    return accessor


def combined_ports_property(population_property):
    def combined_property(self):
        port_groups = defaultdict(list)
        for port in chain(*(population_property.__get__(p)
                            for p in self.populations)):
            port_groups[port.name].append(port)
        # Return ports that appear in all populations in the selection and have
        # the same dimension
        return (grp[0] for grp in port_groups.values()
                if (len(grp) == self.num_populations and
                    all(p == grp[0] for p in grp)))
    return property(combined_property)


class Item(BaseULObject):

    nineml_type = 'Item'
    nineml_attr = ('index',)
    nineml_child = {'population': None}

    def __init__(self, index, population):
        BaseULObject.__init__(self)
        self._index = int(index)
        self._population = population

    @property
    def index(self):
        return self._index

    @property
    def key(self):
        return str(self.index)

    @property
    def population(self):
        """
        Returns the population/selection/component-array referenced in the
        Item
        """
        return self._population

    def serialize_node(self, node, **options):
        node.attr('index', self.index, **options)
        node.child(self.population, reference=True, **options)

    @classmethod
    def unserialize_node(cls, node, **options):
        return cls(node.attr('index', dtype=int, **options),
                   node.child((Population, Selection, ComponentArray),
                              allow_ref='only', **options))


class Concatenate(BaseULObject, ContainerObject):
    """
    Concatenates multiple :class:`Population`\s or :class:`Selection`\s
    together into a larger :class:`Selection`.
    """

    nineml_type = 'Concatenate'
    nineml_children = (Item,)

    def __init__(self, items, **kwargs):
        BaseULObject.__init__(self, **kwargs)
        ContainerObject.__init__(self, **kwargs)
        items = list(items)
        if all(isinstance(it, Item) for it in items):
            indices = [it.index for it in items]
            if min(indices) < 0 or max(indices) > len(indices):
                raise NineMLUsageError(
                    "Indices are not contiguous, have duplicates, or don't "
                    "start from 0 ({})"
                    .format(', '.join(str(i) for i in indices)))
            self.add(*items)
        elif any(isinstance(it, Item) for it in items):
            raise NineMLUsageError(
                "Cannot mix Items and Populations/Selections in Concatenate "
                "__init__ method ({})".format(', '.join(str(it)
                                                        for it in items)))
        else:
            self.add(*(Item(i, p) for i, p in enumerate(items)))
        assert(self.num_items)

    def __repr__(self):
        return "Concatenate({})".format(
            ", ".join(repr(item) for item in self.items))

    @property
    def key(self):
        return '_'.join(p.name for p in self.populations)

    @name_error
    def item(self, index):
        return self._items[index]

    @property
    def item_keys(self):
        """Return a list of the items in the concatenation."""
        return iter(self._items.keys())

    @property
    def items(self):
        """Return a list of the items in the concatenation."""
        return iter(self._items.values())

    @property
    def populations(self):
        """
        Returns and iterator over the populations (or selections or component
        arrays) in the concatenate statement
        """
        return (it.population for it in self.items)

    @property
    def population_names(self):
        return (p.name for p in self.populations)

    @property
    def num_populations(self):
        return len(self._items)

    @name_error
    def population(self, name):
        try:
            return (p for p in self.populations if p.name == name)
        except StopIteration:
            raise KeyError(name)

    @property
    def num_items(self):
        """Return a list of the items in the concatenation."""
        return len(self._items)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.children(self.items, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(node.children(Item, **options))


class Selection(BaseULObject, DocumentLevelObject, DynamicPortsObject):
    """
    Container for combining multiple populations or subsets thereof.

    **Arguments**:
        *name*
            a name for the selection
        *operation*
            a "selector" object which determines which neurons form part of the
            selection. Only :class:`Concatenate` is currently supported.
    """
    nineml_type = "Selection"
    nineml_attr = ('name',)
    nineml_child = {'operation': Concatenate}

    def __init__(self, name, operation, **kwargs):
        self._name = validate_identifier(name)
        BaseULObject.__init__(self, **kwargs)
        DocumentLevelObject.__init__(self)
        self._operation = operation

    def __repr__(self):
        return "Selection(name='{}', {})".format(self.name, self.operation)

    @property
    def name(self):
        return self._name

    @property
    def operation(self):
        return self._operation

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.child(self.operation, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        # The only supported op at this stage
        op = node.child(Concatenate, **options)
        return cls(node.attr('name', **options), op)

    def evaluate(self):
        assert isinstance(self.operation, Concatenate), \
            "Only concatenation is currently supported"
        return self.operation.items

    @property
    def populations(self):
        return self.operation.populations

    @property
    def population_names(self):
        return self.operation.population_names

    @property
    def num_populations(self):
        return self.operation.num_populations

    def population(self, name):
        return self.operation.population(name)

    @property
    def component_classes(self):
        return (p.component_class for p in self.populations)

    @property
    def size(self):
        return sum(p.size for p in self.populations)

    port = combined_port_accessor(Population.port)
    ports = combined_ports_property(Population.ports)
    send_port = combined_port_accessor(Population.send_port)
    send_ports = combined_ports_property(Population.send_ports)
    receive_port = combined_port_accessor(Population.receive_port)
    receive_ports = combined_ports_property(Population.receive_ports)
    event_receive_port = combined_port_accessor(
        Population.event_receive_port)
    event_receive_ports = combined_ports_property(
        Population.event_receive_ports)
    event_send_port = combined_port_accessor(
        Population.event_send_port)
    event_send_ports = combined_ports_property(
        Population.event_send_ports)
    analog_receive_port = combined_port_accessor(
        Population.analog_receive_port)
    analog_receive_ports = combined_ports_property(
        Population.analog_receive_ports)
    analog_send_port = combined_port_accessor(
        Population.analog_send_port)
    analog_send_ports = combined_ports_property(
        Population.analog_send_ports)
    analog_reduce_port = combined_port_accessor(
        Population.analog_reduce_port)
    analog_reduce_ports = combined_ports_property(
        Population.analog_reduce_ports)

    @property
    def analog_send_port_names(self):
        return (p.name for p in self.analog_send_ports)

    @property
    def num_analog_send_ports(self):
        return len(list(self.analog_send_ports))

    @property
    def analog_receive_port_names(self):
        return (p.name for p in self.analog_receive_ports)

    @property
    def num_analog_receive_ports(self):
        return len(list(self.analog_receive_ports))

    @property
    def analog_reduce_port_names(self):
        return (p.name for p in self.analog_reduce_ports)

    @property
    def num_analog_reduce_ports(self):
        return len(list(self.analog_reduce_ports))

    @property
    def event_send_port_names(self):
        return (p.name for p in self.event_send_ports)

    @property
    def num_event_send_ports(self):
        return len(list(self.event_send_ports))

    @property
    def event_receive_port_names(self):
        return (p.name for p in self.event_receive_ports)

    @property
    def num_event_receive_ports(self):
        return len(list(self.event_receive_ports))

# TGC 11/11/ This old implementation of Set (now called Selection) was copied
#            from nineml.user.populations.py probably some of it is worth
#            salvaging as we look to implement some of this functionality for
#            version 2.0
#
# class Set(BaseULObject):
#     """
#     A set of network nodes selected from existing populations within the
#     Network.
#     """
#     nineml_type = "Selection"
#     nineml_attr = ("name",)
#     nineml_child = {"condition": None}
#
#     def __init__(self, name, condition):
#         """
#         condition - instance of an Operator subclass
#         """
#         super(Property, self).__init__()
#         assert isinstance(condition, Operator)
#         self.name = name
#         self.condition = condition
#         self.populations = []
#         self.evaluated = False
#
#     def evaluate(self, group):
#         if not self.evaluated:
#             selection = str(self.condition)
#             # look away now, this isn't pretty
#             subnet_pattern = re.compile(r'\(\("population\[@name\]"\) == '
#                                         r'\("(?P<name>[\w ]+)"\)\) and '
#                                         r'\("population\[@id\]" in '
#                                         r'"(?P<slice>\d*:\d*:\d*)"\)')
#             assembly_pattern = re.compile(r'\(\("population\[@name\]"\) == '
#                                           r'\("(?P<name1>[\w ]+)"\)\) or '
#                                           r'\(\("population\[@name\]"\) == '
#                                           r'\("(?P<name2>[\w ]+)"\)\)')
#             # this should be replaced by the use of ply, or similar
#             match = subnet_pattern.match(selection)
#             if match:
#                 name = match.groupdict()["name"]
#                 slice = match.groupdict()["slice"]
#                 self.populations.append((group.populations[name], slice))
#             else:
#                 match = assembly_pattern.match(selection)
#                 if match:
#                     name1 = match.groupdict()["name1"]
#                     name2 = match.groupdict()["name2"]
#                     self.populations.append((group.populations[name1], None))
#                     self.populations.append((group.populations[name2], None))
#                 else:
#                     raise Exception("Can't evaluate selection")
#             self.evaluated = True
#
#
# class SelectionOperator(Operator):
#     pass
#
#
# class Any(SelectionOperator):
#     nineml_type = "Any"
#
#     def __str__(self):
#         return "(" + ") or (".join(qstr(op) for op in self.operands) + ")"
#
#
# class All(SelectionOperator):
#     nineml_type = "All"
#
#     def __str__(self):
#         return "(" + ") and (".join(qstr(op) for op in self.operands) + ")"
#
#
# class Not(SelectionOperator):
#     nineml_type = "Not"
#
#     def __init__(self, *operands):
#         assert len(operands) == 1
#         SelectionOperator.__init__(self, *operands)
#
#
# class Comparison(Operator):
#
#     def __init__(self, value1, value2):
#         Operator.__init__(self, value1, value2)
#
#
# class Eq(Comparison):
#     nineml_type = "Equal"
#
#     def __str__(self):
#         return "(%s) == (%s)" % tuple(qstr(op) for op in self.operands)
#
#
# class In(Comparison):
#     nineml_type = "In"
#
#     def __init__(self, item, sequence):
#         Operator.__init__(self, item, sequence)
#
#     def __str__(self):
#         return "%s in %s" % tuple(qstr(op) for op in self.operands)
#
# class Operator(BaseULObject):
#     super(Property, self).__init__()
#     nineml_children = (Operand,)
#
#     def __init__(self, *operands):
#         self.operands = operands

