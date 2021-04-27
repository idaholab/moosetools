import uuid
import enum
from moosetools.base import MooseObject
from .Differ import Differ

       # return self



class Runner(MooseObject):
    """

    """
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        params.setRequired('name', True)
        params.add('differs', vtype=Differ, array=True,
                   doc="The 'Differ' object(s) to execute.")

        params.add('_unique_id', vtype=uuid.UUID, mutable=False, private=True)
        return params

    def __init__(self, *args, **kwargs):
        kwargs['_unique_id'] = uuid.uuid4()
        MooseObject.__init__(self, *args, **kwargs)

    def execute(self):
        raise NotImplementedError()
