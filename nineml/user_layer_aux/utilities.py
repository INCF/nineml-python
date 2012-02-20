from nineml.user_layer_aux.connection_generator import ConnectionGenerator, cgClosureFromURI
from nineml.user_layer_aux.cg_closure import cgClosureFromURI
from nineml.user_layer_aux.explicit_list_of_connections import ExplicitListOfConnections

#memoizedConnectionGenerators = {}

def cgFromProjection (projection):
    rule = projection.rule

    # Should we really test for explicit list by testing for attribute?
    if hasattr (rule, 'connections'):
        connections = getattr (rule, 'connections') 
        cg = ExplicitListOfConnections (connections)
        return cg

    # Assembling a CG instantiation
    cgClosure = cgClosureFromURI (rule.definition.url)
    cg = cgClosure (rule.parameters)
    return cg
