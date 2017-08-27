from . import BaseULObject
from nineml.base import DocumentLevelObject
from nineml.user import DynamicsProperties, MultiDynamicsProperties


class ComponentArray(BaseULObject, DocumentLevelObject):

    nineml_type = "ComponentArray"
    defining_attributes = ('_name', "_size", "_dynamics_properties")
    nineml_attrs = ('name', 'size', 'dynamics_properties')
    suffix = {'pre': '__cell', 'post': '__cell', 'response': '__psr',
              'plasticity': '__pls'}

    def __init__(self, name, size, dynamics_properties):
        self._name = name
        BaseULObject.__init__(self)
        DocumentLevelObject.__init__(self)
        self.size = size
        self._dynamics_properties = dynamics_properties

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = int(size)

    @property
    def dynamics_properties(self):
        return self._dynamics_properties

    @property
    def component_class(self):
        return self.dynamics_properties.component_class

    def serialize_node(self, node, **options):  # @UnusedVariable
        node.attr('name', self.name, **options)
        node.attr('Size', self.size, in_body=True, **options)
        node.child(self.dynamics_properties, **options)

    @classmethod
    def unserialize_node(cls, node, **options):
        dynamics_properties = node.child(
            (DynamicsProperties, MultiDynamicsProperties), allow_ref=True,
            **options)
        return cls(name=node.attr('name', **options),
                   size=node.attr('Size', in_body=True, dtype=int, **options),
                   dynamics_properties=dynamics_properties)

