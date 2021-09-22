#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import sys
import argparse
from moosetools import parameters
from moosetools import moosetree
from moosetools import pyhit
from moosetools import factory
from moosetools import core
from moosetools import mooseutils

# These imports are needed so the various Factory objects register the locally available objects
from moosetools.moosetest import base
from moosetools.moosetest import formatters, controllers


def cli_args():
    """
    Create the ArgumentParser object from the `TestHarness` base object.

    The only argument used within the `main` function is the --config option. This is done to get
    the config file, from which the various objects are created. This includes the `TestHarness`
    object which can have additional command line arguments if it has been customized.
    """
    parser = argparse.ArgumentParser(description="Testing system inspired by MOOSE", add_help=False)
    parser.add_argument('--config', default=os.getcwd(), type=str,
                        help="A configuration file or directory. If a directory is provided a " \
                        "'.moosetest' file is searched up the directory tree beginning with " \
                        "the current working directory.")
    known, _ = parser.parse_known_args()  # don't error on custom options

    return known


def main():
    """
    Complete function for automatically detecting and performing tests based on test specifications.

    This function exists for the use by the `moosetest` executable in the bin directory of the
    moosetools repository.
    """
    # Locate/load configuration
    args = cli_args()
    filename = _locate_config(args.config)
    root = _load_config(filename)

    # Setup the environment variables from top-level parameters of HIT configuration file file
    _setup_environment(filename, root)

    # Create the Controller, Formatter, and TestHarness objects
    controllers = _make_controllers(filename, root)
    formatter = _make_formatter(filename, root)
    object_defaults = _get_object_defaults(filename, root)
    harness = _make_harness(filename, root, controllers, formatter, object_defaults)

    # Execute the tests
    harness.parse()
    if harness.status():
        msg = "An unexpected error occurred when calling the `TestHarness.parse` method."
        raise RuntimeError(msg)

    groups = harness.discover()
    if harness.status():
        msg = "An unexpected error occurred when calling the `TestHarness.discover` method."
        raise RuntimeError(msg)

    rcode = harness.run(groups)
    if harness.status():
        msg = "An unexpected error occurred when calling the `TestHarness.run` method."
        raise RuntimeError(msg)

    return rcode


def _make_harness(filename, root, controllers, formatter, object_defaults):
    """
    Create the `TestHarness` object from the [TestHarness] block of the `pyhit.Node` of *root*.

    The *filename* is provided for error reporting and setting the current working directory for
    creating object defined in the configuration file. It should be the file used for generating
    the tree structure in *root*.

    The *controllers*, *formatter*, and *object_defaults* are applied to the created `TestHarness`
    object via the parameters by the same name.
    """
    # Top-level parameters are used to build the TestHarness object. Creating custom `TestHarness`
    # objects is not-supported, so don't allow "type" to be set.
    h_node = moosetree.find(root, func=lambda n: n.fullpath == '/TestHarness')
    if h_node is None:
        h_node = root.append('TestHarness', type='TestHarness')

    # Build a factory capable of creating the TestHarness object
    working_dir = os.path.dirname(filename) if filename is not None else os.getcwd()
    with mooseutils.CurrentWorkingDirectory(working_dir):
        plugin_dirs = [
            os.path.abspath(mooseutils.eval_path(path))
            for path in os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split()
        ]
    h_factory = factory.Factory(plugin_dirs=tuple(plugin_dirs), plugin_types=(base.TestHarness, ))
    h_factory.load()
    if h_factory.status() > 0:
        msg = "An error occurred during registration of the TestHarness type, see console message(s) for details."
        raise RuntimeError(msg)

    # Use the Parser is used to correctly convert HIT to InputParameters
    p = factory.Parser(h_factory)
    with mooseutils.CurrentWorkingDirectory(working_dir):
        harness = p.parseNode(filename, h_node)
    if p.status() > 0:
        msg = "An error occurred during parsing of the root level parameters for creation of the TestHarness object, see console message(s) for details."
        raise RuntimeError(msg)

    harness.parameters().setValue('controllers', controllers)
    harness.parameters().setValue('formatter', formatter)
    harness.parameters().setValue('object_defaults', object_defaults)
    return harness


