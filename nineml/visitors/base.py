from builtins import object
from collections import OrderedDict, namedtuple
from nineml.exceptions import (
    NineMLInvalidElementTypeException,
    NineMLDualVisitException, NineMLDontVisitChildrenException)


class OrderedDefaultOrderedDictDict(OrderedDict):

    def __missing__(self, key):
        self[key] = value = OrderedDict()
        return value

Context = namedtuple('Context', ('parent', 'parent_cls', 'parent_result',
                                 'attr_name', 'dct'))


class BaseVisitor(object):
    """
    Generic visitor base class that visits a 9ML object and all children (and
    children's children etc...) and calls 'action_<nineml-type>'. These methods
    are not implemented in this base class but can be overridden in derived
    classes that wish to perform an action on specific element types.

    For example to perform an action on all units (and nothing else) in the
    object a derived class can be written as

    class UnitVisitor(Visitor):

        def action_unit(unit, **kwargs):
            # Do action here

    """

    as_class = type(None)

    def visit(self, obj, nineml_cls=None, **kwargs):
        # Use the class of the object to visit the object as if one is not
        # explicitly provided. This allows classes to be visited as if they
        # were base classes (e.g. Dynamics instead of MultiDynamics)
        nineml_cls = self._get_nineml_cls(obj, nineml_cls)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        try:
            result = self.action(obj, nineml_cls=nineml_cls, **kwargs)
            # Add the container object to the list of scopes
            for child_name, child_type in nineml_cls.nineml_child.items():
                self.visit_child(child_name, child_type, obj,
                                 nineml_cls, result, **kwargs)
            # Visit children of the object
            for children_type in nineml_cls.nineml_children:
                self.visit_children(children_type, obj, nineml_cls, result,
                                    **kwargs)
        except NineMLDontVisitChildrenException as e:
            result = e.result
        return result

    def visit_child(self, child_name, child_type, parent, parent_cls=None,  # @UnusedVariable @IgnorePep8
                    parent_result=None, **kwargs):  # @UnusedVariable
        child = getattr(parent, child_name)
        if child is None:
            return None  # e.g. Projection.plasticity
        return self.visit(child, nineml_cls=child_type, **kwargs)

    def visit_children(self, children_type, parent, parent_cls=None,  # @UnusedVariable @IgnorePep8
                       parent_result=None, **kwargs):  # @UnusedVariable
        results = []
        for child in parent._members_iter(children_type):
            results.append(self.visit(child, nineml_cls=children_type,
                                      **kwargs))
        return results

    def action(self, obj, nineml_cls, **kwargs):
        try:
            method = getattr(self, 'action_' + nineml_cls.nineml_type.lower())
        except AttributeError:
            method = self.default_action
        return method(obj, nineml_cls=nineml_cls, **kwargs)

    def default_action(self, obj, nineml_cls, **kwargs):  # @UnusedVariable
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_action' method
        """
        assert False, ("No default action provided, so can't action {} ({})"
                       .format(nineml_cls, obj))

    def _get_nineml_cls(self, obj, nineml_cls):
        if nineml_cls is None:
            nineml_cls = (self.as_class
                          if isinstance(obj, self.as_class) else type(obj))
        return nineml_cls


class BasePreAndPostVisitor(BaseVisitor):

    def visit(self, obj, nineml_cls=None, **kwargs):
        nineml_cls = self._get_nineml_cls(obj, nineml_cls)
        pre_result = BaseVisitor.visit(self, obj, nineml_cls=nineml_cls,
                                       **kwargs)
        post_result = self.post_action(obj, pre_result, nineml_cls, **kwargs)
        return pre_result, post_result

    def post_action(self, obj, pre_result, nineml_cls, **kwargs):
        try:
            method = getattr(self, ('post_action_' +
                                    nineml_cls.nineml_type.lower()))
        except AttributeError:
            method = self.default_post_action
        return method(obj, pre_result, nineml_cls=nineml_cls,
                      **kwargs)


    def default_post_action(self, obj, pre_result, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_post_action' method
        """
        assert False, ("No default post_action provided, so can't post_action "
                       "{} ({})".format(nineml_cls, obj))


