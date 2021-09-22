#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import re
#import dataclasses # TODO: use when python 3.6 is dropped
import typing
import packaging.version
from moosetools import mooseutils
from moosetools.parameters import InputParameters
from moosetools.moosetest.base import Controller


# TODO: Use this when python 3.6 is dropped
#@dataclasses.dataclass
#class AutotoolsConfigItem(object):
#    """
#    Helper class for for defining configuration items as meta data within object parameters.
#    """
#    key: str = None  # name of the item in the configuration (e.g., MOOSE_SPARSE_AD)
#    default: typing.Any = None  # default raw value if the value is not within the configuration file
#    mapping: dict = None  # mapping from configuration file values to parameter values
class AutotoolsConfigItem(object):
    """
    Helper class for for defining configuration items as meta data within object parameters.
    """
    def __init__(self, key, default, mapping):
        self.key = key
        self.default = default
        self.mapping = mapping


class AutotoolsConfigController(Controller):
    """
    A base `Controller` to dictate if an object should run based on Autotools configuration file(s).
    """
    RE_DEFINE = re.compile(r"#define\s+(?P<key>\S+)\s+(?P<value>.*?)#endif", flags=re.DOTALL)

    OPERATOR_PREFIX_RE = re.compile(r'(?P<operator><=|>=|!=|==|!|<|>)(?P<value>.*)')

    @staticmethod
    def validParams():
        params = Controller.validParams()
        params.add('config_files',
                   vtype=str,
                   mutable=False,
                   array=True,
                   verify=(AutotoolsConfigController.isFile,
                           "The supplied file name(s) must exist."),
                   doc="The file(s) to read for the current application configuration.")
        return params

    @staticmethod
    def validObjectParams():
        """
        Return an `parameters.InputParameters` object to be added to a sub-parameter of an object
        with the name given in the "prefix" parameter
        """
        params = Controller.validObjectParams()
        return params

    @staticmethod
    def isFile(config_files):
        """
        Return True if the all the file names in *config_files* exist.
        """
        return all(os.path.isfile(mooseutils.eval_path(f)) for f in config_files)

    @staticmethod
    def loadConfig(filename):
        """
        Return a `dict` containing key/value pairs from supplied Autotools configure .h file.

        For example, the following has a key of "MOOSE_GLOBAL_AD_INDEXING" with a value of 1.

        ```c++
        #ifndef MOOSE_GLOBAL_AD_INDEXING
        #define MOOSE_GLOBAL_AD_INDEXING 1
        #endif
        ```
        """
        if not os.path.isfile(filename):
            raise IOError(f"The supplied file name, '{filename}', does not exist.")

        with open(filename, 'r') as fid:
            content = fid.read()

        output = dict()
        for match in AutotoolsConfigController.RE_DEFINE.finditer(content):
            output[match.group('key')] = match.group('value').strip(' \n"\'')
        return output

    def __init__(self, *args, **kwargs):
        Controller.__init__(self, *args, **kwargs)

        # Build a map of configure options from the supplied files
        self.__config_items = dict()
        for config_file in self.getParam('config_files') or set():
            self.__config_items.update(
                AutotoolsConfigController.loadConfig(mooseutils.eval_path(config_file)))

    def getConfigItem(self, params, name):
        """
        Return the mapped and raw configuration file values.

        In general, this function should not be called. It is called automatically by the `execute`
        method of this object.
        """
        item = params.getUserData(name)
        if item is None:
            raise RuntimeError(
                f"The parameter '{name}' does not contain a `AutotoolsConfigItem` object within the parameter 'user_data'."
            )

        raw_value = self.__config_items.get(item.key, item.default)
        mapped_value = item.mapping.get(raw_value, None) if hasattr(
            item.mapping, 'get') else item.mapping(raw_value)

        if mapped_value is None:
            msg = "The value of '{}' in the loaded file does not have a registered value in the mapping for '{}'. The available mapping values are: {}"
            raise RuntimeError(msg.format(name, raw_value, ', '.join(item.mapping.keys())))

        return mapped_value, raw_value, item.key

    def checkConfig(self, params, param_name):
        """
        Inspect that the parameter *param_name* within *params* matches the current configuration.

        In general, this function should not be called. It is called automatically by the `execute`
        method of this object.
        """
        param_value = params.getValue(param_name)
        if param_value is not None:
            mapped_value, raw_value, raw_name = self.getConfigItem(params, param_name)
            result, expression = AutotoolsConfigController._compare(param_value, mapped_value)
            if not result:
                msg = "The application is configured with '{}' equal to '{}', which maps to a value of '{}'. However, the associated '{}' parameter for this test requires '{}'."
                self.info(msg, raw_name, raw_value, mapped_value, param_name, param_value)
                self.skip(f"{raw_name}: not {expression}")

    def execute(self, obj, params):
        """
        Inspect the *params* added by this `Controller` for the supplied *obj*.

        For each parameter added by this object to the *obj*, if the parameter "user_data" is a
        `AutotoolsConfigItem` then check that values within the supplied configuration files match
        with the associated input parameter.
        """
        for key in params.keys():
            user_data = params.getUserData(key)
            if isinstance(user_data, AutotoolsConfigItem):
                self.checkConfig(params, key)

    @staticmethod
    def _compare(value0, value1):
        """
        Perform case insensitive comparisons with operator prefixes.
        """
        v0 = value0.casefold() if isinstance(value0, str) else value0
        v1 = value1.casefold() if isinstance(value1, str) else value1

        operator = '=='
        if isinstance(v1, str):
            match = AutotoolsConfigController.OPERATOR_PREFIX_RE.match(v1)
            if match:
                operator = match.group('operator')
                v1 = match.group('value')
                if operator == '!': operator = '!='

        expression = f'{repr(v0)}{operator}{repr(v1)}'
        return eval(expression), expression


    @staticmethod
    def _compareVersions(value0, value1):
        """
        Perform comparisons between two version strings.
        """
        assert isinstance(value0, str), "'value0' must be a 'str'"
        assert isinstance(value1, str), "'value1' must be a 'str'"

        v0 = packaging.version.parse(value0)

        operator = '=='
        match = AutotoolsConfigController.OPERATOR_PREFIX_RE.match(value1)
        if match:
            operator = match.group('operator')
            v1 = packaging.version.parse(match.group('value'))
            if operator == '!': operator = '!='
        else:
            v1 = packaging.version.parse(value1)

        return eval(f'v0{operator}v1'), f'{str(v0)}{operator}{str(v1)}'
