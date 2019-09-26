"""
dbus_codegen contains classes and methods for parsing dbus introspection data
into python structures.

2019-08 JET
"""

import xml.etree.ElementTree as etree

import typestring

UNNAMED_NODE = "<unnamed>"


def parse(cls, tree):
    "Bootstrapping function for creating the root in a tree of Nodes"
    return [cls(node) for node in tree.findall(cls.nodename())]


def indent(string, prefix):
    "prefix each line in string"
    strings = string.splitlines(keepends=True)
    return "".join(prefix + s for s in strings)


class Node:
    "Base class for dbus introspection xml tree."

    def __init__(self, xmlnode, parent=None):
        self.name = xmlnode.attrib.get("name", UNNAMED_NODE)
        self.parent = parent
        self.interface_name = self.getroot().name
        self.annotations = self.parse(xmlnode, Annotation)
        self.args = self.parse(xmlnode, Arg)
        self.interfaces = self.parse(xmlnode, Interface)
        self.methods = self.parse(xmlnode, Method)
        self.properties = self.parse(xmlnode, Property)
        self.signals = self.parse(xmlnode, Signal)

    def __str__(self):
        header = "%s %s\n" % (self.nodename(), self.name)
        subheader = "  %s: %s\n"
        fields = header

        for key, value in self.__dict__.items():
            if key in ("name", "parent") or key.startswith("_") or callable(value):
                continue
            if isinstance(value, list):
                for val in value:
                    fields += indent(str(val), "  ")
            elif value:
                fields += subheader % (key, value)
        return fields

    @classmethod
    def nodename(cls):
        "Returns the name of the class, for matching against xml tags."
        return cls.__name__.lower()

    def parse(self, node, cls):
        """Given an xml tree node and a class named after a specific tag, returns
        an initialized object for each direct child tag of that kind in node."""
        out = []
        for tag in node.findall(cls.nodename()):
            instance = cls(tag, parent=self)
            out.append(instance)
        return out

    def getroot(self):
        "get root of tree"
        if self.parent is None:
            return self
        return self.parent.getroot()


class Interface(Node):
    "A representation of a DBus interface."


class Method(Node):
    "A representation of a DBus method."

    def signature(self, direction="in"):
        "get the dbus type signature for this method"
        return "".join(a.type for a in self.args if a.direction == direction)

    def argstr(self, direction="in"):
        "makes a type-hinted string of arguments, or a string of types"
        args = self.signature(direction=direction)
        names = (arg.name for arg in self.args)
        types = typestring.typehint(args)
        if direction == "out":
            return "(%s)" % ", ".join(types)
        out = ", ".join("{}: {}".format(n, t) for n, t in zip(names, types))
        if out:
            return "self, " + out
        return "self"

    def valstr(self, direction="in"):
        "makes a string of the default values for each arg"
        args = self.signature(direction)
        return "(%s)" % ", ".join(repr(n) for n in typestring.instantiate(args))


class Signal(Method):
    "A representation of a DBus signal."

    def signature(self, direction="in"):
        return super().signature()


class Arg(Node):
    "A representation of a DBus method argument."

    def __init__(self, xmlnode, *args, **kwargs):
        super().__init__(xmlnode, *args, **kwargs)
        self.type = xmlnode.attrib["type"]
        self.direction = xmlnode.attrib.get("direction", "in")


class Annotation(Node):
    "A representation of a DBus annotation."

    def __init__(self, xmlnode, *args, **kwargs):
        super().__init__(xmlnode, *args, **kwargs)
        self.value = xmlnode.attrib["value"]


class Property(Node):
    "A representation of a DBus property."

    def __init__(self, xmlnode, *args, **kwargs):
        super().__init__(xmlnode, *args, **kwargs)
        self.type = xmlnode.attrib["type"]
        self.pytype = typestring.typehint(self.type)[0]
        self.value = typestring.instantiate(self.type)[0]
        self.access = xmlnode.attrib["access"]
        self.read = "read" in self.access
        self.write = "write" in self.access


def parse_file(xml):
    "Given the introspection file xml, creates a list of Interfaces."
    tree = etree.parse(xml)
    root = tree.getroot()
    return parse(Interface, root)