class BaseChildResultsVisitor(BaseVisitor):
    """
    A generic visitor base class that visits child and children objects
    first and passes their results to the action method.
    """

    def visit(self, obj, nineml_cls=None, **kwargs):
        # Use the class of the object to visit the object as if one is not
        # explicitly provided. This allows classes to be visited as if they
        # were base classes (e.g. Dynamics instead of MultiDynamics)
        nineml_cls = self._get_nineml_cls(obj, nineml_cls)
        # Add the container object to the list of scopes
        child_results = {}
        for child_name, child_type in nineml_cls.nineml_child.items():
            child_results[child_name] = self.visit_child(
                child_name, child_type, obj, nineml_cls, **kwargs)
        # Visit children of the object
        children_results = {}
        for children_type in nineml_cls.nineml_children:
            children_results[children_type] = self.visit_children(
                children_type, obj, **kwargs)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        result = self.action(obj, nineml_cls=nineml_cls,
                             child_results=child_results,
                             children_results=children_results, **kwargs)
        return result


class WithContextMixin(object):
    """
    Adds the context of the object with the hierarchy, i.e. its parent,
    the parents action result and the dictionary it belongs to.
    """

    def __init__(self):
        self.contexts = []

    def visit_child(self, child_name, child_type, parent,
                    parent_cls, parent_result, **kwargs):  # @UnusedVariable
        # Create the context around the visit of the attribute
        context = Context(parent, parent_cls, parent_result, child_name, None)
        self.contexts.append(context)
        result = BaseVisitor.visit_child(
            self, child_name, child_type, parent, parent_cls, **kwargs)
        popped = self.contexts.pop()
        assert context is popped
        return result

    def visit_children(self, children_type, parent, parent_cls, parent_result,
                       **kwargs):
        try:
            dct = parent._member_dict(children_type)
        except (NineMLInvalidElementTypeException, AttributeError):
            dct = None  # If children_type is a base class of the obj
        context = Context(parent, parent_cls, parent_result, None, dct)
        self.contexts.append(context)
        results = BaseVisitor.visit_children(
            self, children_type, parent, **kwargs)
        popped = self.contexts.pop()
        assert context is popped
        return results

    @property
    def context(self):
        if self.contexts:
            context = self.contexts[-1]
        else:
            context = None
        return context


class BaseVisitorWithContext(WithContextMixin, BaseVisitor):

    pass


class BasePreAndPostVisitorWithContext(WithContextMixin,
                                       BasePreAndPostVisitor):

    pass


