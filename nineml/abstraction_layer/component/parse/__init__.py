"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

class NineMLMathParseError(ValueError):
    pass


from expr_parse import expr_parse as expr
from cond_parse import cond_parse as cond
# import cond_parse as cond
