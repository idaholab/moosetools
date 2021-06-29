import os
import logging
import argparse
import inspect
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

        # These are not intended to be set by the HIT configuration file
        params.add('controllers',
                   private=True,
                   vtype=Controller,
                   array=True,
                   doc="The `Controller` object to utilize when creating `Runner` and `Differ` objects.")
        params.add('formatter',
                   default=moosetest.formatters.BasicFormatter(),
                   private=True,
                   vtype=Formatter,
                   doc="The `Formatter` object to utilize for outputting test information.")

        return params

    @staticmethod
    def createCommandLineParser(params):
        parser = argparse.ArgumentParser(description="Testing system inspired by MOOSE",
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--config', default=os.getcwd(), type=str,
                            help="A configuration file or directory. If a directory is provided a " \
                            "'.moosetest' file is searched up the directory tree beginning with " \
                            "the current working directory.")

        p = params.parameter('n_threads')
        parser.add_argument('--n-threads', type=int, default=p.default, help=p.doc)

        p = params.parameter('timeout')
        parser.add_argument('--timeout', type=float, default=p.default, help=p.doc)

        p = params.parameter('max_failures')
        parser.add_argument('--max-failures', type=int, default=p.default, help=p.doc)

        p = params.parameter('spec_file_blocks')
        parser.add_argument('--spec-file-blocks', type=str, nargs='+', default=p.default, help=p.doc)

        p = params.parameter('spec_file_names')
        parser.add_argument('--spec-file-names', type=str, nargs='+', default=p.default, help=p.doc)

        # Options for running a demo with the fuzzer
        subparsers = parser.add_subparsers(dest='fuzzer')
        fuzzer = subparsers.add_parser("fuzzer", formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                       description="Run a demonstration with random tests using the `moosetest.fuzzer` tool.")
        signature = inspect.signature(moosetest.fuzzer)
        actions = dict()
        for key, value in signature.parameters.items():
            vsize = len(value.default) if hasattr(value.default, '__len__') else 1
            vtype = type(value.default) if vsize == 1 else type(value.default[0])
            meta = ('MIN', 'MAX') if vsize == 2 else 'PROB'
            actions[key] = fuzzer.add_argument(f'--{key}', dest=f'fuzzer_{key}', metavar=meta, nargs=vsize, type=vtype, default=value.default)

        actions['timeout'].help = "Set the range of the possible timeout in seconds."
        actions['max_fails'].help = "Set the range of the possible number of a maximum number of failures."
        actions['progress_interval'].help = "Set the range of the possible progress update interval."
        actions['group_num'].help = "Set the range of the possible number of test groups."
        actions['group_name_len'].help = "Set the range of the possible group name length."
        actions['controller_num'].help = "Set the range of the possible number of Controller objects."
        actions['controller_skip'].help = "Set the probability (0 to 1) of a Controller object causing a skip."
        actions['controller_raise'].help = "Set the probability (0 to 1) of a Controller object causing an exception."
        actions['controller_error'].help = "Set the probability (0 to 1) of a Controller object causing an error."
        actions['differ_num'].help = "Set the range of the possible number of Differ objects."
        actions['differ_raise'].help = "Set the probability (0 to 1) of a Differ object causing an exception."
        actions['differ_error'].help = "Set the probability (0 to 1) of a Differ object causing an error."
        actions['differ_fatal'].help = "Set the probability (0 to 1) of a Differ object causing an fatal error."
        actions['differ_platform'].help = "Set the probability (0 to 1) of a Differ object being limited to a random OS platform."
        actions['differ_name_len'].help = "Set the range of the possible Differ object name length."
        actions['runner_num'].help = "Set the range of the possible number of Runner objects."
        actions['runner_raise'].help = "Set the probability (0 to 1) of a Runner object causing an exception."
        actions['runner_error'].help = "Set the probability (0 to 1) of a Runner object causing an error."
        actions['runner_fatal'].help = "Set the probability (0 to 1) of a Runner object causing an fatal error."
        actions['runner_platform'].help = "Set the probability (0 to 1) of a Runner object being limited to a random OS platform."
        actions['runner_name_len'].help = "Set the range of the possible Runner object name length."
        actions['requires_error'].help = "Set the probability (0 to 1) that a Runner object includes an invalid 'requires' name."
        actions['requires_use'].help = "Set the probability (0 to 1) that a Runner will include a 'requires' list."
        return parser

    def __init__(self, *args, **kwargs):
        core.MooseObject.__init__(self, *args, **kwargs)
        self.__fuzzer = None

    def parse(self):
        """
        Initialize the object by processing and applying the command line arguments.

        This needs to be a stand-alone function, because doing this within the constructor
        automatically parse arguments, which might not be desired.
        """
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

        if args.fuzzer is not None:
            self.__fuzzer = dict()
            for key, value in vars(args).items():
                if key.startswith('fuzzer_'):
                    self.__fuzzer[key[7:]] = value

    def run(self):
        """
        Locate and execute the tests.

        If the 'fuzzer' arguments are populated then a demonstration using the `moosetest.fuzzer`
        is executed without locating and executing any tests.
        """

        # Run a demo, if the 'fuzzer' sub-command is supplied
        if self.__fuzzer is not None:
            return moosetest.fuzzer(**self.__fuzzer)

        # Locate the tests to execute
        groups = moosetest.discover(os.getcwd(),
                                     self.getParam('spec_file_names'),
                                     self.getParam('spec_file_blocks'),
                                     os.getenv('MOOSETOOLS_PLUGIN_DIRS', '').split(),
                                     self.getParam('controllers') or tuple(),
                                     self.getParam('n_threads'))

        # Execute the tests
        rcode = moosetest.run(groups,
                              self.getParam('controllers') or tuple(),
                              self.getParam('formatter'),
                              self.getParam('n_threads'),
                              self.getParam('timeout'),
                              self.getParam('max_failures'))

        return rcode
