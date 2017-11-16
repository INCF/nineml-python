from builtins import zip
import math
import sympy
from itertools import chain
from .base import BaseVisitor, BaseDualVisitor, DualWithContextMixin
from nineml.exceptions import (NineMLDualVisitException,
                               NineMLDualVisitValueException,
                               NineMLDualVisitTypeException,
                               NineMLDualVisitKeysMismatchException,
                               NineMLDualVisitNoneChildException,
                               NineMLNotBoundException,
                               NineMLDualVisitAnnotationsMismatchException,
                               NineMLNameError)

NEARLY_EQUAL_PLACES_DEFAULT = 15


class EqualityChecker(BaseDualVisitor):

    def __init__(self, annotations_ns=[], check_urls=True,
                 nearly_equal_places=NEARLY_EQUAL_PLACES_DEFAULT, **kwargs):  # @UnusedVariable @IgnorePep8
        super(EqualityChecker, self).__init__(**kwargs)
        self.annotations_ns = annotations_ns
        self.check_urls = check_urls
        self.nearly_equal_places = nearly_equal_places

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
        if self._not_nearly_equal(val1.value, val2.value):
            self._raise_value_exception('value', val1, val2, nineml_cls)

    def action_arrayvalue(self, val1, val2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        if len(val1.values) != len(val2.values):
            self._raise_value_exception('values', val1, val2, nineml_cls)
        if any(self._not_nearly_equal(s, o)
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

    def _not_nearly_equal(self, float1, float2):
        """
        Determines whether two floating point numbers are nearly equal (to
        within reasonable rounding errors
        """
        mantissa1, exp1 = math.frexp(float1)
        mantissa2, exp2 = math.frexp(float2)
        return not ((round(mantissa1, self.nearly_equal_places) ==
                     round(mantissa2, self.nearly_equal_places)) and
                    exp1 == exp2)


class Hasher(BaseVisitor):

    seed = 0x9e3779b97f4a7c17

    def __init__(self, nearly_equal_places=NEARLY_EQUAL_PLACES_DEFAULT,
                 **kwargs):  # @UnusedVariable @IgnorePep8
        super(Hasher, self).__init__(**kwargs)
        self.nearly_equal_places = nearly_equal_places

    def hash(self, nineml_obj):
        self._hash = None
        self.visit(nineml_obj)
        return self._hash

    def default_action(self, obj, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        for attr_name in nineml_cls.nineml_attr:
            try:
                if attr_name == 'rhs':  # need to use Sympy equality checking
                    self._hash_rhs(obj.rhs)
                else:
                    self._hash_attr(getattr(obj, attr_name))
            except NineMLNotBoundException:
                continue

    def _hash_attr(self, attr):
        attr_hash = hash(attr)
        if self._hash is None:
            self._hash = attr_hash
        else:
            # The rationale behind this equation is explained here
            # https://stackoverflow.com/questions/5889238/why-is-xor-the-default-way-to-combine-hashes
            self._hash ^= (attr_hash + self.seed + (self._hash << 6) +
                           (self._hash >> 2))

    def action_reference(self, ref, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        self._hash_attr(ref.url)

    def action_definition(self, defn, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        self._hash_attr(defn.url)

    def action_singlevalue(self, val, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        self._hash_value(val.value)

    def action_arrayvalue(self, val, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        for v in val.values:
            self._hash_value(v)

    def _hash_rhs(self, rhs, **kwargs):  # @UnusedVariable
        try:
            rhs = sympy.expand(rhs)
        except:
            pass
        self._hash_attr(rhs)

    def action_unit(self, unit, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        # Ignore name
        self._hash_attr(unit.power)
        self._hash_attr(unit.offset)

    def action_dimension(self, dim, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        for sym in nineml_cls.dimension_symbols:
            self._hash_attr(getattr(dim, sym))

    def _hash_value(self, val):
        mantissa, exp = math.frexp(val)
        rounded_val = math.ldexp(round(mantissa, self.nearly_equal_places),
                                 exp)
        self._hash_attr(rounded_val)


class MismatchFinder(DualWithContextMixin, EqualityChecker):

    def __init__(self, **kwargs):
        EqualityChecker.__init__(self, **kwargs)
        DualWithContextMixin.__init__(self)

    def find(self, obj1, obj2, **kwargs):  # @UnusedVariable
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
