#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import inspect
import importlib
import concurrent.futures
from moosetools import moosetree
from moosetools import pyhit
from moosetools import factory
from moosetools.moosetest.base import Controller, TestCase
from moosetools.moosetest.base import Runner, Differ

# TODO:
# - Perform factory.status() checks() and make sure error messages are usable


class MooseTestFactory(factory.Factory):
    """
    Custom `Factory` object to handle specifics of parameters for `moosetest`.

    1. injects the `Controller` parameters as a sub-parameter within the objects (`Runner`
       or `Differ`) being created.
    2. apply "default" parameters for objects (e.g., parameters set in the [Defaults] block of the
       main configuration file, see `moosetest.main`).
    """
    @staticmethod
    def validParams():
        params = factory.Factory.validParams()
        params.add(
            'controllers',
            vtype=Controller,
            array=True,
            doc="Controller objects for injecting into validParams of Runner/Differ objects.")
        params.add('object_defaults',
                   vtype=dict,
                   doc=("Default object settings for `Runner` and `Differ` objects, where the key "
                        "is the registered object name (e.g., `RunCommand`) and the value is a "
                        "`dict` of parameter names and values."))
        return params

    def params(self, name):
        """
        Creates the parameters with sub-parameters for each `Controller` object.
        """
        params = factory.Factory.params(self, name)

        # Add defaults, if any
        object_defaults = self.getParam('object_defaults')
        if object_defaults is not None:
            otype = self._getObjectType(name)
            for obj_type, obj_params in object_defaults.items():
                obj_names = set(['{}.{}'.format(otype.__module__, otype.__name__)] +
                                [p.__module__ for p in inspect.getmro(otype)])
                if obj_type in obj_names:
                    for key, value in obj_params.items():
                        param = params.parameter(key)
                        if param.vtype and isinstance(value, str):
                            value = factory.Parser._getValueFromStr(param.vtype, value, param.array)
                        params.setValue(key, value)

        # Add the controllers, this allows Runner objects to pragmatically add a Differ object
        params.add('_controllers', default=self.getParam('controllers'), private=True)

        # Add the Controller object parameters with the correct prefix from the Controller object
        for controller in self.getParam('controllers') or list():
            if controller.isParamValid('prefix'):
                params.add(
                    controller.getParam('prefix'),
                    default=controller.validObjectParams(),
                    doc="Parameters for determining execute state from the '{}' control object.".
                    format(type(controller).__name__))
        return params

    def create(self, otype, params):

        # Set "working_dir", if not set by the user, to location of HIT file that created the object
        if ('working_dir' in params) and (not params.isSetByUser('working_dir')):
            params.setValue('working_dir', os.path.dirname(params.getValue('_hit_filename')))

        return factory.Factory.create(self, otype, params)


def discover(start,
             controllers,
             spec_file_names,
             *,
             object_defaults=None,
             plugin_dirs=None,
             n_threads=None):
    """
    Return groups of `Runner` objects to execute by recursively searching from the *start* directory.

    The directories are searched for file names that match those in the  *spec_file_names*
    (e.g., ['tests', 'examples']).

    The types of objects created must have a parent class of `Runner` or `Differ` and able to loaded
    from the loaded python paths or within the paths provided in *plugin_dirs*. When the objects
    are created the parameters from all supplied `Controller` objects in *controllers*.

    The parsing of the files occurs within a thread pool, with the given number of threads provided
    in *n_threads*. If not provide the default is used from `concurrent.futures.ThreadPoolExecutor`.
    """
    # Create a list of files
    spec_files = list()
    for root, _, files in os.walk(start):
        spec_files += [os.path.join(root, f) for f in files if f in spec_file_names]

    # Factory for creating the test objects
    obj_factory = MooseTestFactory(plugin_dirs=tuple(plugin_dirs),
                                   plugin_types=(Runner, Differ),
                                   controllers=tuple(controllers or []),
                                   object_defaults=object_defaults or dict())
    obj_factory.load()

    # Build objects
    obj_parser = factory.Parser(obj_factory)
    groups = obj_parser.parse(spec_files)

    # Add Differs to Runner
    runners = list()  # all Runner objects
    for objects in groups:
        differs = list()  # differs objects to add to a Runner
        local = list()
        for obj in objects:
            if isinstance(obj, Differ):
                differs.append(obj)
            else:
                if differs:
                    obj.parameters().setValue('differs', tuple(differs))
                base = obj.getParam('_hit_path').strip(os.sep)
                prefix = obj.getParam('_hit_filename').replace(start, '').strip(os.sep)
                obj.parameters().setValue('name', f"{prefix}:{base}")
                differs.clear()
                local.append(obj)
        runners.append(local)

    return runners
