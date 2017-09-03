from collections import defaultdict
from nineml.exceptions import NineMLInvalidElementTypeException


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

    visits_class = None

    class Context(object):
        "The context within which the current element is situated"

        def __init__(self, parent, parent_cls, parent_result, attr_name=None,
                     dct=None):
            self._parent = parent
            self._parent_cls = parent_cls
            assert isinstance(parent, parent_cls)
            self._parent_result = parent_result
            self._attr_name = attr_name
            self._dct = dct

        @property
        def parent(self):
            return self._parent

        @property
        def parent_cls(self):
            return self._parent_cls

        @property
        def children_types(self):
            try:
                return self._parent_cls.children_types
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

        def __init__(self, action_result):
            self._action = action_result
            self._post_action = None
            self._attr = {}
            self._children = defaultdict(dict)

        @property
        def action(self):
            return self._action

        @property
        def post_action(self):
            return self._post_action

        @property
        def children(self):
            return self._children.itervalues()

        @property
        def child_names(self):
            return self._children.iterkeys()

        def attr_result(self, name):
            return self._attr[name]

        def child_result(self, child):
            return self._children[child.nineml_type][child.key]

        def child_results(self, child_type):
            return self._children[child_type].itervalues()

    def __init__(self):
        self.contexts = []

    def visit(self, obj, nineml_cls=None, **kwargs):
        # Use the class of the object to visit the object as if one is not
        # explicitly provided. This allows classes to be visited as if they
        # were base classes (e.g. Dynamics instead of MultiDynamics)
        if nineml_cls is None:
            if (self.visits_class is not None and
                    isinstance(obj, self.visits_class)):
                nineml_cls = self.visits_class
            else:
                nineml_cls = type(obj)
        # Run the 'action_<obj-nineml_type>' method on the visited object
        action_result = self.action(obj, nineml_cls=nineml_cls, **kwargs)
        # Visit all the attributes of the object that are 9ML objects
        # themselves
        results = self.Results(action_result)
        # Add the container object to the list of scopes
        for attr_name in obj.child_attrs:
            attr = getattr(obj, attr_name)
            if attr is None:
                continue
            # Create the context around the visit of the attribute
            context = self.Context(obj, nineml_cls, action_result, attr_name)
            self.contexts.append(context)
            results._attr[attr_name] = self.visit(attr, **kwargs)
            popped = self.contexts.pop()
            assert context is popped
        # Visit children of the object
        for child_type in nineml_cls.children_types:
            try:
                dct = obj._member_dict(child_type)
            except (NineMLInvalidElementTypeException, AttributeError):
                dct = None  # If child_type is from base class
            context = self.Context(obj, nineml_cls, action_result, dct=dct)
            self.contexts.append(context)
            for child in obj._members_iter(child_type):
                results._children[child_type][child.key] = self.visit(
                    child, nineml_cls=child_type, **kwargs)
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
        return method(obj, **kwargs)

    def post_action(self, obj, results, nineml_cls, **kwargs):
        try:
            method = getattr(self,
                             'post_action_' + nineml_cls.nineml_type.lower())
        except AttributeError:
            method = self.default_post_action
        return method(obj, results, **kwargs)

    @property
    def context(self):
        if self.contexts:
            context = self.contexts[-1]
        else:
            context = None
        return context

    def context_key(self, key):
        return tuple([c.parent for c in self.contexts] + [key])

    def default_action(self, obj, **kwargs):  # @UnusedVariable
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_action' method
        """
        assert False, ("No default action provided, so can't action {} ({})"
                       .format(obj.nineml_type, obj))

    def default_post_action(self, obj, results, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Default action performed on every object that doesn't define an
        explicit '<nineml-type-name>_post_action' method
        """
        return results
