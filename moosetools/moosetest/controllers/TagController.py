#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import re
from moosetools.moosetest.base import Controller, Runner


class TagController(Controller):
    """
    A controller to dictate if an object should run based on allowable tags.
    """
    AUTO_BUILD = True

    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.setValue('prefix', 'tag')

        # TODO: add 'available_names' that is a config file option to limit what can be added to 'tag_names'


        params.add('active_tag_names',
                   array=True,
                   vtype=str,
                   doc="A list of tag names for limiting test execution.")
        return params

    @staticmethod
    def validObjectParams():
        """
        The "prefix" parameter for this object is not set, so this method is not used.

        See the `make_runner` and `make_differ` in the Runner.py and Differ.py modules.
        """
        params = Controller.validObjectParams()
        params.add('names', array=True, vtype=str, doc="The tag names that object is restricted.")
        return params

    @staticmethod
    def validCommandLineArguments(parser, params):
        parser.add_argument('--tags', type=str, nargs='+',
                            help="List of 'tag_names' to allow to execute.")

    def _setup(self, args):
        if args.tags:
            self.parameters().setValue('restricted_names', tuple(args.tags))

    def execute(self, obj, params):

        names = params.getValue('names') or set()
        active = self.getParam('active_tag_names') or set()

        if (not active) and names:
            msg = ("The execution of the test is limited to the '{}' tags, this test requires that "
                   "the 'active_tag_names' includes these tags.")
            self.debug(msg, names)
            self.skip(f"{names} not active")

        elif active and (not names):
            msg = ("The 'active_tag_names' is set to the '{}' tags, this test is not associated "
                   "with a tag.")
            self.debug(msg, active)
            sekf.skip(f"not {active}")

        elif not names.issubset(active):
            msg = ("The execution of the test is limited to the '{}' tags, but the test has the "
                   "tags {} that are not in this set.")
            self.debug(msg, active, names)
            self.skip("{} not in {}", names, active)
