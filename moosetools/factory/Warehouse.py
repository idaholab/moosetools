#!/usr/bin/python
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

from moosetools import core


class Warehouse(core.MooseObject):
    """
    The `Warehouse` object is a basic storage container for `core.MooseObject` objects.

    It was originally designed to be utilized via the `factory.Parser` for storing objects from HIT
    input files.
    """
    @staticmethod
    def validParams():
        params = core.MooseObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        core.MooseObject.__init__(self, *args, **kwargs)
        self.__objects = list()

    def __len__(self):
        """
        Return the number of stored objects for `len` builtin.
        """
        return len(self.__objects)

    def __iter__(self):
        """
        Allow the objects to be iterated directly from `Warehouse` instance.
        """
        yield from self.__objects

    @property
    def objects(self):
        return self.__objects

    def append(self, obj):
        """
        Append the supplied *obj* to the list of objects stored.
        """
        self.__objects.append(obj)

    def clear(self):
        """
        Clear the list of stored objects.
        """
        self.__objects.clear()
