#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import sys
import glob
import pkgutil
import importlib
import inspect
from moosetools.base import MooseObject


class Factory(MooseObject):
    """
    The `Factory` object exists as a convenient way to create `base.MooseObject` objects that
    exist within a directory without requiring PYTHONPATH.

    It was originally designed to be utilized via the `factory.Parser` for creating objects from HIT
    input files.
    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('plugin_dirs',
                   vtype=str,
                   array=True,
                   doc="List of directories to search for plugins.")
        params.add('plugin_types',
                   array=True,
                   default=(MooseObject, ),
                   doc="The python type of the plugins to load.")
        return params

    def __init__(self, **kwargs):
        """
        Create `factory.Factory` object, the type of objects to load and the location can be
        provided via the keyword arguments, as defined in the `validParams` function.
        """
        MooseObject.__init__(self, **kwargs)
        self._registered_types = dict()

    def register(self, name, object_type):
        """
        Register the *name* to create an *object_type* object.

        In general, this should not be required to be called. The `load` method uses this method
        when looping through the supplied plugin directories.
        """
        otype = self._registered_types.get(name, None)
        if otype is not None:
            self.error(
                "The '{}' name is already associated with an object type of {}, it will not be registered again.",
                name,
                otype,
                stack_info=True)
        self._registered_types[name] = object_type

    def params(self, name):
        """
        Return the `InputParameters` object associated with the registered *name*.

        This operates by returning the object from the registered objects `validParam` function.
        """
        otype = self._getObjectType(name)
        if otype is not None:
            try:
                return otype.validParams()
            except Exception:
                self.exception("Failed to evaluate validParams function of '{}' object.", name)
        return None

    def create(self, _registered_name, *args, **kwargs):
        """
        Return an instance of an object associated with the registered *_registered_name*, the
        variable is named as such to avoid conflicts with the *\*args* and *\*\*kwargs* that
        are passed in to the object constructor.
        """
        otype = self._getObjectType(_registered_name)
        if otype is not None:
            try:
                return otype(*args, **kwargs)
            except Exception:
                self.exception("Failed to create '{}' object.", _registered_name)

        return None

    def load(self):
        """
        Loop through the supplied plugin directories and register the objects of the supplied type.

        This method should not raise exceptions. It reports all problems with logging errors. Prior
        to running it resets the error counts (see `base.MooseObject.reset()`). As such the
        `status` method (see `base.MooseObject.status()`) will return a non-zero code if an
        error occurred.
        """
        self.reset()
        plugin_types = self.getParam('plugin_types')

        # Import modules from the supplied directories
        plugin_dirs = self.getParam('plugin_dirs')
        if plugin_dirs is not None:
            for path in set(os.path.abspath(p) for p in plugin_dirs):
                if not os.path.isdir(path):
                    msg = "The supplied item, {}, to the 'plugin_dirs' parameter is not a directory."
                    self.error(msg, path)

                elif not os.path.isfile(os.path.join(path, '__init__.py')):
                    msg = "The supplied item, {}, to the 'plugin_dirs' parameter is not a python package (i.e., it does not contain an __init__.py file)."
                    self.error(msg, path)

                else:
                    d_name, m_name = path.rsplit(os.sep, maxsplit=1)
                    sys.path.append(d_name)
                    try:
                        importlib.import_module(m_name)
                    except Exception:
                        self.exception("Failed to load module '{}' in directory '{}'", m_name,
                                       d_name)

        # Load Classes that exist within the available modules
        def predicate(otype):
            return inspect.isclass(otype) and (otype not in plugin_types) and (
                otype.__name__ not in self._registered_types) and any(p in inspect.getmro(otype)
                                                                      for p in plugin_types)

        for module in list(sys.modules.values()):
            try:
                for name, otype in inspect.getmembers(module, predicate):
                    self.register(name, otype)
            except ModuleNotFoundError:
                continue

        return self.status()

    def _getObjectType(self, name):
        """
        Helper method for getting an object type registered with the given *name*.

        An error is logged if the supplied *name* is not associated with registered object type.
        """
        otype = self._registered_types.get(name, None)
        if otype is None:
            self.error("The supplied name '{}' is not associated with a registered type.", name)
        return otype

    def toString(self):
        """
        Output the available parameters for each of the registered object types to a string.
        """
        out = ''
        for name, otype in self._registered_types.items():
            params = self.params(name)
            if params is not None:
                out += '{}\n{} Parameters:\n{}\n'.format('=' * 80, name, '-' * 80)
                out += params.toString()
                out += '\n\n'
        return out

    def __str__(self):
        """
        Use `print` to output available parameters for each of the registered objects.
        """
        return self.toString()
