#* This file is part of the MOOSE framework
#* https://www.mooseframework.org
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html
import os
import sys
import glob
import pkgutil
import importlib
import inspect
from base import MooseObject

class Factory(MooseObject):
    """


    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.add('plugin_dirs', default=(os.path.join(os.getcwd(), 'plugins'),), vtype=str, array=True,
                   verify=(lambda dirs: all(os.path.isdir(d) for d in dirs),
                           "Supplied plugin directories must exist."),
                   doc="List of directories to search for plugins.")
        params.add('plugin_type', default=MooseObject, doc="The python type of the plugins to load.")
        return params

    def __init__(self, **kwargs):
        MooseObject.__init__(self, **kwargs)
        self._registered_types = dict()
        self.load()

    def register(self, name, object_type):
        otype = self._registered_types.get(name, None)
        if otype is not None:
            self.warning("The '{}' name is already associated with an object type of {}, it will not be registered again.", name, otype, stack_info=True)
        self._registered_types[name] = object_type

    def create(self, _registered_name, *args, **kwargs):
        otype = self._registered_types.get(_registered_name, None)
        if otype is None:
            raise base.MooseException("The supplied name '{}' is not associated with a registered type.")
        return self._registered_types[_registered_name](*args, **kwargs)

    def load(self):
        plugin_dirs = self.getParam('plugin_dirs')
        plugin_type = self.getParam('plugin_type')

        for info in pkgutil.iter_modules(plugin_dirs):
            loader = info.module_finder.find_module(info.name)
            try:
                module = loader.load_module()
            except Exception:
                self.exception("Failed to load module '{}' in file '{}'", info.name, info.module_finder.path)
                continue

            for name, otype in inspect.getmembers(module):
                if inspect.isclass(otype) and (plugin_type in inspect.getmro(otype)) and (name not in self._registered_types):
                    self.register(name, otype)

    def __str__(self):
        out = ''
        for name, otype in self._registered_types.items():
            params = otype.validParams()
            params.set('type', otype.__name__)
            out += str(params)

        return out

    """
    def printDump(self, root_node_name):
        print("[" + root_node_name + "]")

        for name, object in sorted(self.objects.items()):
            print("  [./" + name + "]")

            params = self.validParams(name)

            for key in sorted(params.desc):
                default = ''
                if params.isValid(key):
                    the_param = params[key]
                    if type(the_param) == list:
                        default = "'" + " ".join(the_param) + "'"
                    else:
                        default = str(the_param)

                print("%4s%-30s = %-30s # %s" % ('', key, default, params.getDescription(key)))
            print("  [../]\n")
        print("[]")


    def printYaml(self, root_node_name):
        print("**START YAML DATA**")
        print("- name: /" + root_node_name)
        print("  description: !!str")
        print("  type:")
        print("  parameters:")
        print("  subblocks:")

        for name, object in self.objects.items():
            print("  - name: /" + root_node_name + "/ + name")
            print("    description:")
            print("    type:")
            print("    parameters:")

            params = self.validParams(name)
            for key in params.valid:
                required = 'No'
                if params.isRequired(key):
                    required = 'Yes'
                default = ''
                if params.isValid(key):
                    default = str(params[key])

                print("    - name: " + key)
                print("      required: " + required)
                print("      default: !!str " + default)
                print("      description: |")
                print("        " + params.getDescription(key))

        print("**END YAML DATA**")
    """
