# import math_namespace
from nineml.exceptions import NineMLUsageError
from .. import BaseALObject
from .base import ExpressionWithSimpleLHS, ExpressionSymbol, Expression
from nineml.units import unitless, Unit, Quantity
from nineml.utils import validate_identifier
from nineml.exceptions import NineMLDimensionError


class Alias(BaseALObject, ExpressionWithSimpleLHS):

    """Aliases are a way of defining a variable local to a ``ComponentClass``,
    in terms of its ``Parameters``, ``StateVariables`` and input ``Analog
    Ports``. ``Alias``es allow us to reduce the duplication of code in
    ComponentClass definition, and allow allow more complex outputs to
    ``AnalogPort`` than simply individual ``StateVariables``.

   When specified from a ``string``, an alias uses the notation ``:=``

    ``Alias``es can be defined in terms of other ``Alias``es, so for example,
    if we had ComponentClass representing a Hodgkin-Huxley style gating
    channel, which has a ``Property``, `reversal_potential`, and an input
    ``AnalogPort``, `membrane_voltage`, then we could define an ``Alias``::

        ``driving_force := reversal_potential - membrane_voltage``

    If the relevant ``StateVariables``, ``m`` and ``h``, for example were also
    defined, and a ``Parameter``, ``g_bar``, we could also define the current
    flowing through this channel as::

        current := driving_force * g * m * m * m * h

    This current could then be attached to an output ``AnalogPort`` for
    example.

    It is important to ensure that Alias definitions are not circular, for
    example, it is not valid to define two alias in terms of each other::

        a := b + 1
        b := 2 * a

    During code generation, we typically call ``ComponentClass.backsub_all()``.
    This method first expands each alias in terms of other aliases, such that
    each alias depends only on Parameters, StateVariables and *incoming*
    AnalogPort. Next, it expands any alias definitions within TimeDerivatives,
    StateAssignments, Conditions and output AnalogPorts.



    """
    nineml_type = 'Alias'
    nineml_attr = ('name', 'rhs')

    def __init__(self, name, rhs=None):
        """ Constructor for an Alias

        :param lhs: A `string` specifying the left-hand-side, i.e. the Alias
            name. This should be a single `symbol`.
        :param rhs: A `string` specifying the right-hand-side. This should be a
            mathematical expression, expressed in terms of other Aliases,
            StateVariables, Parameters and *incoming* AnalogPorts local to the
            Component.

        """
        BaseALObject.__init__(self)
        ExpressionWithSimpleLHS.__init__(self, name, rhs)

    def __repr__(self):
        return "Alias(name='{}', rhs='{}')".format(self.name, self.rhs)

    def __str__(self):
        return "{} := {}".format(self.name, self.rhs)

    @property
    def name(self):
        return self._name

    @classmethod
    def from_str(cls, alias_string):
        """Creates an Alias object from a string"""
        if not cls.is_alias_str(alias_string):
            errmsg = "Invalid Alias: %s" % alias_string
            raise NineMLUsageError(errmsg)

        lhs, rhs = alias_string.split(':=')
        return Alias(name=lhs.strip(), rhs=rhs.strip())

    @classmethod
    def is_alias_str(cls, alias_str):
        """ Returns True if the string could be an alias"""
        return ':=' in alias_str

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.lhs, **options)
        node.attr('MathInline', self.rhs_xml, in_body=True, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        name = node.attr('name', **options)
        rhs = node.attr('MathInline', in_body=True, dtype=Expression,
                        **options)
        return cls(name=name, rhs=rhs)


class Constant(BaseALObject, ExpressionSymbol):

    nineml_type = 'Constant'
    nineml_attr = ('name', 'value')
    nineml_child = {'units': Unit}

    # Specify that serialized constants have bodies in v1
    has_serial_body = 'v1'

    def __init__(self, name, value, units=None):
        BaseALObject.__init__(self)
        self._name = validate_identifier(name)
        if isinstance(value, Quantity):
            if units is None:
                self._value = float(value._value)
                self._units = value.units
            elif units.dimension == value.units.dimension:
                self._value = float(value._value * 10 ** (units.power -
                                                          value.units.power))
                self._units = units
            else:
                raise NineMLDimensionError(
                    "Dimensions do not match between provided quantity ({}) "
                    "and units ({})".format(value.units.dimension,
                                            units.dimension))
        else:
            self._value = float(value)
            self._units = units if units is not None else unitless
        if not isinstance(self._units, Unit):
            raise NineMLUsageError(
                "'units' in '{}' constant needs to be a Unit obj ({}). "
                "Supplied arguments were ({}, {}, {}).".format(
                    self.name, self._units, name, value, units))

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @property
    def units(self):
        return self._units

    def __repr__(self):
        return ("Constant(name={}, value={}, units={})"
                .format(self.name, self.value, self.units))

    def name_transform_inplace(self, name_map):
        try:
            self.name = name_map[self.name]
        except KeyError:
            assert False, "'{}' was not found in name_map".format(self.name)

    def set_units(self, units):
        assert self.units == units, \
            "Renaming units with ones that do not match"
        self._units = units

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.attr('units', self.units.name, **options)
        node.attr('value', self.value, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(
            name=node.attr('name', **options),
            value=node.attr('value', dtype=float, **options),
            units=node.visitor.document[
                node.attr('units', **options)])

    def serialize_node_v1(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.attr('units', self.units.name, **options)
        node.body(self.value, **options)

    @classmethod
    def unserialize_node_v1(cls, node, **options):  # @UnusedVariable
        return cls(
            name=node.attr('name', **options),
            value=node.body(dtype=float, **options),
            units=node.visitor.document[
                node.attr('units', **options)])