class BaseDualVisitor(BaseVisitor):
    """
    Generic visitor base class that visits two 9ML objects side-by-side
    """

    def __init__(self, allow_flatten=False, **kwargs):  # @UnusedVariable
        super(BaseDualVisitor, self).__init__()
        self.allow_flatten = allow_flatten

    def visit(self, obj1, obj2, nineml_cls=None, **kwargs):
        # Use the class of the object to visit the object as if one is not
        # explicitly provided. This allows classes to be visited as if they
        # were base classes (e.g. Dynamics instead of MultiDynamics)
        nineml_cls = self._get_nineml_cls(obj1, obj2, nineml_cls)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        result = self.action(obj1, obj2, nineml_cls=nineml_cls, **kwargs)
        # Add the container object to the list of scopes
        for child_name, child_type in nineml_cls.nineml_child.items():
            self.visit_child(child_name, child_type, obj1, obj2,
                             parent_cls=nineml_cls, parent_result=result,
                             **kwargs)
        # Visit children of the object
        for children_type in nineml_cls.nineml_children:
            self.visit_children(children_type, obj1, obj2,
                                parent_cls=nineml_cls, parent_result=result,
                                **kwargs)
        return result

    def _get_nineml_cls(self, obj1, obj2, nineml_cls):
        try:
            if obj1.nineml_type != obj2.nineml_type and not self.allow_flatten:
                self._raise_type_exception(obj1, obj2)
        except AttributeError:
            self._raise_type_exception(obj1, obj2)
        if nineml_cls is None:
            if isinstance(obj1, self.as_class):
                nineml_cls = self.as_class
            elif isinstance(obj2, type(obj1)):
                nineml_cls = type(obj1)
            elif isinstance(obj1, type(obj2)):
                nineml_cls = type(obj2)
            else:
                self._raise_type_exception(obj1, obj2)
        return nineml_cls

    def visit_child(self, child_name, child_type, parent1, parent2,
                    parent_cls=None, parent_result=None, **kwargs):  # @UnusedVariable @IgnorePep8
        child1 = getattr(parent1, child_name)
        child2 = getattr(parent2, child_name)
        if child1 is None and child2 is None:
            return None  # Both children are None so return
        elif child1 is None or child1 is None:
            self._raise_none_child_exception(self, child_name, child1, child2)
        return self.visit(child1, child2, nineml_cls=child_type, **kwargs)

    def visit_children(self, children_type, parent1, parent2,
                       parent_cls=None, parent_result=None, **kwargs):  # @UnusedVariable @IgnorePep8
        results = []
        keys1 = set(parent1._member_keys_iter(children_type))
        keys2 = set(parent2._member_keys_iter(children_type))
        if keys1 != keys2:
            self._raise_keys_mismatch_exception(children_type, parent1,
                                                parent2)
        for key in keys1:
            child1 = parent1._member_accessor(children_type)(key)
            child2 = parent2._member_accessor(children_type)(key)
            results.append(self.visit(
                child1, child2, nineml_cls=children_type, **kwargs))
        return results

    def action(self, obj1, obj2, nineml_cls, **kwargs):
        try:
            method = getattr(self, 'action_' + nineml_cls.nineml_type.lower())
        except AttributeError:
            method = self.default_action
        return method(obj1, obj2, nineml_cls=nineml_cls, **kwargs)

    def default_action(self, obj1, obj2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_action' method
        """
        assert False, ("No default action provided, so can't action {} "
                       "({} & {})".format(nineml_cls, obj1, obj2))

    def _raise_type_exception(self, obj1, obj2):
        raise NineMLDualVisitException()

    def _raise_none_child_exception(self, child_name, child1, child2):
        raise NineMLDualVisitException()

    def _raise_keys_mismatch_exception(self, children_type, obj1, obj2):
        raise NineMLDualVisitException()


class DualWithContextMixin(object):

    def __init__(self):
        self.contexts1 = []
        self.contexts2 = []

    @property
    def context1(self):
        if self.contexts1:
            context = self.contexts1[-1]
        else:
            context = None
        return context

    @property
    def context2(self):
        if self.contexts2:
            context = self.contexts2[-1]
        else:
            context = None
        return context

    def context1_key(self, key):
        return tuple([c.parent for c in self.contexts1] + [key])

    def context2_key(self, key):
        return tuple([c.parent for c in self.contexts2] + [key])

    def visit_child(self, child_name, child_type, parent1, parent2,
                    parent_cls, parent_result, **kwargs):
        # Create the context around the visit of the attribute
        context1 = Context(parent1, parent_cls, parent_result, child_name,
                           None)
        context2 = Context(parent2, parent_cls, parent_result, child_name,
                           None)
        self.contexts1.append(context1)
        self.contexts2.append(context2)
        result = BaseDualVisitor.visit_child(
            self, child_name, child_type, parent1, parent2,
            parent_cls=parent_cls, parent_result=parent_result, **kwargs)
        popped1 = self.contexts1.pop()
        assert context1 is popped1
        popped2 = self.contexts2.pop()
        assert context2 is popped2
        return result

    def visit_children(self, children_type, parent1, parent2,
                       parent_cls, parent_result, **kwargs):
        try:
            dct1 = parent1._member_dict(children_type)
        except (NineMLInvalidElementTypeException, AttributeError):
            dct1 = None  # If children_type is a base class of the obj
        try:
            dct2 = parent2._member_dict(children_type)
        except (NineMLInvalidElementTypeException, AttributeError):
            dct2 = None  # If children_type is a base class of the obj
        context1 = Context(parent1, parent_cls, parent_result, None, dct1)
        context2 = Context(parent2, parent_cls, parent_result, None, dct2)
        self.contexts1.append(context1)
        self.contexts2.append(context2)
        results = BaseDualVisitor.visit_children(
            self, children_type, parent1, parent2, parent_cls, parent_result,
            **kwargs)
        popped1 = self.contexts1.pop()
        assert context1 is popped1
        popped2 = self.contexts2.pop()
        assert context2 is popped2
        return results


class BaseDualVisitorWithContext(DualWithContextMixin, BaseDualVisitor):

    pass
