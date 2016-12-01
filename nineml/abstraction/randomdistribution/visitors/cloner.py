"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.visitors.cloner import ComponentCloner, lookup_memo


class RandomDistributionCloner(ComponentCloner):

    @lookup_memo
    def visit_componentclass(self, component_class, **kwargs):
        ccn = component_class.__class__(
            name=component_class.name,
            standard_library=component_class.standard_library,
            parameters=[p.accept_visitor(self, **kwargs)
                        for p in component_class.parameters])
        return ccn
