"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ..base import ComponentActionVisitor


class BaseValidator(ComponentActionVisitor):

    def get_warnings(self):
        raise NotImplementedError()
