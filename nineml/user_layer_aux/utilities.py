from nineml.user_layer_aux.connection_generator import ConnectionGenerator, callCgClosure, cgClosureFromURI
from nineml.user_layer_aux.explicit_list_of_connections import ExplicitListOfConnections

#memoizedConnectionGenerators = {}

def cgFromProjection (projection):
    rule = projection.rule

    # Should we really test for explicit list by testing for attribute?
    if hasattr (rule, 'connections'):
        connections = getattr (rule, 'connections') 
        cg = explicit_list_of_connections_generator.ExplicitListOfConnections (connections)
        return cg

    # Assembling a CG instantiation
    cgClosure = cgClosureFromURI (rule.definition.url)
    cg = callCgClosure (cgClosure, rule.parameters)
    return cg
