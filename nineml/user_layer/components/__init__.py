

def get_or_create_component(ref, cls, components):
    """
    Each entry in `components` is either an instance of a BaseComponent
    subclass, or the XML (elementtree Element) defining such an instance.

    If given component does not exist, we create it and replace the XML in
    `components` with the actual component. We then return the component.
    """
    assert ref in components, "%s not in %s" % (ref, components.keys())
    if not isinstance(components[ref], BaseComponent):
        components[ref] = cls.from_xml(components[ref], components)
    return components[ref]

from .base import BaseComponent
from .interface import Value, StringValue, Parameter, InitialValue
