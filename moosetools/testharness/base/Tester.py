import io
import platform
import logging
from .MooseTestObject import MooseTestObject

class Tester(MooseTestObject):
    """

    """

    @staticmethod
    def validParams():
        params = MooseTestObject.validParams()
        return params

    def __init__(self, *args, **kwargs):
        MooseTestObject.__init__(self, *args, **kwargs)

    def execute(self, returncode, output):
        raise NotImplementedError()
