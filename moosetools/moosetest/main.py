import os
import sys
import logging
import argparse
from moosetools import parameters
from moosetools import moosetree
from moosetools import pyhit
from moosetools import factory
from moosetools import base
from moosetools.moosetest.base import Controller, Formatter, make_runner, make_differ
from moosetools.moosetest import discover, run, fuzzer


from moosetools.moosetest.base import make_runner, make_differ
from moosetools.moosetest.runners import RunCommand
from moosetools.moosetest.differs import ConsoleDiff
from moosetools.moosetest.controllers import EnvironmentController
from moosetools.moosetest.formatters import BasicFormatter


# TODO:
# - check status() of factory after factory calls
# - change ProcessRunner to RunCommand


# Local directory, to be used for getting the included Controller/Formatter objects
LOCAL_DIR = os.path.abspath(os.path.dirname(__file__))


def cli_args():
    parser = argparse.ArgumentParser(description='Testing system inspired by MOOSE')

    parser.add_argument('--demo', action='store_true',
                        help="Ignore all other arguments and run a demonstration.")

    parser.add_argument('--config', default=os.getcwd(), type=str,
                        help="The configuration file or directory. If a directory is provided a " \
                             "'.moosetest' file is searched up the directory tree beginning at " \
                             "the supplied location (default: %(default)s).")

    # TODO: Add valid_params to this and then apply cli_args to valid_params via the Parser?
    # This would probably be overkill, the --help should probably just refer to the ability to
    # configure things with .moosetest file. The _locate_and_load_config should just accept the
    # complete argparse and update what is needed.

    return parser.parse_args()


class TestHarness(base.MooseObject):
    """
    Object for extracting general configuration options from a HIT file.
    """

    @staticmethod
    def validParams():
        params = base.MooseObject.validParams()
        params.add('plugin_dirs',
                   default=tuple(),
                   vtype=str,
                   array=True,
                   doc="List of directories to search for plugins, the location should be relative to the configure file.")

        params.add('n_threads', default=os.cpu_count(), vtype=int,
                   doc="The number of threads to utilize when running tests.")

        params.add('spec_file_names', vtype=str, array=True, default=('tests',),
                   doc="List of file names (e.g., 'tests') that contain test specifications to run.")
        params.add('spec_file_blocks', vtype=str, array=True, default=('Tests',),
                   doc="List of top-level test specifications (e.g., `[Tests]`) HIT blocks to run.")

        params.add('timeout', default=300., vtype=float,
                   doc="Number of seconds allowed for the execution of a test case.")
        params.add('max_failures', default=50, vtype=int,
                   doc="The maximum number of failures allowed before terminating all test cases.")


        params.add('controllers', vtype=Controller, array=True,
                   doc="Controller objects to utilize for test case creation.")

        params.add('formatter', vtype=Formatter,
                   doc="Formatter object to utilize for test case output.")

        return params

    def __init__(self, *args, **kwargs):
        base.MooseObject.__init__(self, *args, **kwargs)
        logging.basicConfig(level=self.getParam('log_level'))

    #def applyArguments(self, args):
    #    pass





def main():
    """

    Give some notes about mockable/testable functions and avoiding classes


    discover: should be able to operate without any need for config stuff
    run: should be able to operate without any need for HIT files


    """

    # Extract command-line arguments
    args = cli_args()

    if args.demo:
        return fuzzer()


    # Locate the config
    filename = _locate_config(args.config)

    # Load the config (pyhit.Node)
    root = _load_config(filename)

    # Create the TestHarness object from the configuration
    harness = make_harness(filename, root)
    #harness.applyArguments(filename, args)

    controllers = make_controllers(filename, root, harness.getParam('plugin_dirs'))

    formatter = make_formatter(filename, root, harness.getParam('plugin_dirs'))




    groups = discover(os.getcwd(),
                      harness.getParam('spec_file_names'),
                      harness.getParam('spec_file_blocks'),
                      harness.getParam('plugin_dirs'),
                      controllers,
                      harness.getParam('n_threads'))

    rcode = run(groups,
                controllers,
                formatter,
                harness.getParam('n_threads'),
                harness.getParam('timeout'),
                harness.getParam('max_failures'))

    return rcode

