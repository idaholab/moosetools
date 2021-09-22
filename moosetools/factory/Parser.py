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
import enum
import inspect
import multiprocessing
import math
import itertools
from moosetools import core
from moosetools import moosetree
from moosetools import pyhit
from moosetools import mooseutils
from .Factory import Factory


class Parser(core.MooseObject):
    """
    The `Parser` object is designed for creating instances of `core.MooseObject` objects with
    parameters populated from a HIT input file.
    """
    @staticmethod
    def validParams():
        params = core.MooseObject.validParams()
        params.add('_factory', private=True, required=True, vtype=Factory)
        params.add('iteration_method',
                   vtype=moosetree.IterMethod,
                   default=moosetree.IterMethod.PRE_ORDER,
                   doc="Iteration method to utilize when traversing HIT tree.")
        return params

    def __init__(self, factory, **kwargs):
        """
        The *factory* is a factory.Factory object that contains the available object to be
        constructed as dictated by the 'type' parameter in the HIT input file.
        """
        kwargs.setdefault('_factory', factory)
        core.MooseObject.__init__(self, **kwargs)

    @property
    def factory(self):
        """Return the `factory.Factory` object provided in the constructor."""
        return self.getParam('_factory')

    def parse(self, filenames, *, max_workers=None, chunksize=None):
        """
        Instantiate the `MooseObjects` in the supplied *filenames*.
        """
        if chunksize is None:
            chunksize = math.ceil(len(filenames) / (max_workers or os.cpu_count()))
        return Parser._parseWithMultiprocessingPool(self, filenames, max_workers, chunksize)

    def parseFile(self, filename):
        """
        Instantiate the `MooseObjects` in the supplied *filename*.

        This method should not raise exceptions. It reports all problems with logging errors. Prior
        to running it resets the error counts (see `core.MooseObject.reset()`). As such the
        `status` method (see `core.MooseObject.status()`) will return a non-zero code if an
        error occurred.
        """
        if not os.path.isfile(filename):
            self.error("The file '{}' does not exist.".format(filename))
            return None

        with open(filename, 'r') as fid:
            content = fid.read()

        return self.parseText(filename, content)

    def parseText(self, filename, content):
        """
        Instantiate the `MooseObjects` supplied in the *content* string.

        The *filename* is provided for error reporting.
        """
        try:
            root = pyhit.parse(content, filename=filename)
        except Exception as err:
            self.exception("Failed to parse file '{}' with pyhit.", filename)
            return None

        # Iterate of all nodes with "type = ..."
        objects = list()
        paths = set()
        for node in moosetree.findall(root,
                                      func=lambda n: 'type' in n,
                                      method=self.getParam('iteration_method')):
            self._checkDuplicates(filename, paths, node)
            objects.append(self.parseNode(filename, node))

        return objects

    def parseNode(self, filename, node):
        """
        Instantiate a `core.MooseObject` for a supplied `pyhit.Node`.

        The *filename* is provided for error reporting. The *node* is a `pyhit.Node` that should
        contain a "type" parameter that gives the type of object to be constructed. This type must
        be registered with the `factory.Factory` supplied in the `Parser` constructor.
        """
        otype = node.get('type', None)
        if otype is None:
            msg = "{}:{}\nMissing 'type' in block '{}'"
            self.error(msg, filename, node.line(-1), node.fullpath)
            return None

        params = self.factory.params(otype)
        if params is None:
            msg = "{}:{}\nFailed to extract parameters from '{}' object in block '{}'"
            self.error(msg, filename, node.line(-1), otype, node.fullpath, stack_info=True)
            return None

        # Set the object name to that of the block (e.g., [object])
        params.setValue('name', node.name)
        params.setValue('_hit_path', node.fullpath)
        params.setValue('_hit_filename', filename)

        # Update the Parameters with the HIT node
        self.setParameters(params, filename, node, otype)

        # Attempt to build the object
        obj = self.factory.create(otype, params)
        if obj is None:
            msg = "{}:{}\nFailed to create object of type '{}' in block '{}'"
            self.error(msg, filename, node.line(-1), otype, node.fullpath, stack_info=True)

        return obj

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
            if (param.array and (vtype is not None)) or ((vtype is not None) and (type(value) not in vtype)):
                try:
                    new_value = Parser._getValueFromStr(vtype, str(value), param.array)
                except:
                    msg = "{}:{}\nAn Exception occurred trying to convert '{}' to the correct type(s) of '{}' for '{}' parameter."
                    self.exception(msg, filename, node.line(key, -1), value, vtype, key)
                    raise

                if new_value is None:
                    msg = "{}:{}\nFailed to convert '{}' to the correct type(s) of '{}' for '{}' parameter."
                    self.error(msg, filename, node.line(key, -1), value, vtype, key)
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

                elif enum.Enum in inspect.getmro(vtype):
                    try:
                        out = vtype[val]
                        break
                    except KeyError:
                        pass
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

    @staticmethod
    def _parseWithMultiprocessingPool(parser, filenames, max_workers, chunksize):
        ctx = multiprocessing.get_context('fork')
        pool = multiprocessing.pool.Pool(max_workers, context=ctx)
        results = pool.map_async(parser.parseFile, filenames, chunksize=chunksize)
        pool.close()
        return results.get()
