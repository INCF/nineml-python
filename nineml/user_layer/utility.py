from .base import BaseULObject, NINEML


def check_tag(element, cls):
    assert element.tag in (cls.element_name, NINEML + cls.element_name), \
                  "Found <%s>, expected <%s>" % (element.tag, cls.element_name)


def walk(obj, visitor=None, depth=0):
    if visitor:
        visitor.depth = depth
    if isinstance(obj, BaseULObject):
        obj.accept_visitor(visitor)
    if hasattr(obj, "get_children"):
        get_children = obj.get_children
    else:
        get_children = obj.itervalues
    for child in sorted(get_children()):
        walk(child, visitor, depth + 1)


class ExampleVisitor(object):

    def visit(self, obj):
        print " " * self.depth + str(obj)


class Collector(object):

    def __init__(self):
        self.objects = []

    def visit(self, obj):
        self.objects.append(obj)


def flatten(obj):
    collector = Collector()
    walk(obj, collector)
    return collector.objects


def check_units(units, dimension):
    # primitive unit checking, should really use Pint, Quantities or Mike
    # Hull's tools
    if not dimension:
        raise ValueError("dimension not specified")
    base_units = {
        "voltage": "V",
        "current": "A",
        "conductance": "S",
        "capacitance": "F",
        "time": "s",
        "frequency": "Hz",
        "dimensionless": "",
    }
    if len(units) == 1:
        prefix = ""
        base = units
    else:
        prefix = units[0]
        base = units[1:]
    if base != base_units[dimension]:
        raise ValueError("Units %s are invalid for dimension %s" %
                         (units, dimension))
