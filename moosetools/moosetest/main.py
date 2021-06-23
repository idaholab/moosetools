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
import logging
import argparse
from moosetools import parameters
from moosetools import moosetree
from moosetools import pyhit
from moosetools import factory
from moosetools import core
from moosetools import mooseutils
from moosetools.moosetest import discover, run, fuzzer
from moosetools.moosetest.base import Controller, Formatter, make_runner, make_differ
from moosetools.moosetest.base import make_runner, make_differ
from moosetools.moosetest.runners import RunCommand
from moosetools.moosetest.differs import ConsoleDiffer
from moosetools.moosetest.controllers import EnvironmentController
from moosetools.moosetest.formatters import BasicFormatter

# Local directory, to be used for getting the included Controller/Formatter objects
LOCAL_DIR = os.path.abspath(os.path.dirname(__file__))


def cli_args():
    """
    Return command line arguments.
    """
    parser = argparse.ArgumentParser(description='Testing system inspired by MOOSE')
    parser.add_argument('--demo',
                        action='store_true',
                        help="Ignore all other arguments and run a demonstration.")
    parser.add_argument('--config', default=os.getcwd(), type=str,
                        help="The configuration file or directory. If a directory is provided a " \
                             "'.moosetest' file is searched up the directory tree beginning at " \
                             "the supplied location (default: %(default)s).")
    return parser.parse_args()


class TestHarness(core.MooseObject):
    """
    Object for extracting general configuration options from a HIT file.

    !alert info title=Build with `make_harness` function
    This object should be created the the `make_harness` function, which provides handling of the
    current working directory with respect to the configuration file.
    """
    @staticmethod
    def validParams():
        params = core.MooseObject.validParams()
        params.add(
            'plugin_dirs',
            default=tuple(),
            vtype=str,
            array=True,
            doc=
            "List of directories to search for plugins, the location should be relative to the configure file."
        )

        params.add('n_threads',
                   default=os.cpu_count(),
                   vtype=int,
                   doc="The number of threads to utilize when running tests.")
        params.add(
            'spec_file_names',
            vtype=str,
            array=True,
            default=('tests', ),
            doc="List of file names (e.g., 'tests') that contain test specifications to run.")
        params.add('spec_file_blocks',
                   vtype=str,
                   array=True,
                   default=('Tests', ),
                   doc="List of top-level test specifications (e.g., `[Tests]`) HIT blocks to run.")
        params.add('timeout',
                   default=300.,
                   vtype=float,
                   doc="Number of seconds allowed for the execution of a test case.")
        params.add('max_failures',
                   default=50,
                   vtype=int,
                   doc="The maximum number of failures allowed before terminating all test cases.")
        return params

    def __init__(self, *args, **kwargs):
        core.MooseObject.__init__(self, *args, **kwargs)
        logging.basicConfig(level=self.getParam('log_level'))

        # Update the "plugin_dirs" to be absolute paths
        plugin_dirs = list()
        for p_dir in self.getParam('plugin_dirs'):
            plugin_dirs.append(os.path.abspath(p_dir))
        self.parameters().setValue('plugin_dirs', tuple(plugin_dirs))

    def applyCommandLineArguments(self, args):
        """
        Apply options provided via the command line to the TestHarness object parameters.
        """
        pass


def main():
    """
    Complete function for automatically detecting and performing tests based on test specifications.

    This function exists for the use by the `moosetest` executable in the bin directory of the
    moosetools repository.
    """

    # Extract command-line arguments
    args = cli_args()
    if args.demo:
        return fuzzer()

    # Locate the config
    filename = _locate_config(args.config)

    # Load the config (pyhit.Node)
    root = _load_config(filename)

    # Create the TestHarness object from the configuration, after this point the cli_args should
    # no longer be used. They are applied to the TestHarness object in this function by calling
    # the TestHarness.applyCommandLineArguments method.
    harness = make_harness(filename, root, args)
    del args  # just to avoid accidental use in the future

    # Create the Controller objects and Formatter
    controllers = make_controllers(filename, root, harness.getParam('plugin_dirs'))
    formatter = make_formatter(filename, root, harness.getParam('plugin_dirs'))

    # Locate the tests to execute
    groups = discover(os.getcwd(), harness.getParam('spec_file_names'),
                      harness.getParam('spec_file_blocks'), harness.getParam('plugin_dirs'),
                      controllers, harness.getParam('n_threads'))

    # Execute the tests
    rcode = run(groups, controllers, formatter, harness.getParam('n_threads'),
                harness.getParam('timeout'), harness.getParam('max_failures'))

    return rcode


