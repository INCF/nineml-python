from nineml.base import BaseNineMLVisitor


def clone_id(obj):
    """
    Used in storing cloned objects in 'memo' dictionary to avoid duplicate
    clones of the same object referenced from different points in a complex
    data tree. First looks for special method 'clone_id' and falls back on the
    'id' function that returns a memory-address based ID.

    Parameters
    ----------
    obj : object
        Any object
    """
    try:
        return obj.clone_id
    except AttributeError:
        return id(obj)


class Cloner(BaseNineMLVisitor):

    def clone(self, memo=None, **kwargs):
        """
        General purpose clone operation, which copies the attributes used
        to define equality between 9ML objects. Other attributes, such as
        the document the 9ML object belongs to are re-initialized. Use this
        in favour of Python's copy and deepcopy functions unless you know what
        you want (i.e. things are likely to break if you are not careful).

        Parameters
        ----------
        memo : dict
            A dictionary to hold copies of objects that have already been
            cloned to avoid issues with circular references
        exclude_annotations : bool
            Flags that annotations should be omitted from the clone
        """
        if memo is None:
            memo = {}
        try:
            # See if the attribute has already been cloned in memo
            clone = memo[clone_id(self)]
        except KeyError:
            clone = copy(self)  # Create a new object of the same type
            clone.__dict__ = {}  # Wipe it clean to start from scratch
            # Save the element in the memo to avoid it being cloned twice in
            # the object hierarchy. Due to possible recursion this needs to be
            # set before the '_copy_to_clone' method is called.
            memo[clone_id(self)] = clone
            # The actual setting of attributes is handled by _copy_to_clone is
            # used to allow sub classes to override it and control inheritance
            # from super classes
            self._copy_to_clone(clone, memo, **kwargs)
        return clone

    def _copy_to_clone(self, clone, memo, **kwargs):
        self._clone_defining_attr(clone, memo, **kwargs)

    def _clone_defining_attr(self, clone, memo, **kwargs):
        for attr_name in self.defining_attributes:
            setattr(clone, attr_name,
                    _clone_attr(getattr(self, attr_name), memo, **kwargs))


def _clone_attr(attr, memo, **kwargs):
    """Recursively clone an attribute"""
    if attr is None or isinstance(attr, (basestring, float, int, bool,
                                         sympy.Basic)):
        clone = attr  # "primitive" type that doesn't need to be cloned
    elif hasattr(attr, 'clone'):
        clone = attr.clone(memo=memo, **kwargs)
    elif isinstance(attr, defaultdict):
        clone = type(attr)(attr.default_factory,
                            ((k, _clone_attr(v, memo, **kwargs))
                             for k, v in attr.iteritems()))
    elif isinstance(attr, dict):
        clone = type(attr)((k, _clone_attr(v, memo, **kwargs))
                           for k, v in attr.iteritems())
    elif isinstance(attr, Iterable):
        try:
            assert not isinstance(attr, Iterator)
        except:
            raise
        clone = attr.__class__(_clone_attr(a, memo, **kwargs)
                               for a in attr)
    else:
        assert False, "Unhandled attribute type {} ({})".format(type(attr),
                                                                attr)
    return clone