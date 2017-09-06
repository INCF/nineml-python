import sympy
from itertools import izip
from .base import BaseDualVisitor
from nineml.exceptions import (NineMLDualVisitTypeException,
                               NineMLDualVisitKeysMismatchException,
                               NineMLDualVisitValueException,
                               NineMLNotBoundException)
from nineml.utils import nearly_equal


class EqualityChecker(BaseDualVisitor):

    def __init__(self, annotations_ns=True, **kwargs):  # @UnusedVariable
        super(EqualityChecker, self).__init__()
        self.annotations_ns = annotations_ns

    def check(self, obj1, obj2, **kwargs):
        try:
            self.visit(obj1, obj2, **kwargs)
        except (NineMLDualVisitTypeException,
                NineMLDualVisitKeysMismatchException,
                NineMLDualVisitValueException):
            return False
        return True

    def action(self, obj1, obj2, nineml_cls, **kwargs):
#         for ns in self.annotation_ns:
#             self.visit(obj1.annotations[ns], obj2.annotations[ns], **kwargs)
        return super(EqualityChecker, self).action(obj1, obj2, nineml_cls,
                                                   **kwargs)

    def default_action(self, obj1, obj2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        for attr_name in nineml_cls.nineml_attr:
            if attr_name == 'rhs':  # need to use Sympy equality checking
                self._check_rhs(obj1, obj2, nineml_cls)
            else:
                self._check_attr(obj1, obj2, attr_name, nineml_cls)

    def action_reference(self, ref1, ref2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        self._check_attr(ref1, ref2, 'url')

    def action_definition(self, def1, def2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        self._check_attr(def1, def2, 'url')

    def action_singlevalue(self, val1, val2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if not nearly_equal(val1.value, val2.value):
            raise NineMLDualVisitValueException(
                'value', val1, val2, self.contexts1, self.contexts2)

    def action_arrayvalue(self, val1, val2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if not all(nearly_equal(s, o)
                   for s, o in izip(val1.values, val1.values)):
            raise NineMLDualVisitValueException(
                'values', val1, val2, self.contexts1, self.contexts2)

    def _check_rhs(self, expr1, expr2, nineml_cls):
        try:
            expr_eq = (sympy.expand(expr1.rhs - expr2.rhs) == 0)
        except TypeError:
            expr_eq = sympy.Equivalent(expr1.rhs, expr2.rhs) == sympy.true
        if not expr_eq:
            raise NineMLDualVisitValueException(
                'rhs', expr1, expr2, nineml_cls, self.contexts1,
                self.contexts2)

    def _check_attr(self, obj1, obj2, attr_name, nineml_cls):
        try:
            if getattr(obj1, attr_name) != getattr(obj2, attr_name):
                raise NineMLDualVisitValueException(
                    attr_name, obj1, obj2, nineml_cls, self.contexts1,
                    self.contexts2)
        except NineMLNotBoundException:
            pass


class MismatchPrinter(EqualityChecker):

    def mismatch(self, obj1, obj2, **kwargs):
        try:
            self.visit(obj1, obj2, **kwargs)
        except NineMLDualVisitTypeException as e:
            print("Mismatch in type: first={}, second={}, expected={}, "
                  "first-context={}, second-context={}"
                  .format(type(e.obj1), type(e.obj2), e.nineml_cls,
                          self._format_context(e.contexts1),
                          self._format_context(e.contexts2)))
        except NineMLDualVisitKeysMismatchException as e:
            print("Mismatch between {} keys: first={}, second={}, "
                  "first-context={}, second-context={}"
                  .format(e.children_type.nineml_type,
                          tuple(sorted(e.obj1_member_keys_iter())),
                          tuple(sorted(e.obj2_member_keys_iter())),
                          self._format_context(e.contexts1),
                          self._format_context(e.contexts2)))
        except NineMLDualVisitValueException as e:
            print("Mismatch between {} attributes of {}: first={}, second={}, "
                  "first-context={}, second-context={}"
                  .format(e.attr_name,
                          e.nineml_cls.nineml_type,
                          getattr(obj1, e.attr_name),
                          getattr(obj2, e.attr_name),
                          self._format_context(e.contexts1, obj=e.obj1),
                          self._format_context(e.contexts2, obj=e.obj2)))

    @classmethod
    def _format_context(self, contexts, obj=None):
        out = '>'.join('{}({})'.format(type(c.parent).__name__, c.parent.key)
                       for c in contexts)
        if obj is not None:
            out += '>{}({})'.format(type(obj).__name__, obj.key)
