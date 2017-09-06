from collections import defaultdict
from nineml.exceptions import (
    NineMLDualVisitTypeException,
    NineMLDualVisitKeysMismatchException,
    NineMLInvalidElementTypeException)


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

    visit_as_class = None

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
            self._children = defaultdict(dict)

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
            if (self.visit_as_class is not None and
                    isinstance(obj, self.visit_as_class)):
                nineml_cls = self.visit_as_class
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
            if (self.visit_as_class is not None and
                    isinstance(obj1, self.visit_as_class)):
                nineml_cls = self.visit_as_class
            else:
                nineml_cls = type(obj1)
        if (not isinstance(obj1, nineml_cls) or
                not isinstance(obj2, nineml_cls)):
            raise NineMLDualVisitTypeException(
                obj1, obj2, nineml_cls, self.contexts1, label=1)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        action_result = self.action(obj1, obj2, nineml_cls=nineml_cls,
                                    **kwargs)
        # Visit all the attributes of the object that are 9ML objects
        # themselves
        results = self.Results(action_result)
        # Add the container object to the list of scopes
        for child_name, child_type in nineml_cls.nineml_child.iteritems():
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
                continue
            elif child1 is None or child1 is None:
                raise NineMLDualVisitTypeException(
                    child1, child2, child_type, self.contexts1, label=1)
            results._child[child_name] = self.visit(
                child1, child2, nineml_cls=child_type, **kwargs)
            popped1 = self.contexts1.pop()
            assert context1 is popped1
            popped2 = self.contexts2.pop()
            assert context2 is popped2
        # Visit children of the object
        for children_type in nineml_cls.nineml_children:
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
                child1 = obj1.element(key, child_types=[children_type])
                child2 = obj2.element(key, child_types=[children_type])
                results._children[children_type][key] = self.visit(
                    child1, child2, nineml_cls=children_type, **kwargs)
            popped1 = self.contexts1.pop()
            assert context1 is popped1
            popped2 = self.contexts2.pop()
            assert context2 is popped2
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
