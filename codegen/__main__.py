#!/usr/bin/env python3
"""
dbus-codegen: generate python classes from dbus introspection data.

Given an XML file of the format output by DBus introspection, codegen will
create python code describing a class for each interface node it finds in the
file. The classes inherit from python-dbus's service.Object class, and  have
all methods, properties, and signals described in the xml, complete with
type hints and the appropriate python-dbus decorators.

When invoked from the command line, codegen has two modes of operation: single-
and multi-file mode. In single-file mode, every class is concatenated to the
file given by --out, or stdout if nothing is specified. In multi-file mode,
enabled by giving the name of an output directory with --dir, each class gets
its own file. the file names are taken from the interface names of the given
interfaces, with any prefix common to all the interfaces stripped away.
"""

__author__ = "JET 2019-09"
from os import path

import stpl

from xmlnode import parse_file

_PACKAGEPATH, _ = path.split(__file__)
TMPLPATH = _PACKAGEPATH + path.sep + "templates"

TMPL = stpl.SimpleTemplate(name="class", lookup=[TMPLPATH])


def render_template(xmlfile):
    nodes = parse_file(xmlfile)
    content = {}
    for interface in nodes:
        code = TMPL.render(iface=interface)
        content[interface.name] = code

    return content


def write_to_dir(files, where):
    prefix = path.commonprefix(list(files.keys()))
    for name, contents in files.items():
        filename = name.replace(prefix, "").replace(".", "_").lower()
        fullname = where + path.sep + filename + ".py"
        with open(fullname, "w") as f:
            f.write(contents)


def main():
    import argparse
    from sys import stderr, stdin, stdout

    try:
        import black

        black_available = True
    except ImportError:
        black_available = False

    parser = argparse.ArgumentParser(description=__doc__, epilog=__author__)
    parser.add_argument(
        "src",
        nargs="*",
        type=argparse.FileType("r"),
        default=[stdin],
        help="xml file(s) to process (default stdin)",
    )
    parser.add_argument(
        "--out",
        type=argparse.FileType("w"),
        default=stdout,
        help="filename to write to in single-file mode (default stdout)",
    )
    parser.add_argument("--dir", help="directory to write to in multi-file mode")
    args = parser.parse_args()
    if args.dir and not (path.exists(args.dir) and path.isdir(args.dir)):
        print("%s: no such directory" % args.dir, file=stderr)
        return 1

    results = {}
    for f in args.src:
        results = {**results, **render_template(f)}

    if black_available:
        fm = black.FileMode()
        results = {k: black.format_str(v, mode=fm) for k, v in results.items()}

    if args.dir:
        write_to_dir(results, args.dir)
    else:
        filecontents = "\n\n".join(results.values())
        args.out.write(filecontents)


if __name__ == "__main__":
    exit(main() or 0)
