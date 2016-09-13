from __future__ import division
from .base import BaseNineMLObject
from nineml.xml import E, extract_xmlns, get_xml_attr
from abc import ABCMeta, abstractmethod
from nineml.annotations import read_annotations, annotate_xml
from urllib import urlopen
import contextlib
import collections
import sympy
import itertools
from itertools import izip
from operator import itemgetter
import numpy
import nineml
from nineml.exceptions import NineMLRuntimeError
from nineml.utils import nearly_equal
from nineml.xml import from_child_xml, unprocessed_xml


class BaseValue(BaseNineMLObject):

    __metaclass__ = ABCMeta

    @abstractmethod
    def to_xml(self, document, E=E, **kwargs):
        pass

    @classmethod
    @read_annotations
    def from_parent_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return from_child_xml(
            element, (SingleValue, ArrayValue, RandomValue),
            document, allow_reference=True, **kwargs)


class SingleValue(BaseValue):
    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component that generates
    numbers, e.g. a RandomDistribution instance.
    """
    nineml_type = "SingleValue"
    defining_attributes = ("value",)

    def __init__(self, value):
        super(SingleValue, self).__init__()
        self._value = float(value)

    @property
    def value(self):
        return self._value

    def __iter__(self):
        """Infinitely iterate the same value"""
        return itertools.repeat(self._value)

    def __eq__(self, other):
        try:
            if self.nineml_type != other.nineml_type:
                return False
        except AttributeError:
            return False
        return nearly_equal(self._value, other._value)

    def __neq__(self, other):
        return not self == other

    def __len__(self):
        return 0

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return "SingleValue(value={})".format(self.value)

    def __hash__(self):
        return hash(self.value)

    def inverse(self):
        return SingleValue(1.0 / self._value)

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        return E(self.nineml_type, str(self.value))

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        return cls(float(element.text))

    # =========================================================================
    # Magic methods to allow the SingleValue to be treated like a
    # floating point number
    # =========================================================================

    def _sympy_(self):
        return self._value

    def __float__(self):
        return self._value

    def __int__(self):
        return int(self._value)

    def __add__(self, num):
        return SingleValue(self._value + float(num))

    def __sub__(self, num):
        return SingleValue(self._value - float(num))

    def __mul__(self, num):
        return SingleValue(self._value * float(num))

    def __truediv__(self, num):
        return SingleValue(self._value / float(num))

    def __div__(self, num):
        return SingleValue(self.__truediv__(num))

    def __pow__(self, power):
        return SingleValue(self._value ** power)

    def __floordiv__(self, num):
        return SingleValue(self._value // float(num))

    def __mod__(self, num):
        return SingleValue(self._value % float(num))

    def __radd__(self, num):
        return SingleValue(self.__add__(num))

    def __rsub__(self, num):
        return SingleValue(float(num) - self._value)

    def __rmul__(self, num):
        return SingleValue(self.__mul__(num))

    def __rtruediv__(self, num):
        return SingleValue(num.__truediv__(self._value))

    def __rdiv__(self, num):
        return SingleValue(self.__rtruediv__(num))

    def __rpow__(self, num):
        return SingleValue(float(num) ** self._value)

    def __rfloordiv__(self, num):
        return SingleValue(float(num) // self._value)

    def __rmod__(self, num):
        return SingleValue(float(num) % self._value)

    def __neg__(self):
        return SingleValue(-self._value)

    def __abs__(self):
        return SingleValue(abs(self._value))


class ArrayValue(BaseValue):

    nineml_type = "ArrayValue"
    defining_attributes = ("_values",)
    DataFile = collections.namedtuple('DataFile', 'url mimetype, columnName')

    def __init__(self, values, datafile=None):
        super(ArrayValue, self).__init__()
        try:
            iter(values)
        except TypeError:
            raise NineMLRuntimeError(
                "'values' argument provided to ArrayValue is not iterable")
        self._values = values
        if datafile is None:
            self._datafile = None
        else:
            self._datafile = self.DataFile(*datafile)

    @property
    def values(self):
        return iter(self._values)

    def __eq__(self, other):
        try:
            if self.nineml_type != other.nineml_type:
                return False
        except AttributeError:
            return False
        return all(nearly_equal(s, o)
                   for s, o in izip(self._values, other._values))

    def __iter__(self):
        return iter(self._values)

    def __getitem__(self, index):
        return self._values[index]

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return "ArrayValue({}{})".format(
            ', '.join(str(v) for v in self._values[:5]),
            ('...' if len(self) >= 5 else ''))

    def __hash__(self):
        return hash(self.values)

    def inverse(self):
        try:
            return ArrayValue(1.0 / self._values)
        except AttributeError:
            raise ArrayValue(1.0 / v for v in self._values)

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        if self._datafile is None:
            return E.ArrayValue(
                *[E.ArrayValueRow(index=i, value=v).to_xml()
                  for i, v in enumerate(self._values)])
        else:
            raise NotImplementedError(
                "TODO: Need to implement code to save data to external file")
            return E.ExternalArrayValue(
                url=self.url, mimetype=self.mimetype,
                columnName=self.columnName)

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        xmlns = extract_xmlns(element.tag)
        if element.tag == 'ExternalArrayValue':
            url = get_xml_attr(element, 'url', document, **kwargs)
            with contextlib.closing(urlopen(url)) as f:
                # FIXME: Should use a non-numpy version of this load function
                values = numpy.loadtxt(f)
            return cls(values, (get_xml_attr(element, 'url', document,
                                             **kwargs),
                                get_xml_attr(element, 'mimetype', document,
                                             **kwargs),
                                get_xml_attr(element, 'columnName', document,
                                             **kwargs)))
        else:
            rows = [(get_xml_attr(e, 'index', document, dtype=int, **kwargs),
                     get_xml_attr(e, 'value', document, dtype=float, **kwargs))
                    for e in element.findall(xmlns + 'ArrayValueRow')]
            sorted_rows = sorted(rows, key=itemgetter(0))
            indices, values = zip(*sorted_rows)
            if indices[0] < 0:
                raise NineMLRuntimeError(
                    "Negative indices found in array rows")
            if len(list(itertools.groupby(indices))) != len(indices):
                groups = [list(g) for g in itertools.groupby(indices)]
                raise NineMLRuntimeError(
                    "Duplicate indices ({}) found in array rows".format(
                        ', '.join(str(g[0]) for g in groups if len(g) > 1)))
            if indices[-1] >= len(indices):
                raise NineMLRuntimeError(
                    "Indices greater or equal to the number of array rows")
            return cls(values)

    # =========================================================================
    # Magic methods to allow the SingleValue to be treated like a
    # floating point number
    # =========================================================================

    def _sympy_(self):
        return sympy.Matrix(self._values)

    def __float__(self):
        raise NineMLRuntimeError(
            "ArrayValues cannot be converted to a single float")

    def __add__(self, num):
        try:
            return self._value + float(num)
        except AttributeError:
            return ArrayValue([v + float(num) for v in self._values])

    def __sub__(self, num):
        try:
            return self._value - float(num)
        except AttributeError:
            return ArrayValue([v - float(num) for v in self._values])

    def __mul__(self, num):
        try:
            return self._value * float(num)
        except AttributeError:
            return ArrayValue([v * float(num) for v in self._values])

    def __truediv__(self, num):
        try:
            return self._value.__truediv__(num)
        except AttributeError:
            return ArrayValue([v / float(num) for v in self._values])

    def __div__(self, num):
        try:
            return self.__truediv__(num)
        except AttributeError:
            return ArrayValue([v.__truediv__(num) for v in self._values])

    def __pow__(self, power):
        try:
            return self._value ** float(power)
        except AttributeError:
            return ArrayValue([v ** float(power) for v in self._values])

    def __floordiv__(self, num):
        try:
            return self._value // float(num)
        except AttributeError:
            return ArrayValue([v // float(num) for v in self._values])

    def __mod__(self, num):
        try:
            return self._value % float(num)
        except AttributeError:
            return ArrayValue([v % float(num) for v in self._values])

    def __radd__(self, num):
        return self.__add__(num)

    def __rsub__(self, num):
        try:
            return float(num) - self._value
        except AttributeError:
            return ArrayValue([float(num) - v for v in self._values])

    def __rmul__(self, num):
        try:
            return float(num) * self._value
        except AttributeError:
            return ArrayValue([float(num) * v for v in self._values])

    def __rtruediv__(self, num):
        try:
            return num.__truediv__(self._value)
        except AttributeError:
            return ArrayValue([v.__truediv__(num) for v in self._values])

    def __rdiv__(self, num):
        try:
            return self._values.__rtruediv__(num)
        except AttributeError:
            return ArrayValue([v.__rtruediv__(num) for v in self._values])

    def __rpow__(self, num):
        try:
            return self._values.__rpow__(num)
        except AttributeError:
            return ArrayValue([float(num) ** v for v in self._values])

    def __rfloordiv__(self, num):
        try:
            return self._values.__rfloordiv__()
        except AttributeError:
            return ArrayValue([float(num) // v for v in self._values])

    def __rmod__(self, num):
        try:
            return self._values.__rmod__()
        except AttributeError:
            return ArrayValue([float(num) % v for v in self._values])

    def __neg__(self):
        try:
            return self._values.__neg__()
        except AttributeError:
            return ArrayValue([-v for v in self._values])

    def __abs__(self):
        try:
            return self._values.__abs__()
        except AttributeError:
            return ArrayValue([abs(v) for v in self._values])


class RandomValue(BaseValue):

    nineml_type = "RandomValue"
    defining_attributes = ("distribution",)

    def __init__(self, distribution):
        super(RandomValue, self).__init__()
        self._distribution = distribution
        self._generator = None

    def __float__(self):
        raise NineMLRuntimeError(
            "RandomValues cannot be converted to a single float")

    def __eq__(self, other):
        try:
            if self.nineml_type != other.nineml_type:
                return False
        except AttributeError:
            return False
        return self.distribution == other.distribution

    @property
    def distribution(self):
        return self._distribution

    def __len__(self):
        return 0

    def __iter__(self):
        if self._generator is None:
            raise NineMLRuntimeError(
                "Generator not set for RandomValue '{}'"
                .format(self))
        yield self._generator()

    def set_generator(self, generator_cls):
        """
        Generator class can be supplied by the implementing package to allow
        the value to be iterated over in the same manner as the other value
        types
        """
        self._generator = generator_cls(self.distribution)

    def __repr__(self):
        return ("RandomValue({})".format(self.distribution.name))

    @annotate_xml
    def to_xml(self, document, E=E, **kwargs):  # @UnusedVariable
        return E(self.nineml_type,
                 self.distribution.to_xml(document, E=E, **kwargs))

    def inverse(self):
        raise NotImplementedError

    @classmethod
    @read_annotations
    @unprocessed_xml
    def from_xml(cls, element, document, **kwargs):  # @UnusedVariable
        distribution = from_child_xml(
            element, nineml.user.RandomDistributionProperties,
            document, allow_reference=True, **kwargs)
        return cls(distribution)
