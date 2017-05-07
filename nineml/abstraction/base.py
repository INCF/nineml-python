from ..base import AnnotatedNineMLObject
import sympy
from nineml.utils import ensure_valid_identifier
from nineml.units import Dimension, dimensionless


class BaseALObject(AnnotatedNineMLObject):

    """
    Base class for abstraction layer classes
    """
    layer = 'abstraction'


class Parameter(BaseALObject):

    """A class representing a state-variable in a ``ComponentClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    nineml_type = 'Parameter'
    defining_attributes = ('_name', '_dimension')

    def __init__(self, name, dimension=None):
        """Parameter Constructor

        `name` -- The name of the parameter.
        """
        super(Parameter, self).__init__()
        name = name.strip()
        ensure_valid_identifier(name)

        self._name = name
        self._dimension = dimension if dimension is not None else dimensionless
        assert isinstance(self._dimension, Dimension), (
            "dimension must be None or a nineml.Dimension instance")
#         self.constraints = []  # TODO: constraints can be added in the future

    @property
    def name(self):
        """Returns the name of the parameter"""
        return self._name

    @property
    def dimension(self):
        """Returns the dimensions of the parameter"""
        return self._dimension

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("Parameter({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)))

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_parameter(self, **kwargs)

    def _sympy_(self):
        return sympy.Symbol(self.name)

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.attr('dimension', self.dimension.name, **options)

    @classmethod
    def unserialize_node(cls, node, **options):  # @UnusedVariable
        return cls(name=node.attr('name', **options),
                         dimension=node.visitor.document[
                             node.attr('dimension', **options)])
