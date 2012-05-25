from __future__ import print_function
import os, sys, operator, math
import ply.lex as lex
import ply.yacc as yacc
import parser_objects
from parser_objects import Number, BinaryNode, IdentifierNode, ConstantNode
from expression_parser import ExpressionParser
try:
    from daetools.pyDAE import pyUnits
except ImportError as e:
    print(e)

tokens = [ 'BASE_UNIT', 'NUMBER', 'FLOAT', 'EXP' ]

t_EXP    = r'\^'
t_NUMBER = r'(\+|-)?\d+'
t_FLOAT  = r'(\+|-)?(\d+)(\.\d+)'

t_ignore = " \t\n"

t_BASE_UNIT = r'[a-zA-Z_][a-zA-Z_0-9]*'

def t_error(t):
    print("Illegal character '{0}' found while parsing '{1}'".format(t.value[0], t.value))
    #t.lexer.skip(1)

# Parser rules:
def p_expression_1(p):
    """
    unit_expression :
                    | multi_unit
    """
    if len(p) == 1: # Empty string
        p[0] = Number(IdentifierNode(''))
    else:
        p[0] = p[1]

def p_multi_unit_1(p):
    """multi_unit : multi_unit unit"""
    p[0] = p[1] * p[2]

def p_multi_unit_2(p):
    """multi_unit : unit"""
    p[0] = p[1]

def p_unit_1(p):
    """unit :  base_unit"""
    p[0] = p[1]

def p_unit_2(p):
    """unit :  base_unit EXP constant"""
    p[0] = p[1] ** p[3]

def p_constant_1(p):
    """constant : NUMBER"""
    p[0] = Number(ConstantNode(int(p[1])))
    
def p_constant_2(p):
    """constant : FLOAT"""
    p[0] = Number(ConstantNode(float(p[1])))
    
def p_base_unit(p):
    """base_unit : BASE_UNIT  """
    p[0] = Number(IdentifierNode(p[1]))
    
def p_error(p):
    raise Exception("Syntax error at '%s'" % p.value)

class UnitsParser:
    """
    The parser supports dimensions/units in the following format:
       "id_1^exp_1 id_2^exp_2 ... id_n^exp_n"
    where 'id' can be either a dimension or an unit (depending on what is in the dictionary)
    To evaluate the AST tree objects that support the above operators should be provided in dictIdentifiers.
    Dictionary 'dictIdentifiers' should contain pairs of the following type:
        dimension-name:dimension-object (dimension-objects must define * and ** operators)
        unit-name:unit-object (unit-objects must define * and ** operators)
    Instances of the 'unit' class from daetools.pyUnits module could be used as unit/dimension-objects.
    """
    def __init__(self, dictIdentifiers = None):
        self.lexer  = lex.lex() #optimize=1)
        self.parser = yacc.yacc() #optimize=1)
        self.parseResult = None
        self.dictIdentifiers = dictIdentifiers
        
    def parse(self, expression):
        self.parseResult = self.parser.parse(expression, lexer = self.lexer)
        return self.parseResult

    def parse_and_evaluate(self, expression):
        self.parse(expression)
        return self.evaluate()

    def parse_to_latex(self, expression):
        self.parse(expression)
        return self.toLatex()

    def toLatex(self):
        if self.parseResult is None:
            raise RuntimeError('expression not parsed yet')
        return self.parseResult.toLatex()

    def toMathML(self):
        if self.parseResult is None:
            raise RuntimeError('expression not parsed yet')
        return self.parseResult.toMathML()

    def evaluate(self):
        if self.parseResult is None:
            raise RuntimeError('expression not parsed yet')
        if self.dictIdentifiers is None:
            raise RuntimeError('dictIdentifiers not set')

        node = None
        if isinstance(self.parseResult, Number):
            node = self.parseResult.Node
        else:
            raise RuntimeError('Invalid parse result type')

        result = node.evaluate(self.dictIdentifiers, None)
        return result
