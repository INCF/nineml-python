from builtins import zip
import sympy
from itertools import chain
from .base import BaseDualVisitor, DualWithContextMixin
from nineml.exceptions import (NineMLDualVisitException,
                               NineMLDualVisitValueException,
                               NineMLDualVisitTypeException,
                               NineMLDualVisitKeysMismatchException,
                               NineMLDualVisitNoneChildException,
                               NineMLNotBoundException,
                               NineMLDualVisitAnnotationsMismatchException,
                               NineMLNameError)
from nineml.utils import nearly_equal


class EqualityChecker(BaseDualVisitor):

    def __init__(self, annotations_ns=[], check_urls=True, **kwargs):  # @UnusedVariable @IgnorePep8
        super(EqualityChecker, self).__init__()
        self.annotations_ns = annotations_ns
        self.check_urls = check_urls

    def check(self, obj1, obj2, **kwargs):
        try:
            self.visit(obj1, obj2, **kwargs)
        except NineMLDualVisitException:
            return False
        return True

    def action(self, obj1, obj2, nineml_cls, **kwargs):
        if self.annotations_ns:
            try:
                annotations_keys = set(chain(obj1.annotations.branch_keys,
                                             obj2.annotations.branch_keys))
                skip_annotations = False
            except AttributeError:
                skip_annotations = True
            if not skip_annotations:
                for key in annotations_keys:
                    if key[1] in self.annotations_ns:
                        try:
                            annot1 = obj1.annotations.branch(key)
                        except NineMLNameError:
                            self._raise_annotations_exception(
                                nineml_cls, obj1, obj2, key)
                        try:
                            annot2 = obj2.annotations.branch(key)
                        except NineMLNameError:
                            self._raise_annotations_exception(
                                nineml_cls, obj1, obj2, key)
                        self.visit(annot1, annot2, **kwargs)
        return super(EqualityChecker, self).action(obj1, obj2, nineml_cls,
                                                   **kwargs)

    def default_action(self, obj1, obj2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        for attr_name in nineml_cls.nineml_attr:
            if attr_name == 'rhs':  # need to use Sympy equality checking
                self._check_rhs(obj1, obj2, nineml_cls)
            else:
                self._check_attr(obj1, obj2, attr_name, nineml_cls)

    def action_reference(self, ref1, ref2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if self.check_urls:
            self._check_attr(ref1, ref2, 'url', nineml_cls)

    def action_definition(self, def1, def2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if self.check_urls:
            self._check_attr(def1, def2, 'url', nineml_cls)

    def action_singlevalue(self, val1, val2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if not nearly_equal(val1.value, val2.value):
            self._raise_value_exception('value', val1, val2, nineml_cls)

    def action_arrayvalue(self, val1, val2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if len(val1.values) != len(val2.values):
            self._raise_value_exception('values', val1, val2, nineml_cls)
        if any(not nearly_equal(s, o)
               for s, o in zip(val1.values, val2.values)):
            self._raise_value_exception('values', val1, val2, nineml_cls)

    def action_unit(self, unit1, unit2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        # Ignore name
        self._check_attr(unit1, unit2, 'power', nineml_cls)
        self._check_attr(unit1, unit2, 'offset', nineml_cls)

    def action_dimension(self, dim1, dim2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        # Ignore name
        for sym in nineml_cls.dimension_symbols:
            self._check_attr(dim1, dim2, sym, nineml_cls)

    def action__annotationsbranch(self, branch1, branch2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        for attr in nineml_cls.nineml_attr:
            if attr != 'abs_index':
                self._check_attr(branch1, branch2, attr, nineml_cls)

    def _check_rhs(self, expr1, expr2, nineml_cls):
        try:
            expr_eq = (sympy.expand(expr1.rhs - expr2.rhs) == 0)
        except TypeError:
            expr_eq = sympy.Equivalent(expr1.rhs, expr2.rhs) == sympy.true
        if not expr_eq:
            self._raise_value_exception('rhs', expr1, expr2, nineml_cls)

    def _check_attr(self, obj1, obj2, attr_name, nineml_cls):
        try:
            attr1 = getattr(obj1, attr_name)
        except NineMLNotBoundException:
            attr1 = None
        try:
            attr2 = getattr(obj2, attr_name)
        except NineMLNotBoundException:
            attr2 = None
        if attr1 != attr2:
            self._raise_value_exception(attr_name, obj1, obj2, nineml_cls)

    def _raise_annotations_exception(self, nineml_cls, obj1, obj2, key):
        raise NineMLDualVisitException()

    def _raise_value_exception(self, attr_name, obj1, obj2, nineml_cls):
        raise NineMLDualVisitException()


class MismatchFinder(DualWithContextMixin, EqualityChecker):

    def __init__(self, **kwargs):
        EqualityChecker.__init__(self, **kwargs)
        DualWithContextMixin.__init__(self)

    def find(self, obj1, obj2):
        self.mismatch = []
        self.visit(obj1, obj2)
        assert not self.contexts1
        assert not self.contexts2
        return '\n'.join(str(e) for e in self.mismatch)

    def visit(self, *args, **kwargs):
        try:
            super(MismatchFinder, self).visit(*args, **kwargs)
        except NineMLDualVisitException as e:
            self.mismatch.append(e)

    def visit_child(self, child_name, child_type, parent1, parent2,
                    parent_cls, parent_result, **kwargs):
        try:
            super(MismatchFinder, self).visit_child(
                child_name, child_type, parent1, parent2, parent_cls,
                parent_result, **kwargs)
        except NineMLDualVisitException as e:
            self.mismatch.append(e)
            self._pop_contexts()

    def visit_children(self, children_type, parent1, parent2,
                       parent_cls, parent_result, **kwargs):
        try:
            super(MismatchFinder, self).visit_children(
                children_type, parent1, parent2, parent_cls, parent_result,
                **kwargs)
        except NineMLDualVisitException as e:
            self.mismatch.append(e)
            self._pop_contexts()

    def _check_attr(self, obj1, obj2, attr_name, nineml_cls, **kwargs):
        try:
            super(MismatchFinder, self)._check_attr(
                obj1, obj2, attr_name, nineml_cls, **kwargs)
        except NineMLDualVisitException as e:
            self.mismatch.append(e)

    def _check_rhs(self, obj1, obj2, attr_name, **kwargs):
        try:
            super(MismatchFinder, self)._check_rhs(
                obj1, obj2, attr_name, **kwargs)
        except NineMLDualVisitException as e:
            self.mismatch.append(e)

    def action_singlevalue(self, val1, val2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        try:
            super(MismatchFinder, self).action_singlevalue(
                val1, val2, nineml_cls, **kwargs)
        except NineMLDualVisitException as e:
            self.mismatch.append(e)

    def action_arrayvalue(self, val1, val2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        try:
            super(MismatchFinder, self).action_arrayvalue(
                val1, val2, nineml_cls, **kwargs)
        except NineMLDualVisitException as e:
            self.mismatch.append(e)

    def _raise_annotations_exception(self, nineml_cls, obj1, obj2, key):
        raise NineMLDualVisitAnnotationsMismatchException(
            nineml_cls, obj1, obj2, key, self.contexts1, self.contexts2)

    def _raise_value_exception(self, attr_name, obj1, obj2, nineml_cls):
        raise NineMLDualVisitValueException(
            attr_name, obj1, obj2, nineml_cls, self.contexts1, self.contexts2)

    def _raise_type_exception(self, obj1, obj2):
        raise NineMLDualVisitTypeException(
            obj1, obj2, self.contexts1, self.contexts2)

    def _raise_none_child_exception(self, child_name, child1, child2):
        raise NineMLDualVisitNoneChildException(
            child_name, child1, child2, self.contexts1, self.contexts2)

    def _raise_keys_mismatch_exception(self, children_type, obj1, obj2):
        raise NineMLDualVisitKeysMismatchException(
            children_type, obj1, obj2, self.contexts1, self.contexts2)

    def _pop_contexts(self):
        self.contexts1.pop()
        self.contexts2.pop()
