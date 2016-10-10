from operator import itemgetter, and_
from . import BaseULObject
from nineml.reference import resolve_reference, write_reference, Reference
from nineml.annotations import annotate_xml, read_annotations
from nineml.xml import (
    extract_xmlns, E, from_child_xml, unprocessed_xml, get_xml_attr, NINEMLv1)
from nineml.base import DocumentLevelObject, DynamicPortsObject
from .population import Population
from nineml.exceptions import NineMLNameError
from nineml.utils import ensure_valid_identifier


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
        combined = reduce(and_, (set(population_property.__get__(p))
                                 for p in self.populations))
        return iter(combined)
    return property(combined_property)


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
    defining_attributes = ('name', 'operation')

    def __init__(self, name, operation, document=None):
        ensure_valid_identifier(name)
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self, document)
        self._operation = operation

    def __repr__(self):
        return "Selection(name='{}', {})".format(self.name, self.operation)

    @property
    def name(self):
        return self._name

    @property
    def operation(self):
        return self._operation

    @write_reference
    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        return E(self.nineml_type,
                 self.operation.to_xml(document, E=E, **kwargs),
                 name=self.name)

    @classmethod
    @resolve_reference
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        # The only supported op at this stage
        op = from_child_xml(
            element, Concatenate, document, **kwargs)
        return cls(get_xml_attr(element, 'name', document, **kwargs), op,
                   document=document)

    def evaluate(self):
        assert isinstance(self.operation, Concatenate), \
            "Only concatenation is currently supported"
        return self.operation.items

    @property
    def populations(self):
        return self.operation.items

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
        return len(list(self.analog_reduce_ports))

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
        return len(list(self.event_receive_ports))

    @property
    def event_receive_port_names(self):
        return (p.name for p in self.event_receive_ports)

    @property
    def num_event_receive_ports(self):
        return len(list(self.event_receive_ports))


class Concatenate(BaseULObject):
    """
    Concatenates multiple :class:`Population`\s or :class:`Selection`\s
    together into a larger :class:`Selection`.
    """

    nineml_type = 'Concatenate'
    defining_attributes = ('items',)

    def __init__(self, *items):
        super(Concatenate, self).__init__()
        self._items = list(items)

    def __repr__(self):
        return "Concatenate(%s)" % ", ".join(repr(item) for item in self.items)

    @property
    def _name(self):
        return '_'.join(i._name for i in self._items[:10])

    @property
    def items(self):
        """Return a list of the items in the concatenation."""
        # should this perhaps flatten to a list of Populations, where the
        # concatenation includes other Selections? or should that be a separate
        # method?
        return iter(self._items)

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        def item_to_xml(item):
            if isinstance(item, Reference):
                return item.to_xml(document, E=E, **kwargs)
            elif E._namespace == NINEMLv1:
                return E.Reference(item.name)
            else:
                return E.Reference(name=item.name)
        return E(self.nineml_type,
                 *[E.Item(item_to_xml(item), index=str(i))
                   for i, item in enumerate(self.items)])

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        items = []
        # Load references and indices from xml
        for it_elem in element.findall(extract_xmlns(element.tag) + 'Item'):
            items.append((
                get_xml_attr(it_elem, 'index', document, dtype=int, **kwargs),
                from_child_xml(it_elem, Population, document,
                               allow_reference='only', **kwargs)))
            try:
                kwargs['unprocessed'][0].discard(it_elem)
            except KeyError:
                pass
        # Sort by 'index' attribute
        indices, items = zip(*sorted(items, key=itemgetter(0)))
        indices = [int(i) for i in indices]
        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate indices found in Concatenate list ({})"
                             .format(indices))
        if indices[0] != 0:
            raise ValueError("Indices of Concatenate items must start from 0 "
                             "({})".format(indices))
        if indices[-1] != len(indices) - 1:
            raise ValueError("Missing indices in Concatenate items ({}), list "
                             "must be contiguous.".format(indices))
        return cls(*items)  # Strip off indices used to sort elements


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
#     defining_attributes = ("name", "condition")
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
#     def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
#         return E(self.nineml_type,
#                  E.select(self.condition.to_xml(document, E=E, **kwargs)),
#                  name=self.name)
#
#     @classmethod
#     def from_xml(cls, element, components):
#         select_element = element.find(NINEML + 'select')
#         assert len(select_element) == 1
#         return cls(get_xml_attr(element, 'name', document, **kwargs),
#                    Operator.from_xml(select_element.getchildren()[0]))
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
#     defining_attributes = ("operands",)
#     children = ("operands",)
#
#     def __init__(self, *operands):
#         self.operands = operands
#
#     def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
#         operand_elements = []
#         for c in self.operands:
#             if isinstance(c, (basestring, float, int)):
#                 operand_elements.append(E(StringValue.nineml_type, str(c)))
#             else:
#                 operand_elements.append(c.to_xml(document, E=E, **kwargs))
#         return E(self.nineml_type,
#                  *operand_elements)
#
#     @classmethod
#     def from_xml(cls, element):
#         if hasattr(cls, "nineml_type") and element.tag == (NINEML +
#                                                            cls.nineml_type):
#             dispatch = {
#                 NINEML + StringValue.nineml_type: StringValue.from_xml,
#                 NINEML + Eq.nineml_type: Eq.from_xml,
#                 NINEML + Any.nineml_type: Any.from_xml,
#                 NINEML + All.nineml_type: All.from_xml,
#                 NINEML + Not.nineml_type: Not.from_xml,
#                 NINEML + In.nineml_type: In.from_xml,
#             }
#             operands = []
#             for child in element.iterchildren():
#                 operands.append(dispatch[element.tag](child))
#             return cls(*operands)
#         else:
#             return {
#                 NINEML + Eq.nineml_type: Eq,
#                 NINEML + Any.nineml_type: Any,
#                 NINEML + All.nineml_type: All,
#                 NINEML + Not.nineml_type: Not,
#                 NINEML + StringValue.nineml_type: StringValue,
#                 NINEML + In.nineml_type: In,
#             }[element.tag].from_xml(element)