def make_harness(filename, root):
    """

    """
    # Top-level parameters are used to build the TestHarness object. Creating custom `TestHarness`
    # objects is not-supported, so don't allow "type" to be set.
    if 'type' in root:
        msg = "The 'type' parameter must NOT be defined in the top-level of the configuration."
    root['type'] = 'TestHarness'

    plugin_dirs = list()
    hit_plugin_dirs = root.get('plugin_dirs', None)
    if hit_plugin_dirs is not None:
        base_dir = os.path.dirname(filename)
        for p_dir in hit_plugin_dirs.split(' '):
            plugin_dirs.append(os.path.abspath(os.path.join(base_dir, p_dir)))
        root['plugin_dirs'] = ' '.join(plugin_dirs)

    # Create the TestHarness object, the Parser is used to correctly convert HIT to InputParameters
    f = factory.Factory()
    f.register('TestHarness', TestHarness)
    w = list()
    p = factory.Parser(f, w)
    p._parseNode(filename, root)
    harness = w[0]

    #harness.parameters().setValue('plugin_dirs', tuple(plugin_dirs))

    #plugin_dirs.append(os.path.abspath(os.path.join(LOCAL_DIR, 'controllers')))
    #plugin_dirs.append(os.path.abspath(os.path.join(LOCAL_DIR, 'formatters')))
    #plugin_dirs.append(os.path.abspath(os.path.join(LOCAL_DIR, 'runners')))
    #plugin_dirs.append(os.path.abspath(os.path.join(LOCAL_DIR, 'differs')))
    #harness.parameters().setValue('plugin_dirs', tuple(plugin_dirs))


    return harness


def make_controllers(filename, root, plugin_dirs):

    # Locate/create the [Controllers] node
    c_node = moosetree.find(root, func=lambda n: n.fullpath == '/Controllers')
    if c_node is None:
        c_node = root.append('Controllers')

    # Factory for building Controller objects
    c_factory = factory.Factory(plugin_dirs=plugin_dirs, plugin_types=(Controller,))
    c_factory.load()

    # All Controller object type found by the Factory are automatically included with the default
    # configuration. This adds them to the configuration tree so they will be built by the factory
    c_types = set(child['type'] for child in c_node)
    for name in c_factory._registered_types.keys():
        if name not in c_types:
            c_node.append(f"_default_{name}", type=name)

    controllers = list()
    c_parser = factory.Parser(c_factory, controllers)
    c_parser.parse(filename, c_node)

    return tuple(controllers)

def make_formatter(filename, root, plugin_dirs):

    # Locate/create the [Formatter] node
    f_node = moosetree.find(root, func=lambda n: n.fullpath == '/Formatter')
    if f_node is None:
        f_node = root.append('Formatter', type='BasicFormatter', root_test_dir=os.path.dirname(filename))

    # Factory for building Formatter objects
    f_factory = factory.Factory(plugin_dirs=plugin_dirs, plugin_types=(Formatter,))
    f_factory.load()

    formatters = list()
    f_parser = factory.Parser(f_factory, formatters)
    f_parser._parseNode(filename, f_node)

    return formatters[0]

def _locate_config(start):

    if os.path.isfile(start):
        return start

    elif not os.path.isdir(start):
        msg =  f"The supplied configuration location, '{start}', must be a filename or directory."
        raise RuntimeError(msg)

    root_dir = os.path.abspath(start) + os.sep # add trailing / to consider the start directory
    for i in range(root_dir.count(os.sep)):
        root_dir = root_dir.rsplit(os.sep, 1)[0]
        fname = os.path.join(root_dir, '.moosetest')
        if os.path.isfile(fname):
            return fname

    msg = f"Unable to locate a configuration in the location '{start}'."
    raise RuntimeError(msg)

def _load_config(filename):
    if not os.path.isfile(filename):
        msg =  "The configuration file, '{}', does not exist."
        raise RuntimeError(msg.format(filename))
    root = pyhit.load(filename)

    return root

def _locate_and_load_config(location=os.getcwd()):
    """
    Create and return a `pyhit` tree containing the configuration for the testing.

    If a directory is provided to *location* the directory structure is searched from the supplied
    location up the tree. When a ".moosetest" file is found, it is used to create the tree. If it
    is not found then an empty tree structure is returned.

    If a file is provided to *location* this file is used to create the tree.
    """
    filename = location if os.path.isfile(location) else _locate_config(location)
    if filename is None:
        logging.debug('Using default configuration.')
        config = pyhit.Node(None)
        controllers = config.append('Controllers')
        controllers.append('env', type='EnvironmentController')
    else:
        logging.debug('Using configuration from file: {}'.format(filename))
        config = _load_config(filename)
    return filename, config

def _create_controllers(filename, config, plugin_dirs):
    """
    Create the `Controller` objects that dictate if a test should execute given the *config* input,
    which is a `pyhit.Node` that includes the object to create and the associated parameters.
    Generally, the *config* input should be obtained by extracting the `[Controllers]` block returned
    by calling the `locate_and_load_config` function. The *filename* is provided for error reporting
    during parsing. The *plugin_dirs* is a list of locations to look for `Controller` objects, in
    addition to the locations in this module.
    """

    # Get `Controllers` node
    cnode = moosetree.find(config, func=lambda n: n.name == 'Controllers')

    # Load `Controller` plugins
    f = factory.Factory(plugin_dirs=plugin_dirs, plugin_types=(Controller,))
    f.load()

    w = list()
    p = factory.Parser(f, w)
    p.parse(filename, cnode)
    return tuple(w)


if __name__ == '__main__':
    sys.exit(main())
