dbus-codegen
============

Generate Python code from DBus introspection data.

*JET 2019-09*

Description
-----------

Dbus-codegen is a small command line tool that parses the DBus Introspection XML
format and uses it to generate Python classes. The resulting classes will generate
the same XML output when their `Introspect` method is called. The classes inherit
from python-dbus's `service.Object` class, and have all methods, properties, and
signals described in the XML, complete with type hints and the appropriate 
python-dbus decorators.

When invoked from the command line, codegen has two modes of operation: single-
and multi-file mode. In single-file mode, every class is concatenated to the
file given by `--out`, or stdout if nothing is specified. In multi-file mode,
enabled by giving the name of an output directory with `--dir`, each class gets
its own file. The file names are taken from the interface names of the given
interfaces, with any prefix common to all the interfaces stripped away.

Requirements
------------

* Python 3.5+
* SimpleTemplate (stpl)
* python-dbus

...and optionally, the Black code formatter.

Usage
-----

### Command line

	python3 codegen [-h] [--out OUT] [--dir DIR] [src [src ...]]


#### Positional arguments

    src         xml file(s) to process (default stdin)

#### Optional arguments

    -h, --help  show this help message and exit
    --out OUT   filename to write to in single-file mode (default stdout)
    --dir DIR   directory to write to in multi-file mode
