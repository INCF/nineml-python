# encoding: utf-8
from __future__ import division
from builtins import next
from builtins import zip
import re
import operator
from sympy import Symbol
import sympy
import math
from nineml.base import AnnotatedNineMLObject, DocumentLevelObject
from nineml.exceptions import (
    NineMLUsageError, NineMLDimensionError, NineMLValueError,
    NineMLSerializationError)
from nineml.utils import validate_identifier
from functools import reduce


class Dimension(AnnotatedNineMLObject, DocumentLevelObject):
    """
    Defines the dimension used for quantity units
    """

    nineml_type = 'Dimension'
    nineml_attr = ('name', 'm', 'l', 't', 'i', 'n', 'k', 'j')

    dimension_symbols = ('m', 'l', 't', 'i', 'n', 'k', 'j')
    dimension_names = ('mass', 'length', 'time', 'current', 'amount',
                       'temperature', 'luminous_intensity')
    SI_units = ('kg', 'm', 's', 'A', 'mol', 'K', 'cd')

    _trailing_numbers_re = re.compile(r'(.*)(\d+)$')

    def __init__(self, name, dimensions=None, **kwargs):
        self._name = validate_identifier(name)
        AnnotatedNineMLObject.__init__(self)
        DocumentLevelObject.__init__(self)
        if dimensions is not None:
            assert len(dimensions) == 7, "Incorrect dimension length"
            self._dims = tuple(dimensions)
        else:
            self._dims = tuple(kwargs.pop(d, 0)
                               for d in self.dimension_symbols)
        assert not len(kwargs), "Unrecognised kwargs ({})".format(kwargs)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("Dimension(name='{}'{})".format(
            self.name, ''.join(' {}={}'.format(n, p) if p != 0 else ''
                               for n, p in zip(self.dimension_symbols,
                                               self._dims))))

    def __str__(self):
        return self.name

    def __iter__(self):
        return iter(self._dims)

    @property
    def name(self):
        return self._name

    def power(self, name):
        return self._dims[self.dimension_symbols.index(name)]

    def to_SI_units_str(self):
        numer = '*'.join('({}**{})'.format(si, p) if p > 1 else si
                         for si, p in zip(self.SI_units, self._dims) if p > 0)
        denom = '*'.join('({}**{})'.format(si, p) if p < -1 else si
                         for si, p in zip(self.SI_units, self._dims) if p < 0)
        return '{}/({})'.format(numer, denom)

    def _sympy_(self):
        """
        Create a sympy expression by multiplying symbols representing each of
        the dimensions together
        """
        try:
            return reduce(
                operator.mul,
                (Symbol(n) ** p
                 for n, p in zip(self.dimension_symbols, self._dims)))
        except:
            raise

    @property
    def m(self):
        return self._dims[0]

    @property
    def l(self):
        return self._dims[1]

    @property
    def t(self):
        return self._dims[2]

    @property
    def i(self):
        return self._dims[3]

    @property
    def n(self):
        return self._dims[4]

    @property
    def k(self):
        return self._dims[5]

    @property
    def j(self):
        return self._dims[6]

    @property
    def time(self):
        return self.t

    @property
    def temperature(self):
        return self.k

    @property
    def luminous_intensity(self):
        return self.j

    @property
    def amount(self):
        return self.n

    @property
    def mass(self):
        return self.m

    @property
    def length(self):
        return self.l

    @property
    def current(self):
        return self.i

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name)
        for n, p in zip(self.dimension_symbols, self._dims):
            if abs(p) > 0:
                node.attr(n, p)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        name = node.attr('name', **options)
        # Get the attributes corresponding to the dimension symbols
        dim_args = dict((s, node.attr(s, default=0, dtype=int, **options))
                         for s in cls.dimension_symbols)
        return cls(name, **dim_args)

    def __mul__(self, other):
        "self * other"
        return Dimension(self.make_name([self.name, other.name]),
                         dimensions=tuple(s + o for s, o in zip(self, other)))

    def __truediv__(self, other):
        "self / expr"
        return Dimension(self.make_name([self.name], [other.name]),
                         dimensions=tuple(s - o for s, o in zip(self, other)))

    def __pow__(self, power):
        "self ** expr"
        return Dimension(self.make_name([self.name], power=power),
                         dimensions=tuple(s * power for s in self))

    def __div__(self, other):
        return self.__truediv__(other)

    @classmethod
    def make_name(cls, products=[], divisors=[], power=1):
        """
        Generates a sensible name from the combination of dimensions/units.

        E.g.

        voltage * current -> voltage_current
        voltage / current -> voltage_per_current
        voltage ** 2 -> voltage2
        dimensionless / voltage -> per_voltage
        (voltage * current * dimensionless) ** 3 -> current3_voltage3
        """
        if power == 0:
            return 'dimensionless'
        numerator = []
        denominator = []
        for p in products:
            p_split = p.split('_per_')
            numerator.extend(p_split[0].split('_'))
            if len(p_split) > 1:
                denominator.extend(p_split[1].split('_'))
        for d in divisors:
            d_split = d.split('_per_')
            denominator.extend(d_split[0].split('_'))
            if len(d_split) > 1:
                numerator.extend(d_split[1].split('_'))
        num_denoms = []
        for lst in ((numerator, denominator)
                    if power > 0 else (denominator, numerator)):
            new_lst = []
            for dim_name in lst:
                if dim_name not in ('dimensionless', 'unitless', 'none'):
                    if power != 1:
                        assert isinstance(power, int)
                        match = cls._trailing_numbers_re.match(dim_name)
                        if match:
                            name = match.group(1)
                            pw = int(match.group(2)) * power
                        else:
                            name = dim_name
                            pw = power
                        dim_name = name + str(abs(pw))
                    new_lst.append(dim_name)
            num_denoms.append(new_lst)
        numerator, denominator = num_denoms
        name = '_'.join(sorted(numerator))
        if len(denominator):
            if len(numerator):
                name += '_'
            name += 'per_' + '_'.join(sorted(denominator))
        if not name:
            name = 'dimensionless'
        return name

    @classmethod
    def from_sympy(self, expr):
        if expr == 1:
            return dimensionless
        elif not isinstance(expr, sympy.Basic):
            raise NineMLUsageError(
                "Cannot convert '{}' dimension, must be 1 or sympy expression"
                .format(expr))
        powers = {}
        stack = [expr]
        while stack:
            expr = stack.pop()
            if isinstance(expr, sympy.Mul):
                stack.extend(expr.args)
            elif isinstance(expr, sympy.Pow):
                powers[str(expr.args[0])] = expr.args[1]
            else:
                powers[str(expr)] = 1
        name_num = []
        name_den = []
        for sym, p in powers.items():
            name = self.dimension_names[next(
                i for i, s in enumerate(self.dimension_symbols) if s == sym)]
            if abs(p) > 1:
                name += str(abs(p))
            if p > 0:
                name_num.append(name)
            else:
                name_den.append(name)
        name = '_'.join(name_num)
        if name_den:
            if name:
                name += '_'
            name += 'per_' + '_'.join(name_den)
        return Dimension(name, **powers)

    @property
    def origin(self):
        """Returns a Quantity that equal to the origin of this dimension"""
        return Quantity(0.0, Unit(self.name + 'SIUnit', self, power=0))


