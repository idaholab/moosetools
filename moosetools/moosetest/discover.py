#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
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
    Custom `Factory` object that injects the `Controller` parameters as a sub-parameter within
    the objects (`Runner` or `Differ`) being created.
    """
    @staticmethod
    def validParams():
        params = factory.Factory.validParams()
        params.add(
            'controllers',
            vtype=Controller,
            array=True,
            doc="Controller objects for injecting into validParams of Runner/Differ objects.")
        return params

    def params(self, *args, **kwargs):
        """
        Creates the parameters with sub-parameters for each `Controller` object.
        """
        params = factory.Factory.params(self, *args, **kwargs)

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


class MooseTestWarehouse(factory.Warehouse):
    """
    Custom `Warehouse` that handles automatically adds `Differ` objects to the parent `Runner` as
    well as prefixes the name of the `Runner` with the test specification file.

    This warehouse is used within the the `_create_runners` function and is designed to operate
    on a per specification file basis. That is, a warehouse is created for each specification, with
    the resulting objects returned by the warehouse being the `Runner` objects.

    The first object added using the `append` method must be a `Runner` objects. All `Differ`
    objects are appended to the latest `Runner` object.
    """
    @staticmethod
    def validParams():
        params = factory.Warehouse.validParams()
        params.add('root_dir',
                   vtype=str,
                   required=True,
                   doc="The root directory for loading test specification files.")
        params.add('specfile', vtype=str, required=True, doc="The test specification file.")
        return params

    def append(self, obj):
        """
        Add `Runner` or `Differ` object, *obj*, to the warehouse.
        """
        if (len(self.objects) == 0) and isinstance(obj, Differ):
            msg = "The `Differ` object '{}' is being added without the existence of a `Runner`, which is not supported."
            self.critical(msg, obj.name())

        elif isinstance(obj, Differ):
            differs = list(self.objects[-1].getParam('differs') or set())
            differs.append(obj)
            self.objects[-1].parameters().setValue('differs', tuple(differs))

        else:
            base = obj.getParam('_hit_path').strip(os.sep)
            prefix = self.getParam('specfile').replace(self.getParam('root_dir'), '').strip(os.sep)
            obj.parameters().setValue('name', f"{prefix}:{base}")
            factory.Warehouse.append(self, obj)

        # Propagate construction errors of object
        if obj.status():
            msg = "The '{}' object produced error(s) during construction."
            self.critical(msg, obj.name())


def _create_runners(root_dir, filename, spec_file_blocks, obj_factory):
    """
    Return the `Runner` objects, with attached `Differ` objects, as defined in HIT file given in
    *filename*.

    The *root_dir* is the starting location provided to the `discover` function. Objects are
    only extracted from the HIT blocks in *spec_file_blocks*. The *obj_factory* is used to by the
    HIT parser to create the desired object type.
    """
    root = pyhit.load(filename)
    wh = MooseTestWarehouse(root_dir=root_dir, specfile=filename)
    parser = factory.Parser(obj_factory, wh)
    for node in moosetree.findall(root, func=lambda n: n.name in spec_file_blocks):
        parser.parse(
            filename,
            node,
        )
    return wh.objects, max(parser.status(), wh.status())


def discover(start,
             controllers,
             spec_file_names,
             spec_file_blocks,
             *,
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
                                   controllers=tuple(controllers or []))
    obj_factory.load()

    # Build the objects for each file
    with concurrent.futures.ThreadPoolExecutor(n_threads) as pool:
        futures = [
            pool.submit(_create_runners, start, filename, spec_file_blocks, obj_factory)
            for filename in spec_files
        ]

    # Raise an exception if an error occurred during parsing
    if any(f.result()[1] for f in futures):
        raise RuntimeError(
            "Errors occurred during parsing of specifications, refer to console output for messages."
        )

    return [f.result()[0] for f in futures]
