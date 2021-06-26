import os
import logging
import argparse
from moosetools import core
from moosetools import moosetest

from .Controller import Controller
from .Formatter import Formatter


class TestHarness(core.MooseObject):
    """
    Object for locating and running tests defined by HIT specification files.

    Please refer to `moostest.main` for use.
    """
    @staticmethod
    def validParams():
        params = core.MooseObject.validParams()

        # Public parameters
        # These are intended to be set within a HIT configuration file
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
                   doc="The maximum number of seconds allowed for the execution of a test (default: 300).")
        params.add('max_failures',
                   default=50,
                   vtype=int,
                   doc="The maximum number of failures allowed before terminating all test cases.")

        # Private parameters
        # These are not intended to be set by the HIT configuration file
        params.add('_controllers',
                   private=True,
                   vtype=Controller,
                   array=True,
                   doc="The `Controller` object to utilize when creating `Runner` and `Differ` objects.")
        params.add('_formatter',
                   private=True,
                   vtype=Formatter,
                   doc="The `Formatter` object to utilize for outputting test information.")

        return params

    @staticmethod
    def createCommandLineParser(params):
        parser = argparse.ArgumentParser(description="Testing system inspired by MOOSE")
        parser.add_argument('--config', default=os.getcwd(), type=str,
                            help="A configuration file or directory. If a directory is provided a " \
                            "'.moosetest' file is searched up the directory tree beginning with " \
                            "the current working directory.")

        p = params.parameter('timeout')
        parser.add_argument('--timeout', type=float, default=p.default, help=p.doc)

        p = params.parameter('max_failures')
        parser.add_argument('--max-failures', type=int, default=p.default, help=p.doc)

        p = params.parameter('spec_file_blocks')
        parser.add_argument('--spec-file-blocks', type=str, nargs='+', default=p.default, help=p.doc)

        p = params.parameter('spec_file_names')
        parser.add_argument('--spec-file-names', type=str, nargs='+', default=p.default, help=p.doc)

        return parser


    def __init__(self, *args, **kwargs):
        core.MooseObject.__init__(self, *args, **kwargs)

        # Parse the command-line arguments and apply them to this object
        parser = self.createCommandLineParser(self.parameters())
        args = parser.parse_args()
        self._setup(args)



    def _setup(self, args):
        """
        Apply options provided via the command line to the TestHarness object parameters.
        """
        if args.timeout:
            self.parameters().setValue('timeout', args.timeout)

        if args.max_failures:
            self.parameters().setValue('max_failures', args.max_failures)

        if args.spec_file_blocks:
            self.parameters().setValue('spec_file_blocks', tuple(args.spec_file_blocks))

        if args.spec_file_names:
            self.parameters().setValue('spec_file_names', tuple(args.spec_file_names))

    def run(self):

        # Locate the tests to execute
        groups = moosetest.discover(os.getcwd(),
                                     self.getParam('spec_file_names'),
                                     self.getParam('spec_file_blocks'),
                                     os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split(),
                                     self.getParam('_controllers'),
                                     self.getParam('n_threads'))

        # Execute the tests
        rcode = moosetest.run(groups,
                              self.getParam('_controllers'),
                              self.getParam('_formatter'),
                              self.getParam('n_threads'),
                              self.getParam('timeout'),
                              self.getParam('max_failures'))

        return rcode
