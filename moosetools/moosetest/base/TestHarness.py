#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import logging
import argparse
import inspect
from moosetools import core
from moosetools import moosetest

from .Controller import Controller
from .Formatter import Formatter
from .Filter import Filter


class TestHarness(core.MooseObject):
    """
    Object for locating and running tests defined by HIT specification files.

    Please refer to `moostest.main` for use.
    """
    @staticmethod
    def validParams():
        params = core.MooseObject.validParams()

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
                   doc="The maximum number of seconds allowed for the execution of a test.")
        params.add('max_failures',
                   default=300,
                   vtype=int,
                   doc="The maximum number of failures allowed before terminating all test cases.")

        # These are not intended to be set by the HIT configuration file
        params.add(
            'controllers',
            vtype=Controller,
            array=True,
            doc="The `Controller` object(s) to utilize when creating `Runner` and `Differ` objects."
        )
        params.add('formatter',
                   default=moosetest.formatters.BasicFormatter(),
                   vtype=Formatter,
                   doc="The `Formatter` object to utilize for outputting test information.")
        params.add('filters',
                   vtype=Filter,
                   array=True,
                   doc="The `Filter` object(s) to utilize when create `TestCase` objects.")

        return params

    @staticmethod
    def validCommandLineArguments(parser, params):
        parser.add_argument('--config', default=os.getcwd(), type=str,
                            help="A configuration file or directory. If a directory is provided a " \
                            "'.moosetest' file is searched up the directory tree beginning with " \
                            "the current working directory.")

        params.toArgs(parser, 'n_threads', 'timeout', 'max_failures', 'spec_file_blocks',
                      'spec_file_names')

        # Add CLI arguments from other top-level objects
        for obj in (params.getValue('controllers') or tuple()):
            obj.validCommandLineArguments(parser, obj.parameters())

        for obj in (params.getValue('filters') or tuple()):
            obj.validCommandLineArguments(parser, obj.parameters())

        obj = params.getValue('formatter')
        if obj is not None:
            obj.validCommandLineArguments(parser, obj.parameters())

        return parser

    def parse(self):
        """
        Initialize the object by processing and applying the command line arguments.

        This needs to be a stand-alone function, because doing this within the constructor
        automatically parse arguments, which might not be desired.
        """
        # Parse the command-line arguments and apply them to this object
        parser = argparse.ArgumentParser(description="Testing system inspired by MOOSE",
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.validCommandLineArguments(parser, self.parameters())
        args = parser.parse_args()
        self._setup(args)

    def _setup(self, args):
        """
        Apply options provided via the command line to the TestHarness object parameters.
        """
        self.parameters().fromArgs(args, 'n_threads', 'timeout', 'max_failures', 'spec_file_blocks',
                                   'spec_file_names')

        # Call setup function from other top-level objects
        for obj in (self.getParam('controllers') or tuple()):
            obj._setup(args)

        for obj in (self.getParam('filters') or tuple()):
            obj._setup(args)

        obj = self.getParam('formatter')
        if obj is not None:
            obj._setup(args)

    def run(self):
        """
        Locate and execute the tests.
        """

        # Locate the tests to execute
        groups = moosetest.discover(os.getcwd(),
                                    self.getParam('controllers') or tuple(),
                                    self.getParam('spec_file_names'),
                                    self.getParam('spec_file_blocks'),
                                    plugin_dirs=os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split(),
                                    n_threads=self.getParam('n_threads'))

        # Execute the tests
        rcode = moosetest.run(groups,
                              self.getParam('controllers') or tuple(),
                              self.getParam('formatter'),
                              self.getParam('filters'),
                              n_threads=self.getParam('n_threads'),
                              timeout=self.getParam('timeout'),
                              max_fails=self.getParam('max_failures'))

        return rcode
