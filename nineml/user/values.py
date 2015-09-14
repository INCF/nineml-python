# encoding: utf-8
from . import BaseULObject
from nineml.xmlns import E, NINEML
from nineml.annotations import read_annotations, annotate_xml
#from .component import Component
from urllib import urlopen
import contextlib
import numpy
from nineml.exceptions import NineMLRuntimeError
from nineml.exceptions import handle_xml_exceptions


class BaseValue(BaseULObject):
    pass


class SingleValue(BaseValue):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component that generates
    numbers, e.g. a RandomDistributionComponent instance.
    """
    element_name = "SingleValue"
    defining_attributes = ("value",)

    def __init__(self, value):
        super(SingleValue, self).__init__()
        self.value = value

    def __repr__(self):
        return "SingleValue(value={})".format(self.value)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name, str(self.value))

    @classmethod
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, _):
        cls.check_tag(element)
        return cls(float(element.text))


class ArrayValue(BaseValue):

    element_name = "ArrayValue"
    defining_attributes = ("_values",)

    def __init__(self, values):
        super(ArrayValue, self).__init__()
        self._values = values

    @property
    def values(self):
        return self._values

    def __repr__(self):
        return "ArrayValue(with {} values)".format(len(self._values))

    def __hash__(self):
        return hash(self.value)

    def __iter__(self):
        return iter(self._values)

    def __getitem__(self, index):
        return self._values[index]

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name,
                 *[ArrayValueRow(i, v).to_xml(document, **kwargs)
                   for i, v in enumerate(self._values)])

    @classmethod
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        rows = [ArrayValueRow.from_xml(r, document)
                for r in element.findall(NINEML + ArrayValueRow.element_name)]
        if set(r.index for r in rows) != set(xrange(len(rows))):
            raise Exception("Missing or duplicate indices in ArrayValue rows "
                            "({})".format(', '.join(r.index for r in rows)))
        values_str = [row.value for row in sorted(rows, key=lambda r: r.index)]
        try:
            values = [int(v) for v in values_str]
        except ValueError:
            try:
                values = [float(v) for v in values_str]
            except ValueError:
                raise NineMLRuntimeError(
                    "Could not converted loaded values to numerical values "
                    "({})".format(', '.join(values_str)))
        return cls(values)


class ArrayValueRow(BaseValue):

    element_name = "ArrayValueRow"
    defining_attributes = ("index", "value")

    def __init__(self, index, value):
        super(ArrayValueRow, self).__init__()
        self.index = index
        self.value = value

    def __repr__(self):
        return "ArrayValueRow({}, {})".format(self.index, self.value)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                len(self.rows) == len(other.rows) and
                all(r1 == r2 for r1, r2 in zip(self.rows, other.rows)))

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        return E(self.element_name, str(self.value), index=str(self.index))

    @classmethod
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, _):
        return cls(index=int(element.attrib["index"]), value=element.text)


class ExternalArrayValue(BaseValue):

    element_name = "ExternalArrayValue"
    defining_attributes = ("url", "mimetype", "columnName")

    def __init__(self, data, url=None, mimetype=None, columnName=None):
        super(ExternalArrayValue, self).__init__()
        self.data = data
        self.url = url
        self.mimetype = mimetype
        self.columnName = columnName

    def __repr__(self):
        return "ExternalArrayValue(with {} rows)".format(len(self.rows))

    @annotate_xml
    def to_xml(self, document, **kwargs):  # @UnusedVariable
        try:
            numpy.savetxt(self.url, self.data)
        except Exception:
            raise NineMLRuntimeError(
                "Could not write external array to file '{}'"
                .format(self.url))
        return E(self.element_name, url=self.url, mimetype=self.mimetype,
                 columnName=self.columnName)

    @classmethod
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element, _):
        url = element.attrib["url"]
        with contextlib.closing(urlopen(url)) as f:
            data = numpy.loadtxt(f)
        return cls(data, url=element.attrib["url"],
                   mimetype=element.attrib["mimetype"],
                   columnName=element.attrib["columnName"])


#class ComponentValue(BaseValue):
#
#    element_name = "ComponentValue"
#    defining_attributes = ("port", "component")
#
#    def __init__(self, component, port):
#        self.port = port
#        self.component = component
#
#    def __repr__(self):
#        return ("ComponentValue({} port of {} component)"
#                .format(self.port, self.component.name))
#
#    def __eq__(self, other):
#        return (self.port == other.port and
#                self.component == other.component)
#
#    @annotate_xml
#    def to_xml(self, document, **kwargs):  # @UnusedVariable
#        return E(self.element_name, self.component.to_xml(document, **kwargs), port=self.url)
#
#     @classmethod
#     @read_annotations
#     def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
#         comp_element = element.find(NINEML + 'DynamicsProperties')
#         if comp_element is None:
#             comp_element = element.find(NINEML + 'Reference')
#             if comp_element is None:
#                 raise Exception("Did not find component in ComponentValue")
#         component = Component.from_xml(comp_element, document)
#         return cls(component, port=element.attrib["port"])


class StringValue(BaseValue):

    """
    Not intended to be instantiated: just provides the from_xml() classmethod.
    """
    element_name = "Value"

    @classmethod
    @read_annotations
    @handle_xml_exceptions
    def from_xml(cls, element):
        """
        Parse an XML ElementTree structure and return a string value.

        `element` - should be an ElementTree Element instance.
        """
        return element.text
