import io
import platform
import logging
from moosetools.base import MooseObject

class Differ(MooseObject):
    """

    """

    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        params.add('_runner_name', vtype=str, private=True)
        return params

    def __init__(self, params=None, controllers=None, **kwargs):
        if params is None: params = getattr(self.__class__, 'validParams')()
        for ctrl in controllers:
            params.add(ctrl.getParam('prefix'), default=ctrl.validObjectParams())
        MooseObject.__init__(self, params, **kwargs)

    def execute(self, rcode, stdout, stderr):
        raise NotImplementedError()
