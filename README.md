dbus-codegen
============

Usage:

	python3 codegen [-h] [--out OUT] [--dir DIR] [--fmt] [src [src ...]]

Given an XML file of the format output by DBus introspection, codegen will
create python code describing a class for each interface node it finds in the
file. The classes inherit from python-dbus's service.Object class, and have all
methods, properties, and signals described in the xml, complete with type hints
and the appropriate python-dbus decorators.

When invoked from the command line, codegen has two modes of operation: single-
and multi-file mode. In single-file mode, every class is concatenated to the
file given by --out, or stdout if nothing is specified. In multi-file mode,
enabled by giving the name of an output directory with --dir, each class gets
its own file. The file names are taken from the interface names of the given
interfaces, with any prefix common to all the interfaces stripped away.

positional arguments:

  src         xml file(s) to process (default stdin)

optional arguments:

    -h, --help  show this help message and exit
    --out OUT   filename to write to in single-file mode (default stdout)
    --dir DIR   directory to write to in multi-file mode
    --fmt       format output (requires black)

JET 2019-09




