"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.abstraction_layer.readers import XMLReader


class CgClosure:

    def __init__(self, formals, pyFunc):
        self.formals = formals
        self.function = pyFunc

    def __call__(self, parameterSet):
        args = map(lambda p: parameterSet[p.name].value, self.formals)
        return self.function(*args)


def alConnectionRuleFromURI(uri):
    component = XMLReader.read(uri)
    return CgClosure(component.parameters, component.connection_rule)
