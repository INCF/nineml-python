from . import Dynamics


class SpikingNodeType(Dynamics):
    """
    Component representing a model of a spiking node, i.e. something that can
    emit (and optionally receive) spikes.
    """
    pass


class IonDynamicsType(Dynamics):
    """
    Component representing either a ion channel or the dynamics of the
    concentration of a pool of ions. Typically part of a SpikingNodeType.
    """
    pass


class SynapseType(Dynamics):
    """
    Component representing a model of a post-synaptic response, i.e. the
    current produced in response to a spike.
    """
    pass


class CurrentSourceType(Dynamics):
    """
    Component representing a model of a current source that may be injected
    into a spiking node.
    """
    pass


class ConnectionType(Dynamics):
    """
    Component representing a model of a synaptic connection, including weight,
    delay, optionally a synaptic plasticity rule.
    """
    pass
