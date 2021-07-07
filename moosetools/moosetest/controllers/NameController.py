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


class NameController(Controller):
    """
    A controller to dictate if an object should run based on the name.
    """
    AUTO_BUILD = True

    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.add('remove_if_text_in_name',
                   vtype=str,
                   doc="Remove test if the supplied text is in the object name.")
        params.add('remove_if_text_not_in_name',
                   vtype=str,
                   doc="Remove test if the supplied text is not in the object name.")
        params.add('remove_if_re_match_name',
                   vtype=str,
                   doc="Remove test if the supplied regular expression matches the object name.")
        params.add(
            'remove_if_re_not_match_name',
            vtype=str,
            doc="Remove test if the supplied regular expression does not match the object name.")
        params.add('re_flags',
                   vtype=str,
                   array=True,
                   default=('MULTILINE', 'DOTALL', 'UNICODE'),
                   allow=('MULTILINE', 'DOTALL', 'UNICODE', 'IGNORECASE', 'VERBOSE', 'LOCALE',
                          'DEBUG', 'ASCII'),
                   doc="The names of the flags to pass to regular expression `match` function.")
        params.add('blocks',
                   vtype=str,
                   array=True,
                   doc=("The block names to allow when the test name is formatted as in the "
                        "'block_re' parameter."))
        params.add(
            'block_re',
            vtype=str,
            default="(?P<prefix>.*?):(?P<block>.*?)/(?P<name>.*?)",
            doc=("The regular expression used for determine the 'block name', the expression "
                 "must contain a 'block' group. By default the form <prefix>:<block>/<name>. "
                 "When test names are populated by `moosetest.discover` via HIT files the "
                 "block name is the top-level block (e.g., [Tests]) of the file. The "
                 "parameter is only applied to `Runner` object."))
        return params

    @staticmethod
    def validObjectParams():
        """
        The "prefix" parameter for this object is not set, so this method is not used.

        See the `make_runner` and `make_differ` in the Runner.py and Differ.py modules.
        """
        return None

    def execute(self, obj, params):

        # TEXT
        text_in = self.getParam('remove_if_text_in_name')
        if (text_in is not None) and (text_in in obj.name()):
            self.debug(
                "The text in 'remove_if_text_in_name', '{}', was located in the object name '{}'",
                text_in, obj.name())
            self.remove('remove_if_text_in_name')

        text_not_in = self.getParam('remove_if_text_not_in_name')
        if (text_not_in is not None) and (text_not_in not in obj.name()):
            self.debug(
                "The text in 'remove_if_text_not_in_name', '{}', was not located in the object name '{}'",
                text_in, obj.name())
            self.remove('remove_if_text_not_in_name')

        # RE
        flags = 0
        for flag in self.getParam('re_flags'):
            flags |= eval(f're.{flag}')

        re_match = self.getParam('remove_if_re_match_name')
        if re_match is not None:
            match = re.search(re_match, obj.name(), flags=flags)
            if match:
                self.debug(
                    "The regular expression of 'remove_if_re_match_name', '{}', matches the object name '{}'",
                    text_in, obj.name())
                self.remove('remove_if_re_match_name')

        re_not_match = self.getParam('remove_if_re_not_match_name')
        if re_not_match is not None:
            match = re.search(re_not_match, obj.name(), flags=flags)
            if not match:
                self.debug(
                    "The regular expression of 'remove_if_re_not_match_name', '{}', does not match the object name '{}'",
                    text_in, obj.name())
                self.remove('remove_if_re_not_match_name')

        # BLOCKS
        blocks = self.getParam('blocks')
        if isinstance(obj, Runner) and (blocks is not None):
            match = re.search(self.getParam('block_re'), obj.name())
            if not match:
                msg = "A block name was not located in the test with name '{}', the test name must be in <prefix>:<block>/<name> format."
                self.error(msg, obj.name())
            elif 'block' not in match.groupdict():
                self.error(
                    "The 'block_re' must be a regular expression that includes a group with name 'block'."
                )
            elif match.group('block') not in blocks:
                msg = "The block name for the test '{}' is '{}', which is not in the allowable block names '{}'."
                self.debug(msg, obj.name(), match.group('block'), blocks)
                self.remove("'{}' not in {}", match.group('block'), blocks)
