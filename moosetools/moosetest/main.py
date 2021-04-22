import os
import sys
import logging
import argparse
from moosetools import parameters
from moosetools import moosetree
from moosetools import pyhit
from moosetools import factory
from moosetools.moosetest.base import Controller
from moosetools.moosetest.controllers import EnvironmentController
from moosetools.moosetest import discover


# TODO:
# - check status() of factory after factory calls
# - change ProcessRunner to RunCommand

def valid_params():
    """
    No need for MooseObject
    """
    params = parameters.InputParameters()
    params.add('progress_interval', vtype=int, default=10,
               doc="The duration between printing the progress message of test cases.")

    params.add('plugin_dirs',
               vtype=str,
               array=True,
               verify=(lambda dirs: all(os.path.isdir(d) for d in dirs),
                       "Supplied plugin directories must exist."),
               doc="List of directories to search for plugins, the location should be relative to the configure file.")

    params.add('n_threads', default=os.cpu_count(), vtype=int,
               doc="The number of threads to utilize when running tests.")

    params.add('spec_file_names', vtype=str, array=True, default=('tests',),
               doc="List of file names (e.g., 'tests') that contain test specifications to run.")
    params.add('spec_file_blocks', vtype=str, array=True, default=('Tests',),
               doc="List of top-level test specifications (e.g., `[Tests]`) HIT blocks to run.")


    return params


def cli_args():
    parser = argparse.ArgumentParser(description='Testing system inspired by MOOSE')
    parser.add_argument('--config', default=os.getcwd(), type=str,
                        help="The configuration file or directory. If a directory is provided a " \
                             "'.moosetest' file is searched up the directory tree beginning at " \
                             "the supplied location (default: %(default)s).")

    # TODO: Add valid_params to this and then apply cli_args to valid_params via the Parser?
    # This would probably be overkill, the --help should probably just refer to the ability to
    # configure things with .moosetest file. The _locate_and_load_config should just accept the
    # complete argparse and update what is needed.

    return parser.parse_args()


def main():
    """

    Give some notes about mockable/testable functions and avoiding classes

    discover: should be able to operate without any need for config stuff
    run: should be able to operate without any need for HIT files

    """
    # Extract command-line arguments
    args = cli_args()

    # TODO: update docs after this is working, perhaps the handler needs to be set on the MooseTest object
    # TODO: change formatter in redirect output of TestCase
    # Setup basic logging. The formatting is removed to allow for captured logs from the tests to
    # have a minimal width. A stream handler is also added to allow for the capture to occur, this
    # occurs in the TestCase object.
    #handler = logging.StreamHandler()
    #logging.basicConfig(handlers=[handler], level=args.level)#, format='%(message)s')
    logging.basicConfig(level='DEBUG')

    # Load the configuration
    filename, config = _locate_and_load_config(args.config)

    # Get/update the [Main] parameters
    params = _create_main_parameters(filename, config)

    # Create `Controller` objects for managing the testing
    controllers = _create_controllers(filename, config, params.get('plugin_dirs') or tuple())


    testcase_groups = discover(os.getcwd(),
                               params.get('spec_file_names'),
                               params.get('spec_file_blocks'),
                               params.get('plugin_dirs'),
                               controllers,
                               params.get('n_threads'))

    # run(testcase_groups)
    # - remove execute functions from TestCase
    # - remove 'controllers' from TestCase, it should just be an argument in run_testcases function

    # return 0|1

def _create_main_parameters(filename, config):
    """
    ...
    """
    # Update the parameters with the key/value pairs in the [Main] block
    params = valid_params()
    m_mode = moosetree.find(config, func=lambda n: n.name == 'Main')
    if m_mode is not None:
        factory.Parser.setParameters(params, filename, m_mode)

    # Update the paths of supplied plugin directories to be relative to the config file
    plugin_dirs = set()
    if params.isValid('plugin_dirs'):
        root_dir_name = os.path.dirname(filename) if os.path.isfile(filename) else filename
        for p_dir in params.get('plugin_dirs'):
            plugin_dirs.add(os.path.join(root_dir_name, p_dir))

    # Add directories in the moosetest package itself
    plugin_dirs.add(os.path.abspath(os.path.join(os.path.dirname(__file__), 'runners')))
    plugin_dirs.add(os.path.abspath(os.path.join(os.path.dirname(__file__), 'differs')))
    plugin_dirs.add(os.path.abspath(os.path.join(os.path.dirname(__file__), 'controllers')))

    params.set('plugin_dirs', tuple(plugin_dirs))
    return params


def _locate_config(start):
    if not os.path.isdir(start):
        msg =  "The supplied starting directory, '{}', does not exist or is not a directory."
        raise RuntimeError(msg.format(start))

    root_dir = os.path.abspath(start) + os.sep # add trailing / to consider the start directory
    for i in range(root_dir.count(os.sep)):
        fname = os.path.join(root_dir.rsplit(os.sep, 1)[0], '.moosetest')
        if os.path.isfile(fname):
            return fname

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
    main()