def make_harness(filename, root, cli_args):
    """
    Create the `TestHarness` object from top-level parameters in the `pyhit.Node` of *root*.

    The *filename* is provided for error reporting and should be the file used for generating
    the tree structure in *root*. The *cli_args* input is passed to the created `TestHarness` object
    via the `applyCommandLineArguments` method.

    It is expected that the file that produced *root* has top-level parameters, which are used to
    create a `TestHarness` object.
    """
    # Top-level parameters are used to build the TestHarness object. Creating custom `TestHarness`
    # objects is not-supported, so don't allow "type" to be set.
    if 'type' in root:
        msg = "The 'type' parameter must NOT be defined in the top-level of the configuration."
        raise RuntimeError(msg)
    root['type'] = 'TestHarness'

    # Build a factory capable of creating the TestHarness object
    f = factory.Factory()
    f.register('TestHarness', TestHarness)
    if f.status() > 0:
        msg = "An error occurred during registration of the TestHarness type, see console message(s) for details."
        raise RuntimeError(msg)

    # Setup the environment variables
    setup_environment(filename, root)

    # Use the Parser is used to correctly convert HIT to InputParameters
    w = list()
    p = factory.Parser(f, w)
    with mooseutils.CurrentWorkingDirectory(os.path.dirname(filename)):
        p._parseNode(filename, root)
    if p.status() > 0:
        msg = "An error occurred during parsing of the root level parameters for creation of the TestHarness object, see console message(s) for details."
        raise RuntimeError(msg)

    # Apply the command line arguments to update TestHarness object parameters
    harness = w[0]
    harness.applyCommandLineArguments(cli_args)
    if harness.status() > 0:
        msg = "An error occurred applying the command line arguments to the TestHarness object, see console message(s) for details."
        raise RuntimeError(msg)

    return harness


def make_controllers(filename, root, plugin_dirs):
    """
    Create the `Controller` object from the [Controllers] block of the `pyhit.Node` of *root*.

    The *filename* is provided for error reporting and setting the current working directory for
    creating object defined in the configuration file. It should be the file used for generating
    the tree structure in *root*.

    The *plugin_dirs* should contain a list of absolute paths to include when registering Controller
    objects with the factory. By default, regardless of the contents of *root*, all registered
    Controller objects are created.
    """

    # Locate/create the [Controllers] node
    c_node = moosetree.find(root, func=lambda n: n.fullpath == '/Controllers')
    if c_node is None:
        c_node = root.append('Controllers')

    # Factory for building Controller objects
    c_factory = factory.Factory(plugin_dirs=plugin_dirs, plugin_types=(Controller, ))
    c_factory.load()
    if c_factory.status() > 0:
        msg = "An error occurred registering the Controller type, see console message(s) for details."
        raise RuntimeError(msg)

    # All Controller object type found by the Factory are automatically included with the default
    # configuration. This adds them to the configuration tree so they will be built by the factory
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


def make_formatter(filename, root, plugin_dirs):
    """
    Create the `Formatter` object from the [Formatter] block of the `pyhit.Node` of *root*.

    By default, a `BasicFormatter` is created. Refer to `make_controllers` function for information
    on the supplied input arguments.
    """

    # Locate/create the [Formatter] node
    f_node = moosetree.find(root, func=lambda n: n.fullpath == '/Formatter')
    if f_node is None:
        f_node = root.append('Formatter', type='BasicFormatter')

    # Factory for building Formatter objects
    f_factory = factory.Factory(plugin_dirs=plugin_dirs, plugin_types=(Formatter, ))
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


def setup_environment(filename, root):
    """
    Update environment from the [Environment] block.
    """
    e_node = moosetree.find(root, func=lambda n: n.fullpath == '/Environment')
    if e_node is not None:
        for name, value in e_node.params():
            if name not in os.environ:
                with mooseutils.CurrentWorkingDirectory(os.path.dirname(filename)):
                    path = mooseutils.eval_path(value)
                    if os.path.exists(path):
                        value = os.path.abspath(path)
                    os.environ[name] = value


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
