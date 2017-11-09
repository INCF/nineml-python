"""
Exceptions specific to the 9ML library

:copyright: Copyright 2010-2017 by the NineML Python team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
import re


class NineMLException(Exception):
    pass


class NineMLUsageError(NineMLException):
    pass


class NineMLDimensionError(NineMLUsageError):
    pass


class NineMLMathParseError(ValueError, NineMLUsageError):
    pass


class NineMLUnitMismatchError(ValueError, NineMLUsageError):
    pass


class NineMLNameError(KeyError, NineMLUsageError):
    pass


class NineMLValueError(ValueError, NineMLUsageError):
    pass


class NineMLTypeError(TypeError, NineMLUsageError):
    pass


class NineMLInvalidElementTypeException(TypeError, NineMLUsageError):
    pass


class NineMLImmutableError(NineMLUsageError):
    pass


class NineMLTargetMissingError(NineMLUsageError):
    pass


class NineMLXMLError(NineMLUsageError):
    pass


class NineMLSerializationError(NineMLUsageError):
    pass


class NineMLSerializerNotImportedError(NineMLSerializationError):
    pass


class NineMLMissingSerializationError(NineMLSerializationError):
    pass


class NineMLSerializationNotSupportedError(NineMLUsageError):
    pass


class NineMLUnexpectedMultipleSerializationError(NineMLSerializationError):
    pass


class NineMLAnnotationsError(NineMLUsageError):
    pass


class NineMLXMLTagError(NineMLXMLError):
    pass


class NineMLXMLAttributeError(NineMLXMLError):
    pass


class NineMLXMLBlockError(NineMLXMLError):
    pass


class NineMLNoSolutionException(NineMLException):
    pass


class NineMLIOError(NineMLUsageError):
    pass


class NineMLReloadDocumentException(NineMLException):
    pass


class NineMLStopVisitException(NineMLException):
    pass


class NineMLDontVisitChildrenException(NineMLException):

    def __init__(self, result=None):
        self.result = result


class NineMLDuplicateObjectError(NineMLStopVisitException):

    def __init__(self, obj, context1, context2):
        self.object = obj
        self.context1 = context1
        self.context2 = context2

    def __str__(self):
        return ("{} found twice in object hierarchy:\n{}\n{}"
                .format(self.object, format_context(self.context1),
                        format_context(self.context2)))


class NineMLFoundElementException(NineMLStopVisitException):

    def __init__(self, obj, context):
        self.object = obj
        self.context = context


class NineMLRandomDistributionDelayException(NineMLException):
    pass


class NineMLNotBoundException(NineMLException):
    """
    Raised when trying to access an attribute that hasn't been bound to the
    object"""
    pass


class NineMLDualVisitException(NineMLException):
    pass


class NineMLDualVisitTypeException(NineMLDualVisitException):

    def __init__(self, obj1, obj2, contexts1, contexts2):
        self.obj1 = obj1
        self.obj2 = obj2
        self.contexts1 = tuple(contexts1)
        self.contexts2 = tuple(contexts2)

    def __str__(self):
        return ("{} - types: [{}({})] | [{}({})]"
                .format(format_contexts(self.contexts1, self.contexts2),
                        self.obj1.nineml_type, type(self.obj1),
                        self.obj2.nineml_type, type(self.obj2)))


class NineMLDualVisitNoneChildException(NineMLDualVisitException):

    def __init__(self, child_name, obj1, obj2, contexts1, contexts2):
        self.child_name = child_name
        self.obj1 = obj1
        self.obj2 = obj2
        self.contexts1 = tuple(contexts1)
        self.contexts2 = tuple(contexts2)

    def __str__(self):
        return ("{} - '{}' child: [{}] | [{}]"
                .format(format_contexts(self.contexts1, self.contexts2),
                        self.child_name, self.obj1, self.obj2))


class NineMLDualVisitValueException(NineMLDualVisitException):

    def __init__(self, attr_name, obj1, obj2, nineml_cls, contexts1,
                 contexts2):
        self.attr_name = attr_name
        self.obj1 = obj1
        self.obj2 = obj2
        self.nineml_cls = nineml_cls
        self.contexts1 = tuple(contexts1)
        self.contexts2 = tuple(contexts2)

    def __str__(self):
        return ("{} - '{}' attr: [{}] | [{}]"
                .format(format_contexts(self.contexts1, self.contexts2,
                                              obj1=self.obj1, obj2=self.obj2),
                        self.attr_name,
                        getattr(self.obj1, self.attr_name),
                        getattr(self.obj2, self.attr_name)))


class NineMLDualVisitKeysMismatchException(NineMLDualVisitException):

    def __init__(self, children_type, obj1, obj2, contexts1, contexts2):
        self.children_type = children_type
        self.obj1 = obj1
        self.obj2 = obj2
        self.contexts1 = tuple(contexts1)
        self.contexts2 = tuple(contexts2)

    def __str__(self):
        return ("{} - {} keys: {} | {}"
                .format(format_contexts(self.contexts1, self.contexts2),
                        self.children_type.nineml_type,
                        sorted(self.obj1._member_keys_iter(
                               self.children_type), key=lambda k: str(k)),
                        sorted(self.obj2._member_keys_iter(
                               self.children_type), key=lambda k: str(k))))


class NineMLDualVisitAnnotationsMismatchException(NineMLDualVisitException):

    def __init__(self, children_type, obj1, obj2, key, contexts1,
                 contexts2):
        self.children_type = children_type
        self.obj1 = obj1
        self.obj2 = obj2
        self.key = key
        self.contexts1 = tuple(contexts1)
        self.contexts2 = tuple(contexts2)

    def __str__(self):
        return ("{} - '{}' annotations: [{}] | [{}]"
                .format(format_contexts(self.contexts1, self.contexts2),
                        self.key,
                        ', '.join(re.sub('\s', '', str(a))
                                  for a in self.obj1.annotations.namespace(
                                      self.key[1])),
                        ', '.join(re.sub('\s', '', str(a))
                                  for a in self.obj2.annotations.namespace(
                                      self.key[1]))))


def format_context(contexts, obj=None):
    l = [(type(c.parent).__name__, c.parent.key) for c in contexts]
    if obj is not None:
        l.append((type(obj).__name__, obj.key))
    return '[' + '>'.join("{}('{}')".format(t, k) for t, k in l) + ']'


def format_contexts(contexts1, contexts2, obj1=None, obj2=None):
    l1 = [(type(c.parent).__name__, c.parent.key) for c in contexts1]
    l2 = [(type(c.parent).__name__, c.parent.key) for c in contexts2]
    if obj1 is not None:
        l1.append((type(obj1).__name__, obj1.key))
    if obj2 is not None:
        l2.append((type(obj2).__name__, obj2.key))
    out = '[' + '>'.join("{}('{}')".format(t, k) for t, k in l1) + ']'
    if l2 != l1:
        out += (' | [' + '>'.join("{}('{}')".format(t, k) for t, k in l2) +
                ']')
    return out


def internal_error(s):
    assert False, 'INTERNAL ERROR:' + s


def name_error(accessor):
    def accessor_with_handling(self, name):
        try:
            return accessor(self, name)
        except KeyError:
            # Get the name of the element type to be accessed making use of a
            # strict naming convention of the accessors
            type_name = ''.join(p.capitalize()
                                for p in accessor.__name__.split('_'))
            try:
                available = getattr(self, accessor.__name__ + '_names')
            except AttributeError:
                available = []
            raise NineMLNameError(
                "'{}' {} does not have {} named '{}' ('{}')"
                .format(self.key, self.nineml_type, type_name, name,
                        "', '".join(available)))
    return accessor_with_handling