def _make_controllers(filename, root):
    """
    Create the `Controller` object from the [Controllers] block of the `pyhit.Node` of *root*.

    The *filename* is provided for error reporting and setting the current working directory for
    creating object defined in the configuration file. It should be the file used for generating
    the tree structure in *root*.
    """

    # Locate/create the [Controllers] node
    c_node = moosetree.find(root, func=lambda n: n.fullpath == '/Controllers')
    if c_node is None:
        c_node = root.append('Controllers')

    # Factory for building Controller objects
    working_dir = os.path.dirname(filename) if (filename is not None) else os.getcwd()
    with mooseutils.CurrentWorkingDirectory(working_dir):
        plugin_dirs = [
            os.path.abspath(mooseutils.eval_path(path))
            for path in os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split()
        ]
    c_factory = factory.Factory(plugin_dirs=tuple(plugin_dirs), plugin_types=(base.Controller, ))
    c_factory.load()
    if c_factory.status() > 0:
        msg = "An error occurred registering the Controller type, see console message(s) for details."
        raise RuntimeError(msg)

    # All Controller object type found by the Factory are automatically included with the default
    # configuration, if the static AUTO_BUILD member variable is True. This adds these objects to the
    # configuration tree so they will be built by the factory
    c_types = set(child['type'] for child in c_node)
    for name in [key for key, value in c_factory._registered_types.items() if value.AUTO_BUILD]:
        if name not in c_types:
            c_node.append(f"_moosetools_{name}", type=name)

    # Use the Parser to create the Controller objects
    c_parser = factory.Parser(c_factory)
    with mooseutils.CurrentWorkingDirectory(working_dir):
        controllers = [c_parser.parseNode(filename, n) for n in c_node]
    if c_parser.status() > 0:
        msg = "An error occurred during parsing of the Controller block, see console message(s) for details."
        raise RuntimeError(msg)

    return tuple(controllers)


def _make_formatter(filename, root):
    """
    Create the `Formatter` object from the [Formatter] block of the `pyhit.Node` of *root*.

    By default, a `BasicFormatter` is created. Refer to `make_controllers` function for information
    on the supplied input arguments.
    """
    #from moosetools.moosetest.formatters import BasicFormatter
    # Locate/create the [Formatter] node
    f_node = moosetree.find(root, func=lambda n: n.fullpath == '/Formatter')
    if f_node is None:
        f_node = root.append('Formatter', type='BasicFormatter')

    # Factory for building Formatter objects
    working_dir = os.path.dirname(filename) if (filename is not None) else os.getcwd()
    with mooseutils.CurrentWorkingDirectory(working_dir):
        plugin_dirs = [
            os.path.abspath(mooseutils.eval_path(path))
            for path in os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split()
        ]
    f_factory = factory.Factory(plugin_dirs=tuple(plugin_dirs), plugin_types=(base.Formatter, ))
    f_factory.load()
    if f_factory.status() > 0:
        msg = "An error occurred registering the Formatter type, see console message(s) for details."
        raise RuntimeError(msg)

    # Create the Formatter object by parsing the input file
    f_parser = factory.Parser(f_factory)
    with mooseutils.CurrentWorkingDirectory(working_dir):
        formatter = f_parser.parseNode(filename, f_node)
    if f_parser.status() > 0:
        msg = "An error occurred during parsing of the root level parameters for creation of the Formatter object, see console message(s) for details."
        raise RuntimeError(msg)

    return formatter


def _setup_environment(filename, root):
    """
    Set environment variables from the top-level parameters
    """
    working_dir = os.path.dirname(filename) if filename is not None else os.getcwd()
    with mooseutils.CurrentWorkingDirectory(working_dir):
        for name, value in root.params():
            if name not in os.environ:
                value = mooseutils.eval_path(value)
                os.environ[name] = os.path.abspath(value) if os.path.isdir(value) else value


def _get_object_defaults(filenname, root):
    """
    Return a dict of dict containing object defaults to pass to discover function.
    """
    d_node = moosetree.find(root, func=lambda n: n.fullpath == '/Defaults')
    if d_node is None:
        return dict()

    out = dict()
    for child in d_node:
        out[child.name] = dict(child.params())

    return out


def _locate_config(start):
    """
    Recursively, up the directory tree, locate and return a ".moosetest" file if *start* is a directory.

    If *start* is a file, return the supplied value.
    """

    if os.path.isfile(start):
        return start

    elif not os.path.isdir(start):
        msg = f"The supplied configuration location, '{start}', must be a filename or directory."
        raise RuntimeError(msg)

    root_dir = os.path.abspath(start) + os.sep  # add trailing / to consider the start directory
    for i in range(root_dir.count(os.sep)):
        root_dir = root_dir.rsplit(os.sep, 1)[0]
        fname = os.path.join(root_dir, '.moosetest')
        if os.path.isfile(fname):
            return fname

    return None


def _load_config(filename):
    """
    Load the supplied HIT *filename* using the `pyhit.load` function and return the root node.

    If the supplied *filename* is `None`, then a default configuration is returned.
    """
    if filename is None:
        root = pyhit.Node(None)
        root.append('TestHarness', type='TestHarness')

    elif not os.path.isfile(filename):
        msg = "The configuration file, '{}', does not exist."
        raise RuntimeError(msg.format(filename))

    else:
        root = pyhit.load(filename)

    return root
