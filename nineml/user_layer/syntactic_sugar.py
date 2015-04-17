from . import Component


class SpikingNodeType(Component):
    """
    Component representing a model of a spiking node, i.e. something that can
    emit (and optionally receive) spikes.
    """
    pass


class IonDynamicsType(Component):
    """
    Component representing either a ion channel or the dynamics of the
    concentration of a pool of ions. Typically part of a SpikingNodeType.
    """
    pass


class SynapseType(Component):
    """
    Component representing a model of a post-synaptic response, i.e. the
    current produced in response to a spike.
    """
    pass


class CurrentSourceType(Component):
    """
    Component representing a model of a current source that may be injected
    into a spiking node.
    """
    pass


class ConnectionType(Component):
    """
    Component representing a model of a synaptic connection, including weight,
    delay, optionally a synaptic plasticity rule.
    """
    pass