class Unit(AnnotatedNineMLObject, DocumentLevelObject):
    """
    Defines the units of a quantity
    """

    nineml_type = 'Unit'
    nineml_attr = ('name', 'power', 'offset')
    nineml_child = {'dimension': Dimension}

    def __init__(self, name, dimension, power, offset=0.0):
        self._name = validate_identifier(name)
        AnnotatedNineMLObject.__init__(self)
        DocumentLevelObject.__init__(self)
        assert isinstance(dimension, Dimension)
        self._dimension = dimension
        self._power = power
        self._offset = offset

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return ("Unit(name='{}', dimension='{}', power={}{})"
                .format(self.name, self.dimension.name, self.power,
                        (", offset='{}'".format(self.offset)
                         if self.offset else '')))

    def __str__(self):
        return self.name

    def to_SI_units_str(self):
        if self.offset != 0.0:
            raise Exception("Cannot convert to SI units string as offset is "
                            "not zero ({})".format(self.offset))
        return (self.dimension.to_SI_units_str() +
                ' * 10**({})'.format(self.power) if self.power else '')

    @property
    def name(self):
        return self._name

    @property
    def dimension(self):
        return self._dimension

    def set_dimension(self, dimension):
        """
        Used to standardize dimension names across a NineML document. The
        actual dimension (in terms of fundamental dimension powers) should
        not change.
        """
        assert self.dimension == dimension, "dimensions do not match"
        self._dimension = dimension

    @property
    def power(self):
        return self._power

    @property
    def offset(self):
        return self._offset

    @property
    def symbol(self):
        return self.name

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('symbol', self.name)
        node.attr('dimension', self.dimension.name)
        node.attr('power', self.power)
        if self.offset:
            node.attr('offset', self.offset)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        name = node.attr('symbol', **options)
        dimension = node.document[node.attr('dimension', **options)]
        power = node.attr('power', dtype=int, default=0, **options)
        offset = node.attr('offset', dtype=float, default=0.0, **options)
        return cls(name, dimension, power, offset=offset)

    def __mul__(self, other):
        "self * other"
        try:
            if (self.offset != 0 or other.offset != 0):
                raise NineMLUsageError(
                    "Can't multiply units with nonzero offsets ({} and {})"
                    .format(self, other))
            return Unit(Dimension.make_name([self.name, other.name]),
                        dimension=self.dimension * other.dimension,
                        power=(self.power + other.power))
        except AttributeError:
            return Quantity(other, self)

    def __truediv__(self, other):
        "self / expr"
        try:
            if (self.offset != 0 or other.offset != 0):
                raise NineMLUsageError(
                    "Can't divide units with nonzero offsets ({} and {})"
                    .format(self, other))
            return Unit(Dimension.make_name([self.name], [other.name]),
                        dimension=self.dimension / other.dimension,
                        power=(self.power - other.power))
        except AttributeError:
            if isinstance(other, (float, int)):
                inverted = 1.0 / other
            else:
                inverted = other.inverse()
            return Quantity(inverted, self)

    def __pow__(self, power):
        "self ** expr"
        if self.offset != 0:
            raise NineMLUsageError(
                "Can't raise units to power with nonzero offsets ({})"
                .format(self))
        return Unit(Dimension.make_name([self.name], power=power),
                    dimension=(self.dimension ** power),
                    power=(self.power * power))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return Quantity(float(other), unitless / self)

    def __div__(self, other):
        return self.__truediv__(other)

    def __rdiv__(self, other):
        return self.__rtruediv__(other)


