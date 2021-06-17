#!/usr/bin/python
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
import re
import time
import logging
from moosetools import core
from moosetools import moosetree
from moosetools import pyhit
from .Factory import Factory
from .Warehouse import Warehouse


class Parser(base.MooseObject):
    """
    The `Parser` object is designed for creating instances of `base.MooseObject` objects with
    parameters populated from a HIT input file.
    """
    @staticmethod
    def validParams():
        params = base.MooseObject.validParams()
        params.add('_factory', private=True, required=True, vtype=Factory)
        params.add('_warehouse', private=True, required=True, vtype=(Warehouse, list))
        params.add('iteration_method',
                   vtype=moosetree.IterMethod,
                   default=moosetree.IterMethod.PRE_ORDER,
                   doc="Iteration method to utilize when traversing HIT tree.")
        return params

    def __init__(self, factory, warehouse, **kwargs):
        """
        The *factory* is a factory.Factory object that contains the available object to be
        constructed as dictated by the 'type' parameter in the HIT input file.

        The *warehouse* is factory.Warehouse object that the `Parser` injects the constructed
        objects.
        """
        kwargs.setdefault('_factory', factory)
        kwargs.setdefault('_warehouse', warehouse)
        base.MooseObject.__init__(self, **kwargs)

    @property
    def factory(self):
        """Return the `factory.Factory` object provided in the constructor."""
        return self.getParam('_factory')

    @property
    def warehouse(self):
        """Return the `factory.Warehouse` object provided in the constructor."""
        return self.getParam('_warehouse')

    def parse(self, filename, root=None):
        """
        Instantiate the `MooseObjects` in the supplied *filename* or in the `pyhit.Node` tree with
        a *root* node. If the *root* is supplied, the *filename* is only used for error reporting, if
        it is omitted then the file is opened to create the *root*.

        This method should not raise exceptions. It reports all problems with logging errors. Prior
        to running it resets the error counts (see `base.MooseObject.reset()`). As such the
        `status` method (see `base.MooseObject.status()`) will return a non-zero code if an
        error occurred.
        """
        if root is None:
            if not os.path.isfile(filename):
                self.error("The filename '{}' does not exist.".format(filename))
                return 1
            try:
                root = pyhit.load(filename)
            except Exception as err:
                self.exception("Failed to load filename with pyhit: {}", filename)
                return 1

        # Iterate of all nodes with "type = ..."
        paths = set()
        for node in moosetree.findall(root,
                                      func=lambda n: 'type' in n,
                                      method=self.getParam('iteration_method')):
            self._checkDuplicates(filename, paths, node)
            self._parseNode(filename, node)
        return self.status()

    def _parseNode(self, filename, node):
        """
        Instantiate a `base.MooseObject` for a supplied `pyhit.Node`.

        The *filename* is provided for error reporting. The *node* is a `pyhit.Node` that should
        contain a "type" parameter that gives the type of object to be constructed. This type must
        be registered with the `factory.Factory` supplied in the `Parser` constructor.

        When an object is created, it is added to the `factory.Warehouse` object supplied in the
        `Parser` constructor.
        """
        otype = node.get('type', None)
        if otype is None:
            msg = "{}:{}\nMissing 'type' in block '{}'"
            self.error(msg, filename, node.line(-1), node.fullpath)
            return

        params = self.factory.params(otype)
        if params is None:
            msg = "{}:{}\nFailed to extract parameters from '{}' object in block '{}'"
            self.error(msg, filename, node.line(-1), otype, node.fullpath, stack_info=True)
            return

        # Set the object name to that of the block (e.g., [object])
        params.setValue('name', node.name)
        params.add('_hit_path', default=node.fullpath, private=True)
        params.add('_hit_filename', default=filename, private=True)

        # Update the Parameters with the HIT node
        self.setParameters(params, filename, node, otype)

        # Attempt to build the object and update warehouse
        obj = self.factory.create(otype, params)
        if obj is None:
            msg = "{}:{}\nFailed to create object of type '{}' in block '{}'"
            self.error(msg, filename, node.line(-1), otype, node.fullpath, stack_info=True)
        else:
            self.warehouse.append(obj)

    def _checkDuplicates(self, filename, paths, node):
        """
        Check for duplicate blocks and/or parameters.

        The *filename* is provided for error reporting. The *paths* is a `set` provided that
        contains the existing HIT paths for blocks and parameters. The block and parameters from
        the supplied `pyhit.Node` object, *node*, are checked to exist in *paths*. If they are in
        set an error is logged. If they are not, the *paths* are updated to include the syntax from
        *node*. Refer to `parse` for use.
        """

        if node.fullpath in paths:
            msg = "{}:{}\Duplicate section '{}'".format(filename, node.line(-1), node.fullpath)
            self.error(msg)
        else:
            paths.add(node.fullpath)

        for key, _ in node.params():
            fullparam = os.path.join(node.fullpath, key)
            if fullparam in paths:
                msg = "{}:{}\Duplicate parameter '{}'".format(filename, node.line(key, -1),
                                                              fullparam)
                self.error(msg)
            else:
                paths.add(fullparam)

    def setParameters(self, params, filename, node, otype):
        """
        Update the `InputParameters` object in *params* with the key/value pairs in *node*,
        which is a `pyhit.Node` object.
        """
        # Loop through all the parameters in the hit file
        for key, value in node.params():
            if key == 'type':
                continue

            if key not in params:
                msg = "{}:{}\nThe parameter '{}' does not exist in '{}' object parameters."
                self.error(msg, filename, node.line(key, -1), key, otype)
                continue

            # Attempt to convert the string value supplied by the HIT parser to types as given
            # in the `InputParameters` object returned by `validParams` function
            param = params.parameter(key)
            vtype = param.vtype
            if param.array or ((vtype is not None) and (type(value) not in vtype)):
                new_value = Parser._getValueFromStr(vtype, str(value), param.array)
                if new_value is None:
                    msg = "{}:{}\nFailed to convert '{}' to the correct type(s) of '{}' for '{}' parameter."
                    self.error(msg, filename, node.line(key, -1), new_value, vtype, key)
                value = new_value

            if value is not None:
                params.setValue(key, value)

    @staticmethod
    def _getValueFromStr(vtypes, str_value, array):
        """
        Attempts to convert a string input *str_value* to the correct type, as defined by 'vtype'.

        This method is used by the factor.Parser to convert data from HIT files to correct types.
        """
        assert isinstance(vtypes, tuple) and all(
            isinstance(v, type) for v in vtypes), "'vtypes' must be a tuple of types"
        assert isinstance(
            str_value,
            str), "'str_value' must be a string, a type of {} provided in value {}".format(
                type, str_value, repr(str_value))
        assert isinstance(array, bool), "'array' must be a bool"

        def convert(val, vtypes):
            out = None
            for vtype in vtypes:
                if vtype is bool:
                    if val.lower() in ('0', '1', 'true', 'false'):
                        out = val.lower() in ('1', 'true')
                        break
                else:
                    try:
                        out = vtype(val)
                        break
                    except ValueError:
                        pass

            return out

        if array:
            value = tuple(convert(v, vtypes) for v in re.split(r' +', str_value))
            if any(v is None for v in value): value = None
        else:
            value = convert(str_value, vtypes)

        return value
