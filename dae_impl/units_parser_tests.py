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

tokens = [ 'BASE_UNIT',
           'NUMBER', 'FLOAT',
           'EXP'
         ]

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
    """unit_expression : multi_unit"""
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
    
def p_base_unit_1(p):
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
    def __init__(self, dictUnits = None):
        self.lexer  = lex.lex() #optimize=1)
        self.parser = yacc.yacc() #optimize=1)
        self.parseResult = None
        self.dictIdentifiers = dictUnits
        
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

def testConsistency(parser, expression, expected_units):
    parse_res    = parser.parse(expression)
    latex_res    = parser.toLatex()
    print('Expression: ' + expression)
    #print('NodeTree:\n', repr(parse_res))
    print('Parse result: ', str(parse_res))
    try:
        # If no exception has been thrown everything is fine
        eval_res = parser.evaluate()
        print('Units consistency: OK, evaluated {0}, expected {1}\n'.format(eval_res.units, expected_units))
    except RuntimeError as e:
        print('Units consistency failed: {0}\n'.format(str(e)))
        
def testExpression(parser, expression, do_evaluation = True):
    parse_res    = parser.parse(expression)
    latex_res    = parser.toLatex()
    print('Expression: ' + expression)
    #print('NodeTree:\n', repr(parse_res))
    print('Parse result string: ', str(parse_res))
    print('Parse result latex: ', parser.toLatex())
    print('Parse result mathml: ', parser.toMathML())
    #if do_evaluation:
    #    eval_res = parser.evaluate()
    #    print('Evaluate result String: {0}'.format(eval_res.toString()))
    #    print('Evaluate result Latex: {0}'.format(eval_res.toLatex()))
    print(' ')

def testUnitsConsistency():
    dictIdentifiers = {}
    dictFunctions   = {}

    # Define some 'quantity' objects (they have 'value' and 'units')
    y   = 15   * pyUnits.mm
    x1  = 1.0  * pyUnits.m
    x2  = 0.2  * pyUnits.km
    x3  = 15   * pyUnits.N
    x4  = 1.25 * pyUnits.kJ
    print('y  = {0} ({1} {2})'.format(y,  y.valueInSIUnits,  y.units.baseUnit))
    print('x1 = {0} ({1} {2})'.format(x1, x1.valueInSIUnits, x1.units.baseUnit))
    print('x2 = {0} ({1} {2})'.format(x2, x2.valueInSIUnits, x2.units.baseUnit))
    print('x3 = {0} ({1} {2})'.format(x3, x3.valueInSIUnits, x3.units.baseUnit))
    print('x4 = {0} ({1} {2})'.format(x4, x4.valueInSIUnits, x4.units.baseUnit))

    #print('x1({0}) == x2({1}) ({2})'.format(x1, x2, x1 == x2))
    #print('x1({0}) != x2({1}) ({2})'.format(x1, x2, x1 != x2))
    #print('x1({0}) > x2({1}) ({2})'.format(x1, x2, x1 > x2))
    #print('x1({0}) >= x2({1}) ({2})'.format(x1, x2, x1 >= x2))
    #print('x1({0}) < x2({1}) ({2})'.format(x1, x2, x1 < x2))
    #print('x1({0}) <= x2({1}) ({2})'.format(x1, x2, x1 <= x2))
    
    # quantity in [m]
    z = 1 * pyUnits.m
    print(z)
    z.value = 12.4 * pyUnits.mm # set a new value given in [mm]
    print(z)
    z.value = 0.32 * pyUnits.km # set a new value given in [km]
    print(z)
    z.value = 1 # set a new value in units in the quantity object, here in [m]
    print(z)
    
    # Define identifiers for the parser
    dictIdentifiers['pi'] = math.pi
    dictIdentifiers['e']  = math.e
    dictIdentifiers['y']  = y
    dictIdentifiers['x1'] = x1
    dictIdentifiers['x2'] = x2
    dictIdentifiers['x3'] = x3
    dictIdentifiers['x4'] = x4

    # Define math. functions for the parser
    dictFunctions['__create_constant__'] = float
    dictFunctions['sin']   = parser_objects.sin
    dictFunctions['cos']   = parser_objects.cos
    dictFunctions['tan']   = parser_objects.tan
    dictFunctions['asin']  = parser_objects.asin
    dictFunctions['acos']  = parser_objects.acos
    dictFunctions['atan']  = parser_objects.atan
    dictFunctions['sinh']  = parser_objects.sinh
    dictFunctions['cosh']  = parser_objects.cosh
    dictFunctions['tanh']  = parser_objects.tanh
    dictFunctions['asinh'] = parser_objects.asinh
    dictFunctions['acosh'] = parser_objects.cosh
    dictFunctions['atanh'] = parser_objects.atanh
    dictFunctions['log10'] = parser_objects.log10
    dictFunctions['log']   = parser_objects.log
    dictFunctions['sqrt']  = parser_objects.sqrt
    dictFunctions['exp']   = parser_objects.exp
    dictFunctions['floor'] = parser_objects.floor
    dictFunctions['ceil']  = parser_objects.ceil
    dictFunctions['pow']   = parser_objects.pow_
    dictFunctions['abs']   = parser_objects.abs_

    #print('Identifiers:\n', dictIdentifiers, '\n')
    #print('Functions:\n', dictFunctions, '\n')

    parser = ExpressionParser(dictIdentifiers, dictFunctions)

    testConsistency(parser, 'x1 * x3', pyUnits.kJ)                  # OK
    testConsistency(parser, 'x1 - x3', None)                        # Fail
    testConsistency(parser, 'x1 * y', pyUnits.m**2)                 # OK
    testConsistency(parser, '1 + x1/x2 + x1*x3/x4', pyUnits.unit()) # OK
    
def testDimensionsParser():
    dictIdentifiers = {
                        'L' : pyUnits.m,
                        'M' : pyUnits.kg,
                        'T' : pyUnits.s,
                        'I' : pyUnits.A,
                        'O' : pyUnits.K,
                        'J' : pyUnits.cd,
                        'N' : pyUnits.mol
                      }
    parser = UnitsParser(dictIdentifiers)

    testExpression(parser, 'M')
    testExpression(parser, 'M T^2 J^-2')
    testExpression(parser, 'M^5 L^-2 O')

def testUnitsParser():
    pass

if __name__ == "__main__":
    testDimensionsParser()
    #testUnitsParser()
    testUnitsConsistency()
