#!/usr/bin/env python
"""
docstring goes here

.. module:: connection_generator.py
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from .. import BaseALObject
from ..componentclass import ComponentClass


class ConnectionRuleBlock(BaseALObject):

    element_name = 'ConnectionRule'
    defining_attributes = ('standard_library',)

    def __init__(self, standard_library):
        self.standard_library = standard_library

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_connectionruleblock(self, **kwargs)


class ConnectionRuleClass(ComponentClass):

    defining_attributes = ('name', '_parameters', '_main_block')

    def __init__(self, name, connectionruleblock, parameters=None):
        super(ConnectionRuleClass, self).__init__(
            name, parameters, main_block=connectionruleblock)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_componentclass(self, **kwargs)

    def __copy__(self):
        return ConnectionRuleCloner().visit(self)

    def rename(self, old_symbol, new_symbol):
        ConnectionRuleRenameSymbol(self, old_symbol, new_symbol)

from .utils.cloner import ConnectionRuleCloner
from .utils.modifiers import ConnectionRuleRenameSymbol
