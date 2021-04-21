import os
import sys
import logging
import argparse
from moosetools import moosetree
from moosetools import pyhit
from moosetools import factory
from moosetools.moosetest.base import MooseTest, Controller
from moosetools.moosetest.controllers import EnvironmentController

def locate_config(start):
    if not os.path.isdir(start):
        msg =  "The supplied starting directory, '{}', does not exist or is not a directory."
        raise RuntimeError(msg.format(start))

    root_dir = os.path.abspath(start) + os.sep # add trailing / to consider the start directory
    for i in range(root_dir.count(os.sep)):
        fname = os.path.join(root_dir.rsplit(os.sep, 1)[0], '.moosetest')
        if os.path.isfile(fname):
            return fname

def load_config(filename):
    if not os.path.isfile(filename):
        msg =  "The configuration file, '{}', does not exist."
        raise RuntimeError(msg.format(filename))
    root = pyhit.load(filename)
    return root

def create_objects(filename, root):
    """

    """
    # Create a MooseTest object.
    # The MooseTest object is the starting point for managing the tests that will be executed. It is
    # not the intent to specialize this class. However, it is configurable via a ".moosetest" file.
    # As such, the moosetools.factory system is used to parse this file and create the object. The
    # parameters at the root level of the file, which is a HIT file, are used in creating the object.
    f = factory.Factory(plugin_type=MooseTest)
    f.register('MooseTest', MooseTest)
    w = list()
    p = factory.Parser(f, w)
    p.parse(filename, root)
    if p.status():
        raise RuntimeError("An error occurred during the creation of the 'MooseTest' object.")
    mt_obj = w[0]

    # Create `Controller` objects
    plugin_dirs = [os.path.dirname(EnvironmentController.__file__)]
    if mt_obj.isParamValid('plugin_dirs'): plugin_dirs += list(mt_obj.getParam('plugin_dirs'))

    f = factory.Factory(plugin_dirs=tuple(plugin_dirs), plugin_type=Controller)
    f.load()

    w = list()
    p = factory.Parser(f, w)
    for child in config:
        p._parseNode(filename, child)


    return mt_obj, None




def locate_and_load_config(location=os.getcwd()):
    """
    Create and return a `pyhit` tree containing the configuration for the testing.

    If a directory is provided to *location* the directory structure is searched from the supplied
    location up the tree. When a ".moosetest" file is found, it is used to create the tree. If it
    is not found then an empty tree structure is returned.

    If a file is provided to *location* this file is used to create the tree.
    """
    filename = location if os.path.isfile(location) else locate_config(location)
    if filename is None:
        logging.debug('Using default configuration.')
        config = pyhit.Node(None)
        config.append('Main', type='MooseTest')
        controllers = config.append('Controllers')
        controllers.append('env', type='EnvironmentController')
    else:
        logging.debug('Using configuration from file: {}'.format(filename))
        config = load_config(filename)
    return filename, config

def create_moose_test(filename, config):
    """
    Create the base `MooseTest` object responsible for managing the testing given the *config* input,
    which is a `pyhit.Node` that include the parameters for the object to be created. Generally, the
    *config* input should be obtained by calling the `locate_and_load_config` function. The
    *filename* is provided for error reporting during parsing.
    """
    if ('type' in config) and (config['type'] != 'MooseTest'):
        msg = "The 'type' should not exist or be `MooseTest`. If you are needing to specialize, " \
              "please contact the developers and explain what you are trying to do, perhaps there " \
              "is an improvement that can be made to support your need."
        raise RuntimeError(msg)

    # Set default/private parameters for the MooseTest object to be created
    config['type'] = 'MooseTest'
    config['_root_dir'] = os.path.dirname(filename)

    # Create a MooseTest object.
    # The MooseTest object is the starting point for managing the tests that will be executed. It is
    # not the intent to specialize this class. However, it is configurable via a ".moosetest" file.
    # As such, the moosetools.factory system is used to parse this file and create the object. The
    # parameters at the root level of the file, which is a HIT file, are used in creating the object.
    f = factory.Factory(plugin_type=MooseTest)
    f.register('MooseTest', MooseTest)
    w = list()
    p = factory.Parser(f, w)
    p._parseNode(filename, config)
    if p.status():
        raise RuntimeError("An error occurred during the creation of the 'MooseTest' object.")
    obj = w[0]
    return w[0] # MooseTest instance


def create_controllers(filename, config, plugin_dirs):
    """
    Create the `Controller` objects that dictate if a test should execute given the *config* input,
    which is a `pyhit.Node` that includes the object to create and the associated parameters.
    Generally, the *config* input should be obtained by extracting the `[Controllers]` block returned
    by calling the `locate_and_load_config` function. The *filename* is provided for error reporting
    during parsing. The *plugin_dirs* is a list of locations to look for `Controller` objects, in
    addition to the locations in this module.
    """

    # Load `Controller` plugins
    f = factory.Factory(plugin_dirs=plugin_dirs or tuple(), plugin_type=Controller)
    f.load()
    f.register('EnvironmentController', EnvironmentController)

    w = list()
    p = factory.Parser(f, w)
    for child in config:
        p._parseNode(filename, child)

    print(w)


def get_options():
    parser = argparse.ArgumentParser(description='Testing system inspired by MOOSE')
    parser.add_argument('--config', default=os.getcwd(), type=str,
                        help="The configuration file or directory. If a directory is provided a " \
                             "'.moosetest' file is searched up the directory tree beginning at " \
                             "the supplied location (default: %(default)s).")
    #parser.add_argument('--level', default='INFO', choices=list(logging._nameToLevel.keys()),
    #                    help='Set the logging level (default: %(default)s).')

    return parser.parse_args()


def main():
    """

    Give some notes about mockable/testable functions

    """


    # Extract command-line arguments
    args = get_options()

    # TODO: update docs after this is working, perhaps the handler needs to be set on the MooseTest object
    # TODO: change formatter in redirect output of TestCase
    # Setup basic logging. The formatting is removed to allow for captured logs from the tests to
    # have a minimal width. A stream handler is also added to allow for the capture to occur, this
    # occurs in the TestCase object.
    handler = logging.StreamHandler()
    logging.basicConfig(handlers=[handler], level=args.level)#, format='%(message)s')

    # Load the configuration
    filename, config = locate_and_load_config(args.config)

    # Create the object that will manage the testing.
    moosetest, controllers = create_objects(filename, config)
    #moosetest = create_moose_test(filename, config)

    # Create the Controller objects.
    #cnode = moosetree.find(config, func=lambda n: n.name=='Controllers') or pyhit.Node(None)
    #controllers = create_controllers(filename, cnode, moosetest.getParam('plugin_dirs'))







if __name__ == '__main__':
    main()
