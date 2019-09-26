"""
dbus_codegen contains classes and methods for parsing dbus introspection data
into python structures.

2019-08 JET
"""

from types import FunctionType
from typing import Any, Callable, Dict, List, Tuple

import dbus
import dbus.service

from . import xmlnode
from .exceptions import UnknownInterface, UnknownProperty

UNNAMED_NODE = "<unnamed>"


def create_mock(interface: xmlnode.Interface) -> Any:
    "given an Interface, creates a dbus object."

    classname = interface.name.split(".")[-1]
    attributes = {"interface_name": interface.interface_name}
    for method in interface.methods:
        attributes[method.name] = create_method(method)

    for signal in interface.signals:
        attributes[signal.name] = create_signal(signal)

    if interface.properties:
        attributes.update(create_property_functions())
        attributes["properties"] = {p.name: p for p in interface.properties}

    return type(classname, (dbus.service.Object,), attributes)


def create_dbus_function(method: xmlnode.Method) -> Callable:
    """Given a Method node, creates a function stub with the correct arguments
    and return value(s).
    """

    # Build a list of in- and out-parameters.
    args = ["self"]
    retargs = []
    unnamed_arg_name = ord("a")
    for arg in method.args:
        if arg.direction == "out":
            retargs.append(repr(arg.value))
            continue

        name = arg.name
        if name == UNNAMED_NODE:
            # unnamed args are given one-letter names
            name = chr(unnamed_arg_name)
            unnamed_arg_name += 1
        args.append(name)

    func = __create_function(
        method.name,
        ", ".join(args),
        "return %s" % (", ".join(retargs) or "None"),
        global_env={"dbus": dbus},  # retargs use dbus types
        sourcefile=method.interface_name + ".xml",
    )

    return func


def __create_function(
    name: str,
    args: List[str],
    body: List[str],
    global_env: Dict[str, Any] = None,
    sourcefile: str = "<string>",
) -> Callable:
    """creates a function with the given name, argument list, and body.
    This function is DANGEROUS, as it performs NO CHECKING OR SANITIZATION.
    FOR INTERNAL USE ONLY."""

    code = compile(
        "def {name}({args}):\n    {body}".format(name=name, args=args, body=body),
        sourcefile,
        "exec",
    )

    func = FunctionType(code.co_consts[0], global_env or {})
    return func


def create_method(method: xmlnode.Method) -> Callable:
    """Wraps a generated method stub in a dbus method decorator, which
    publishes it onto the bus."""
    func = create_dbus_function(method)

    annotation = dbus.service.method(
        dbus_interface=method.interface_name,
        in_signature=method.signature("in"),
        out_signature=method.signature("out"),
    )
    return annotation(func)


def create_signal(signal: xmlnode.Signal) -> Callable:
    """As create_method, but with a signal; the returned method will signal any
    subscribers when called."""
    func = create_dbus_function(signal)
    annotation = dbus.service.signal(
        dbus_interface=signal.interface_name, signature=signal.signature()
    )
    return annotation(func)


def create_property_functions():
    """Methods for accessing named properties on an object through dbus.
    Separated to their own function for ease of gluing into a runtime-created
    class pre-construction"""

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface_name):
        if interface_name in (self.interface_name, ""):
            return {k: p.value for k, p in self.properties.items() if p.read}
        raise UnknownInterface(self.interface_name, interface_name)

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature="ss", out_signature="v")
    def Get(self, interface_name, property_name):
        try:
            return self.GetAll(interface_name)[property_name]
        except KeyError:
            raise UnknownProperty(self.interface_name, property_name, "read")

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature="ssv")
    def Set(self, interface_name, property_name, property_value):
        if interface_name in (self.interface_name, ""):

            if (
                property_name not in self.properties
                or not self.properties[property_name].write
            ):
                raise UnknownProperty(self.interface_name, property_name, "write")

            self.properties[property_name].value = property_value
            self.PropertiesChanged(
                interface_name, property_name, {property_name: property_value}, []
            )
        raise UnknownInterface(self.interface_name, interface_name)

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature="sa{sv}as")
    def PropertiesChanged(
        self, interface_name, changed_properties, invalidated_properties
    ):
        pass

    return {
        "GetAll": GetAll,
        "Get": Get,
        "Set": Set,
        "PropertiesChanged": PropertiesChanged,
    }
