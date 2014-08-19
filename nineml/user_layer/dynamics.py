from .components import BaseComponent, get_or_create_component, check_units


class BaseDynamicsComponent(BaseComponent):

    def check_initial_values(self):
        for var in self.definition.component.state_variables:
            try:
                initial_value = self.initial_values[var.name]
            except KeyError:
                raise Exception("Initial value not specified for %s" %
                                var.name)
            check_units(initial_value.unit, var.dimension)


class SpikingNodeType(BaseDynamicsComponent):

    """
    Component representing a model of a spiking node, i.e. something that can
    emit (and optionally receive) spikes.

    Should perhaps be called SpikingNodePrototype, since this is type +
    parameters
    """
    abstraction_layer_module = 'dynamics'


class SynapseType(BaseDynamicsComponent):

    """
    Component representing a model of a post-synaptic response, i.e. the
    current produced in response to a spike.

    This class is probably mis-named. Should be PostSynapticResponseType.
    """
    abstraction_layer_module = 'dynamics'


class CurrentSourceType(BaseDynamicsComponent):

    """
    Component representing a model of a current source that may be injected
    into a spiking node.
    """
    abstraction_layer_module = 'dynamics'


class ConnectionType(BaseDynamicsComponent):

    """
    Component representing a model of a synaptic connection, including weight,
    delay, optionally a synaptic plasticity rule.
    """
    abstraction_layer_module = 'dynamics'


def get_or_create_prototype(prototype_ref, components, groups):
    if prototype_ref in groups:
        return groups[prototype_ref]
    else:
        return get_or_create_component(prototype_ref, SpikingNodeType,
                                       components)