class Quantity(AnnotatedNineMLObject):

    """
    Representation of a numerical- or string-valued parameter.

    A numerical parameter is a (name, value, units) triplet, a string parameter
    is a (name, value) pair.

    Numerical values may either be numbers, or a component_class that generates
    numbers, e.g. a RandomDistribution instance.
    """
    nineml_type = 'Quantity'
    nineml_child = {'value': None,
                    'units': Unit}

    def __init__(self, value, units=None):
        super(Quantity, self).__init__()
        if isinstance(value, Quantity):
            if units is not None:
                value = value.in_units(units)
            else:
                units = value.units
                value = value.value
        elif not isinstance(value, (SingleValue, ArrayValue,
                                    RandomDistributionValue)):
            try:
                # Convert value from float
                value = SingleValue(float(value))
            except TypeError:
                # Convert value from iterable
                value = ArrayValue(value)
        if units is None:
            units = unitless
        elif not isinstance(units, Unit):
            raise Exception("Units ({}) must of type <Unit>".format(units))
        self._value = value
        self._units = units

    @property
    def key(self):
        return self._value.key + '_' + self._units.name

    def __iter__(self):
        """For conveniently expanding quantities like a tuple"""
        return iter((self.value, self.units))

    def __float__(self):
        return float(self.value)

    @property
    def value(self):
        return self._value

    @property
    def units(self):
        return self._units

    def __getitem__(self, index):
        if self.value.is_array():
            return self._value.values[index] * self.units
        elif self.value.is_single():
            return self._value.value * self.units
        else:
            raise NineMLUsageError(
                "Cannot get item from random distribution")

    def set_units(self, units):
        if units.dimension != self.units.dimension:
            raise NineMLDimensionError(
                "Can't change dimension of quantity from '{}' to '{}'"
                .format(self.units.dimension, units.dimension))
        self._value = self.in_units(units)
        self._units = units

    def in_units(self, units):
        """
        Returns a float value in terms of the given units (dimensions must be
        equivalent)
        """
        if units.dimension != self.units.dimension:
            raise NineMLDimensionError(
                "Can't change convert quantity dimension from '{}' to '{}'"
                .format(self.units.dimension, units.dimension))
        return self.value * 10 ** (self.units.power - units.power)

    def __repr__(self):
        return '{} * {}'.format(
            (self.value.value if isinstance(self.value, SingleValue)
             else self.value), self.units)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.child(self._value, **options)
        node.attr('units', self.units.name, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        value = node.child((SingleValue, ArrayValue, RandomDistributionValue),
                           allow_ref=True, **options)
        units_str = node.attr('units', **options)
        try:
            units = node.document[units_str]
        except KeyError:
            raise NineMLSerializationError(
                "Did not find definition of '{}' units in the current "
                "document.".format(units_str))
        return cls(value=value, units=units)

    def __add__(self, qty):
        return Quantity(self.value + self._scaled_value(qty), self.units)

    def __sub__(self, qty):
        return Quantity(self.value - self._scaled_value(qty), self.units)

    def __mul__(self, qty):
        try:
            return Quantity(self.value * qty.value, self.units * qty.units)
        except AttributeError:
            if isinstance(qty, (float, int)):
                return Quantity(self.value * qty, self.units)
            else:
                return Quantity(self.value, self.units * qty)  # If qty is a Unit @IgnorePep8

    def __truediv__(self, qty):
        try:
            return Quantity(self.value / qty.value, self.units / qty.units)
        except AttributeError:
            if isinstance(qty, float):
                return Quantity(self.value / qty, self.units)
            else:
                return Quantity(self.value, self.units / qty)  # If qty is a Unit @IgnorePep8

    def __div__(self, qty):
        return self.__truediv__(qty)

    def __pow__(self, power):
        return Quantity(self.value ** power, self.units ** power)

    def __radd__(self, qty):
        return self.__add__(qty)

    def __rsub__(self, qty):
        return self._scaled_value(qty) - self._value

    def __rmul__(self, qty):
        return self.__mul__(qty)

    def __rtruediv__(self, qty):
        if isinstance(qty, (float, int)):
            qty = qty * unitless
        return qty.__truediv__(self)

    def __rdiv__(self, qty):
        return self.__rtruediv__(qty)

    def __neg__(self):
        return Quantity(-self._value, self.units)

    def __abs__(self):
        return Quantity(abs(self._value), self.units)

    def __lt__(self, qty):
        return self._value < self._scaled_value(qty)

    def __le__(self, qty):
        return self._value <= self._scaled_value(qty)

    def __ge__(self, qty):
        return self._value >= self._scaled_value(qty)

    def __gt__(self, qty):
        return self._value > self._scaled_value(qty)

    def _scaled_value(self, qty):
        try:
            if qty.units.dimension != self.units.dimension:
                raise NineMLDimensionError(
                    "Cannot scale value as dimensions do not match ('{}' and "
                    "'{}')".format(self.units.dimension.name,
                                   qty.units.dimension.name))
            return qty.value * 10 ** (self.units.power - qty.units.power)
        except AttributeError:
            if self.units == unitless:
                return float(qty.value)
            else:
                raise NineMLDimensionError(
                    "Can only add/subtract numbers from dimensionless "
                    "quantities")

    @classmethod
    def parse(cls, qty):
        """
        Parses ints and floats as dimensionless quantities and
        python-quantities Quantity objects into 9ML Quantity objects
        """
        if not isinstance(qty, cls):
            # Assume it is a python quantities quantity and convert to
            # 9ML quantity
            try:
                unit_name = str(qty.units).split()[1].replace(
                    '/', '_per_').replace('**', '').replace('*', '_')
                if unit_name.startswith('_per_'):
                    unit_name = unit_name[1:]  # strip leading underscore
                powers = dict(
                    (cls._pq_si_to_dim[type(u).__name__], p)
                    for u, p in
                    qty.units.simplified._dimensionality.items())
                dimension = Dimension(unit_name + 'Dimension', **powers)
                units = Unit(
                    unit_name, dimension=dimension,
                    power=int(math.log10(float(qty.units.simplified))))
                value = SingleValue(qty)
            except AttributeError:
                if isinstance(qty, (int, float)):
                    value = SingleValue(qty)
                else:
                    try:
                        value = ArrayValue(qty)
                    except NineMLValueError:
                        raise NineMLUsageError(
                            "Cannot convert '{}' to nineml.Quantity (can only "
                            "convert quantities.Quantity and numeric objects)"
                            .format(qty))
                units = unitless
            qty = Quantity(value, units)
        return qty

    _pq_si_to_dim = {'UnitMass': 'm', 'UnitLength': 'l', 'UnitTime': 't',
                     'UnitCurrent': 'i', 'UnitLuminousIntensity': 'j',
                     'UnitSubstance': 'n', 'UnitTemperature': 'k'}

# ----------------- #
# Common dimensions #
# ----------------- #

time = Dimension(name="time", t=1)
per_time = Dimension(name="per_time", t=-1)
voltage = Dimension(name="voltage", m=1, l=2, t=-3, i=-1)
velocity = Dimension(name="velocity", l=1, t=-1)
per_voltage = Dimension(name="per_voltage", m=-1, l=-2, t=3, i=1)
conductance = Dimension(name="conductance", m=-1, l=-2, t=3, i=2)
conductanceDensity = Dimension(name="conductanceDensity", m=-1, l=-4, t=3, i=2)
capacitance = Dimension(name="capacitance", m=-1, l=-2, t=4, i=2)
specificCapacitance = Dimension(name="specificCapacitance", m=-1, l=-4, t=4,
                                i=2)
resistance = Dimension(name="resistance", m=1, l=2, t=-3, i=-2)
resistivity = Dimension(name="resistivity", m=2, l=2, t=-3, i=-2)
charge = Dimension(name="charge", i=1, t=1)
charge_per_mole = Dimension(name="charge_per_mole", i=1, t=1, n=-1)
charge_density = Dimension(name="charge_per_mole", i=1, t=1, m=-3)
mass_per_charge = Dimension(name="mass_per_charge", i=-1, t=-1)
current = Dimension(name="current", i=1)
currentDensity = Dimension(name="currentDensity", i=1, l=-2)
current_per_time = Dimension(name="current", i=1, t=-1)
length = Dimension(name="length", l=1)
area = Dimension(name="area", l=2)
volume = Dimension(name="volume", l=3)
concentration = Dimension(name="concentration", l=-3, n=1)
per_time_per_concentration = Dimension(name="concentration", l=3, n=-1, t=-1)
substance = Dimension(name="substance", n=1)
flux = Dimension(name="flux", m=1, l=-3, t=-1)
substance_per_area = Dimension(name="substance", n=1, l=-2)
permeability = Dimension(name="permeability", l=1, t=-1)
temperature = Dimension(name="temperature", k=1)
idealGasConstantDims = Dimension(name="idealGasConstantDims", m=1, l=2, t=-2,
                                 k=-1, n=-1)
rho_factor = Dimension(name="rho_factor", l=-1, n=1, i=-1, t=-1)
dimensionless = Dimension(name="dimensionless")
energy_per_temperature = Dimension(name="energy_per_temperature", m=1, l=2,
                                   t=-2, k=-1)
luminous_intensity = Dimension(name="luminous_intensity", j=1)

# ------------ #
# Common units #
# ------------ #

s = Unit(name="s", dimension=time, power=0)
per_s = Unit(name="per_s", dimension=per_time, power=0)
Hz = Unit(name="Hz", dimension=per_time, power=0)
kHz = Unit(name="kHz", dimension=per_time, power=3)
ms = Unit(name="ms", dimension=time, power=-3)
per_ms = Unit(name="per_ms", dimension=per_time, power=3)
m = Unit(name="m", dimension=length, power=0)
cm = Unit(name="cm", dimension=length, power=-2)
um = Unit(name="um", dimension=length, power=-6)
m2 = Unit(name="m2", dimension=area, power=0)
cm2 = Unit(name="cm2", dimension=area, power=-4)
um2 = Unit(name="um2", dimension=area, power=-12)
m3 = Unit(name="m3", dimension=volume, power=0)
cm3 = Unit(name="cm3", dimension=volume, power=-6)
litre = Unit(name="litre", dimension=volume, power=-3)
um3 = Unit(name="um3", dimension=volume, power=-18)
V = Unit(name="V", dimension=voltage, power=0)
mV = Unit(name="mV", dimension=voltage, power=-3)
per_V = Unit(name="per_V", dimension=per_voltage, power=0)
per_mV = Unit(name="per_mV", dimension=per_voltage, power=3)
ohm = Unit(name="ohm", dimension=resistance, power=0)
kohm = Unit(name="kohm", dimension=resistance, power=3)
Mohm = Unit(name="Mohm", dimension=resistance, power=6)
S = Unit(name="S", dimension=conductance, power=0)
mS = Unit(name="mS", dimension=conductance, power=-3)
uS = Unit(name="uS", dimension=conductance, power=-6)
nS = Unit(name="nS", dimension=conductance, power=-9)
pS = Unit(name="pS", dimension=conductance, power=-12)
S_per_m2 = Unit(name="S_per_m2", dimension=conductanceDensity, power=0)
mS_per_cm2 = Unit(name="mS_per_cm2", dimension=conductanceDensity, power=1)
S_per_cm2 = Unit(name="S_per_cm2", dimension=conductanceDensity, power=4)
F = Unit(name="F", dimension=capacitance, power=0)
uF = Unit(name="uF", dimension=capacitance, power=-6)
nF = Unit(name="nF", dimension=capacitance, power=-9)
pF = Unit(name="pF", dimension=capacitance, power=-12)
F_per_m2 = Unit(name="F_per_m2", dimension=specificCapacitance, power=0)
uF_per_cm2 = Unit(name="uF_per_cm2", dimension=specificCapacitance, power=-2)
ohm_m = Unit(name="ohm_m", dimension=resistivity, power=0)
kohm_cm = Unit(name="kohm_cm", dimension=resistivity, power=1)
ohm_cm = Unit(name="ohm_cm", dimension=resistivity, power=-2)
C = Unit(name="C", dimension=charge, power=0)
C_per_mol = Unit(name="C_per_mol", dimension=charge_per_mole, power=0)
A = Unit(name="A", dimension=current, power=0)
mA = Unit(name="mA", dimension=current, power=-3)
uA = Unit(name="uA", dimension=current, power=-6)
nA = Unit(name="nA", dimension=current, power=-9)
pA = Unit(name="pA", dimension=current, power=-12)
A_per_m2 = Unit(name="A_per_m2", dimension=currentDensity, power=0)
uA_per_cm2 = Unit(name="uA_per_cm2", dimension=currentDensity, power=-2)
mA_per_cm2 = Unit(name="mA_per_cm2", dimension=currentDensity, power=1)
mol_per_m3 = Unit(name="mol_per_m3", dimension=concentration, power=0)
mol_per_cm3 = Unit(name="mol_per_cm3", dimension=concentration, power=6)
M = Unit(name="M", dimension=concentration, power=3)
mM = Unit(name="mM", dimension=concentration, power=0)
mol = Unit(name="mol", dimension=substance, power=0)
m_per_s = Unit(name="m_per_s", dimension=permeability, power=0)
cm_per_s = Unit(name="cm_per_s", dimension=permeability, power=-2)
um_per_ms = Unit(name="um_per_ms", dimension=permeability, power=-3)
cm_per_ms = Unit(name="cm_per_ms", dimension=permeability, power=1)
degC = Unit(name="degC", dimension=temperature, power=0, offset=273.15)
K = Unit(name="K", dimension=temperature, power=0)
J_per_K_per_mol = Unit(name="J_per_K_per_mol", dimension=idealGasConstantDims,
                       power=0)
J_per_K = Unit(name="J_per_K", dimension=energy_per_temperature, power=0)
mol_per_m_per_A_per_s = Unit(name="mol_per_m_per_A_per_s",
                             dimension=rho_factor, power=0)
unitless = Unit(name="unitless", dimension=dimensionless, power=0)
coulomb = Unit(name="coulomb", dimension=current_per_time, power=0)
cd = Unit(name="cd", dimension=luminous_intensity, power=0)
kg_per_coulomb = Unit(name="kg_per_coulomb", dimension=mass_per_charge,
                      power=0)
cm_per_s = Unit(name="cm_per_s", dimension=velocity, power=-2)
pF_per_nA = Unit(name='pF_per_nA', dimension=voltage / time, power=-6)


from nineml.values import (  # @IgnorePep8
    SingleValue, ArrayValue, RandomDistributionValue)
