from collections import OrderedDict, namedtuple
from nineml.exceptions import (
    NineMLDualVisitTypeException,
    NineMLDualVisitKeysMismatchException,
    NineMLInvalidElementTypeException,
    NineMLDualVisitNoneChildException,
    NineMLDualVisitException)


class OrderedDefaultOrderedDictDict(OrderedDict):

    def __missing__(self, key):
        self[key] = value = OrderedDict()
        return value

Context = namedtuple('Context', ('parent', 'parent_cls', 'parent_result',
                                 'attr_name', 'dct'))


class BaseVisitor2(object):
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
        result = self.action(obj, nineml_cls=nineml_cls, **kwargs)
        # Add the container object to the list of scopes
        for child_name, child_type in nineml_cls.nineml_child.iteritems():
            self.visit_child(child_name, child_type, obj,
                             nineml_cls, result, **kwargs)
        # Visit children of the object
        for children_type in nineml_cls.nineml_children:
            self.visit_children(children_type, obj, nineml_cls, result,
                                **kwargs)
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


class BaseChildResultsVisitor(BaseVisitor2):
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
        for child_name, child_type in nineml_cls.nineml_child.iteritems():
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
        context = self.Context(parent, parent_cls, parent_result, child_name,
                               None)
        self.contexts.append(context)
        result = BaseVisitor2.visit_child(
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
        context = self.Context(parent, parent_cls, parent_result, None, dct)
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

    def context_key(self, key):
        return tuple([c.parent for c in self.contexts] + [key])


class BaseDualVisitor2(BaseVisitor2):
    """
    Generic visitor base class that visits two 9ML objects side-by-side
    """

    def visit(self, obj1, obj2, nineml_cls=None, **kwargs):
        # Use the class of the object to visit the object as if one is not
        # explicitly provided. This allows classes to be visited as if they
        # were base classes (e.g. Dynamics instead of MultiDynamics)
        nineml_cls = self._get_nineml_cls(obj1, obj2, nineml_cls)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        result = self.action(obj1, obj2, nineml_cls=nineml_cls, **kwargs)
        # Add the container object to the list of scopes
        for child_name, child_type in nineml_cls.nineml_child.iteritems():
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
        result = BaseDualVisitor2.visit_child(
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
        results = BaseDualVisitor2.visit_children(
            self, children_type, parent1, parent2, parent_cls, parent_result,
            **kwargs)
        popped1 = self.contexts1.pop()
        assert context1 is popped1
        popped2 = self.contexts2.pop()
        assert context2 is popped2
        return results


class BaseVisitor(object):
    """
    Generic visitor base class that visits a 9ML object and all children (and
    children's children etc...) and calls 'action_<nineml-type>' and
    'post_action_<nineml-type>'. These methods are not implemented in this
    base class but can be overridden in derived classes that wish to perform
    an action on specific element types.

    For example to perform an action on all units (and nothing else) in the
    object a derived class can be written as

    class UnitVisitor(Visitor):

        def action_unit(unit, **kwargs):
            # Do action here

    """

    as_class = None

    class Context(object):
        "The context within which the current element is situated"

        def __init__(self, parent, parent_cls, parent_result, attr_name=None,
                     dct=None):
            self._parent = parent
            self._parent_cls = parent_cls
            try:
                assert isinstance(parent, parent_cls)
            except:
                raise
            self._parent_result = parent_result
            self._attr_name = attr_name
            self._dct = dct

        @property
        def parent(self):
            return self._parent

        def __repr__(self):
            return ("Context(parent={}, parent_cls={}, parent_result={}, "
                    "attr_name={}, dct={}".format(self.parent, self.parent_cls,
                                                  self.parent_result,
                                                  self.attr_name,
                                                  self.dct))

        @property
        def parent_cls(self):
            return self._parent_cls

        @property
        def nineml_children(self):
            try:
                return self._parent_cls.nineml_children
            except AttributeError:
                return None

        @property
        def parent_result(self):
            return self._parent_result

        @property
        def attr_name(self):
            return self._attr_name

        @property
        def dct(self):
            return self._dct

        def replace(self, old, new):
            if self.attr_name is not None:
                setattr(self.parent, '_' + self.attr_name, new)
            elif self.dct is not None:
                del self.dct[old.name]
                self.dct[new.name] = new

    class Results(object):

        def __init__(self, action_result, post_action=None):
            self._action = action_result
            self._post_action = post_action
            self._child = {}
            self._children = OrderedDefaultOrderedDictDict()

        @property
        def action(self):
            return self._action

        @property
        def post_action(self):
            return self._post_action

        @post_action.setter
        def post_action(self, post_action):
            self._post_action = post_action

        def child_result(self, name):
            return self._child[name]

        def children_results(self, child_type):
            return self._children[child_type].itervalues()

        @property
        def children_types(self):
            return self._children.iterkeys()

    def __init__(self):
        self.contexts = []

    def visit(self, obj, nineml_cls=None, **kwargs):
        # Use the class of the object to visit the object as if one is not
        # explicitly provided. This allows classes to be visited as if they
        # were base classes (e.g. Dynamics instead of MultiDynamics)
        if nineml_cls is None:
            if (self.as_class is not None and
                    isinstance(obj, self.as_class)):
                nineml_cls = self.as_class
            else:
                nineml_cls = type(obj)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        action_result = self.action(obj, nineml_cls=nineml_cls, **kwargs)
        # Visit all the attributes of the object that are 9ML objects
        # themselves
        results = self.Results(action_result)
        # Add the container object to the list of scopes
        for child_name, child_type in nineml_cls.nineml_child.iteritems():
            child = getattr(obj, child_name)
            if child is None:
                continue
            # Create the context around the visit of the attribute
            context = self.Context(obj, nineml_cls, action_result, child_name)
            self.contexts.append(context)
            results._child[child_name] = self.visit(
                child, nineml_cls=child_type, **kwargs)
            popped = self.contexts.pop()
            assert context is popped
        # Visit children of the object
        for children_type in nineml_cls.nineml_children:
            try:
                dct = obj._member_dict(children_type)
            except (NineMLInvalidElementTypeException, AttributeError):
                dct = None  # If children_type is a base class of the obj
            context = self.Context(obj, nineml_cls, action_result, dct=dct)
            self.contexts.append(context)
            for child in obj._members_iter(children_type):
                results._children[children_type][child.key] = self.visit(
                    child, nineml_cls=children_type, **kwargs)
            popped = self.contexts.pop()
            assert context is popped
        # Peform "post-action" method that runs after the children/attributes
        # have been visited
        self.post_action(obj, results, nineml_cls=nineml_cls, **kwargs)
        return results

    def action(self, obj, nineml_cls, **kwargs):
        try:
            method = getattr(self, 'action_' + nineml_cls.nineml_type.lower())
        except AttributeError:
            method = self.default_action
        return method(obj, nineml_cls=nineml_cls, **kwargs)

    def post_action(self, obj, results, nineml_cls, **kwargs):
        try:
            method = getattr(self,
                             'post_action_' + nineml_cls.nineml_type.lower())
        except AttributeError:
            method = self.default_post_action
        return method(obj, results, nineml_cls=nineml_cls, **kwargs)

    @property
    def context(self):
        if self.contexts:
            context = self.contexts[-1]
        else:
            context = None
        return context

    def context_key(self, key):
        return tuple([c.parent for c in self.contexts] + [key])

    def default_action(self, obj, nineml_cls, **kwargs):  # @UnusedVariable
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_action' method
        """
        assert False, ("No default action provided, so can't action {} ({})"
                       .format(nineml_cls, obj))

    def default_post_action(self, obj, results, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_post_action' method
        """
        return results


class BaseDualVisitor(BaseVisitor):
    """
    Generic visitor base class that visits two 9ML objects side-by-side
    """

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

    def visit(self, obj1, obj2, nineml_cls=None, **kwargs):
        # Use the class of the object to visit the object as if one is not
        # explicitly provided. This allows classes to be visited as if they
        # were base classes (e.g. Dynamics instead of MultiDynamics)
        if nineml_cls is None:
            if (self.as_class is not None and
                    isinstance(obj1, self.as_class)):
                nineml_cls = self.as_class
            else:
                if isinstance(obj2, type(obj1)):
                    nineml_cls = type(obj1)
                elif isinstance(obj1, type(obj2)):
                    nineml_cls = type(obj2)
                else:
                    raise NineMLDualVisitTypeException(
                        nineml_cls, obj1, obj2, self.contexts1, self.contexts2)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        action_result = self.action(obj1, obj2, nineml_cls=nineml_cls,
                                    **kwargs)
        # Visit all the attributes of the object that are 9ML objects
        # themselves
        results = self.Results(action_result)
        # Add the container object to the list of scopes
        for child_name, child_type in nineml_cls.nineml_child.iteritems():
            self._compare_child(obj1, obj2, nineml_cls, results, action_result,
                                child_name, child_type, **kwargs)
        # Visit children of the object
        for children_type in nineml_cls.nineml_children:
            self._compare_children(obj1, obj2, nineml_cls, results,
                                   action_result, children_type, **kwargs)
        # Peform "post-action" method that runs after the children/attributes
        # have been visited
        self.post_action(obj1, obj2, results, nineml_cls=nineml_cls, **kwargs)
        return results

    def action(self, obj1, obj2, nineml_cls, **kwargs):
        try:
            method = getattr(self, 'action_' + nineml_cls.nineml_type.lower())
        except AttributeError:
            method = self.default_action
        return method(obj1, obj2, nineml_cls=nineml_cls, **kwargs)

    def post_action(self, obj1, obj2, results, nineml_cls, **kwargs):
        try:
            method = getattr(self,
                             'post_action_' + nineml_cls.nineml_type.lower())
        except AttributeError:
            method = self.default_post_action
        return method(obj1, obj2, results, nineml_cls=nineml_cls, **kwargs)

    def default_action(self, obj1, obj2, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_action' method
        """
        assert False, ("No default action provided, so can't action {} "
                       "({} & {})".format(nineml_cls, obj1, obj2))

    def default_post_action(self, obj1, obj2, results, nineml_cls, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_post_action' method
        """
        return results

    def _compare_child(self, obj1, obj2, nineml_cls, results, action_result,
                       child_name, child_type, **kwargs):
        child1 = getattr(obj1, child_name)
        child2 = getattr(obj2, child_name)
        # Create the context around the visit of the attribute
        context1 = self.Context(obj1, nineml_cls, action_result,
                                child_name)
        context2 = self.Context(obj2, nineml_cls, action_result,
                                child_name)
        self.contexts1.append(context1)
        self.contexts2.append(context2)
        if child1 is None and child2 is None:
            self.contexts1.pop()
            self.contexts2.pop()
            return  # Both children are None so return
        elif child1 is None or child1 is None:
            raise NineMLDualVisitNoneChildException(
                child1, child2, child_type, self.contexts1, label=1)
        results._child[child_name] = self.visit(
            child1, child2, nineml_cls=child_type, **kwargs)
        popped1 = self.contexts1.pop()
        assert context1 is popped1
        popped2 = self.contexts2.pop()
        assert context2 is popped2

    def _compare_children(self, obj1, obj2, nineml_cls, results, action_result,
                          children_type, **kwargs):
        try:
            dct1 = obj1._member_dict(children_type)
        except (NineMLInvalidElementTypeException, AttributeError):
            dct1 = None  # If children_type is a base class of the obj
        try:
            dct2 = obj2._member_dict(children_type)
        except (NineMLInvalidElementTypeException, AttributeError):
            dct2 = None  # If children_type is a base class of the obj
        context1 = self.Context(obj1, nineml_cls, action_result, dct=dct1)
        context2 = self.Context(obj2, nineml_cls, action_result, dct=dct2)
        self.contexts1.append(context1)
        self.contexts2.append(context2)
        keys1 = set(obj1._member_keys_iter(children_type))
        keys2 = set(obj2._member_keys_iter(children_type))
        if keys1 != keys2:
            raise NineMLDualVisitKeysMismatchException(
                children_type, obj1, obj2, self.contexts1, self.contexts2)
        for key in keys1:
            try:
                child1 = obj1._member_accessor(children_type)(key)
                child2 = obj2._member_accessor(children_type)(key)
            except:
                obj1._member_accessor(children_type)(key)
                obj2._member_accessor(children_type)(key)
                raise
            results._children[children_type][key] = self.visit(
                child1, child2, nineml_cls=children_type, **kwargs)
        popped1 = self.contexts1.pop()
        assert context1 is popped1
        popped2 = self.contexts2.pop()
        assert context2 is popped2
