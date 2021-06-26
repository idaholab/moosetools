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
#from moosetools.moosetest import discover, run, fuzzer
# These imports are needed so the various Factory objects register the locally available objects
from moosetools.moosetest import base
#from moosetools.moosetest.base import TestHarness
from moosetools.moosetest import formatters, controllers

def cli_args():
    """
    Create the ArgumentParser object from the `TestHarness` base object. The only argument used
    within the `main` function is the --config option. All objects are created
    """
    parser = base.TestHarness.createCommandLineParser(base.TestHarness.validParams())
    parser.add_help = False
    known, _ = parser.parse_known_args()
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

    # Setup the environment variables from [Environment] block
    _setup_environment(filename, root)

    # Create the Controller, Formatter, and TestHarness objects
    controllers =_make_controllers(filename, root)
    formatter = _make_formatter(filename, root)
    harness = _make_harness(filename, root, controllers, formatter)

    return harness.run()


def _make_harness(filename, root, controllers, formatter):
    """
    Create the `Controller` object from the [TestHarness] block of the `pyhit.Node` of *root*.

    The *filename* is provided for error reporting and setting the current working directory for
    creating object defined in the configuration file. It should be the file used for generating
    the tree structure in *root*.

    The *controllers* and *formatter* are applied to the created `TestHarness` object via the
    parameters by the same name.
    """
    # Top-level parameters are used to build the TestHarness object. Creating custom `TestHarness`
    # objects is not-supported, so don't allow "type" to be set.
    h_node = moosetree.find(root, func=lambda n: n.fullpath == '/TestHarness')
    if h_node is None:
        h_node = root.append('TestHarness', type='TestHarness')

    # Build a factory capable of creating the TestHarness object
    plugin_dirs = os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split()
    h_factory = factory.Factory(plugin_dirs=tuple(plugin_dirs), plugin_types=(base.TestHarness,))
    h_factory.load()
    if h_factory.status() > 0:
        msg = "An error occurred during registration of the TestHarness type, see console message(s) for details."
        raise RuntimeError(msg)

    # Use the Parser is used to correctly convert HIT to InputParameters
    w = list()
    p = factory.Parser(h_factory, w)
    with mooseutils.CurrentWorkingDirectory(os.path.dirname(filename)):
        p._parseNode(filename, h_node)
    if p.status() > 0:
        msg = "An error occurred during parsing of the root level parameters for creation of the TestHarness object, see console message(s) for details."
        raise RuntimeError(msg)

    harness = w[0]
    harness.parameters().setValue('_controllers', controllers)
    harness.parameters().setValue('_formatter', formatter)
    return harness


def _make_controllers(filename, root, *kwargs):
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
    plugin_dirs = os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split()
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
    controllers = list()
    c_parser = factory.Parser(c_factory, controllers)
    with mooseutils.CurrentWorkingDirectory(os.path.dirname(filename)):
        c_parser.parse(filename, c_node)
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
    plugin_dirs = os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split()
    f_factory = factory.Factory(plugin_dirs=tuple(plugin_dirs), plugin_types=(base.Formatter, ))
    f_factory.load()
    if f_factory.status() > 0:
        msg = "An error occurred registering the Formatter type, see console message(s) for details."
        raise RuntimeError(msg)

    # Create the Formatter object by parsing the input file
    formatters = list()
    f_parser = factory.Parser(f_factory, formatters)
    with mooseutils.CurrentWorkingDirectory(os.path.dirname(filename)):
        f_parser._parseNode(filename, f_node)
    if f_parser.status() > 0:
        msg = "An error occurred during parsing of the root level parameters for creation of the Formatter object, see console message(s) for details."
        raise RuntimeError(msg)

    return formatters[0]


def _setup_environment(filename, root):
    """
    Set environment variables from the top-level parameters

    """
    for name, value in root.params():
        os.environ[name] = value


    """
    Update environment from the [Environment] block.

    e_node = moosetree.find(root, func=lambda n: n.fullpath == '/Environment')
    if e_node is not None:
        for name, value in e_node.params():
            if name not in os.environ:
                with mooseutils.CurrentWorkingDirectory(os.path.dirname(filename)):
                    path = mooseutils.eval_path(value)
                    if os.path.exists(path):
                        value = os.path.abspath(path)
                    os.environ[name] = value
    """


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

    msg = f"Unable to locate a configuration in the location '{start}'."
    raise RuntimeError(msg)


def _load_config(filename):
    """
    Load the supplied HIT *filename* using the `pyhit.load` function and return the root node.
    """
    if not os.path.isfile(filename):
        msg = "The configuration file, '{}', does not exist."
        raise RuntimeError(msg.format(filename))
    return pyhit.load(filename)
