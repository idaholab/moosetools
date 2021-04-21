import os
from moosetools.base import MooseObject
from moosetools.moosetest.base import Controller, Runner, Differ

class MooseTest(MooseObject):
    @staticmethod
    def validParams():
        params = MooseObject.validParams()
        #params.add('working_dir', vtype=str,
        #           verify=(lambda d: os.path.isdir(d), "The supplied working directory must exist."),
        #           doc="The working directory for locating and executing tests.")

        params.add('progress_interval', vtype=int, default=10,
                   doc="The duration between printing the progress message of test cases.")

        params.add('plugin_dirs',
                   vtype=str,
                   array=True,
                   verify=(lambda dirs: all(os.path.isdir(d) for d in dirs),
                           "Supplied plugin directories must exist."),
                   doc="List of directories to search for plugins.")

        # Storage for the location of the '.moosetest' file or the current working directory, this
        # is set by the creation function in main.py.
        #params.add('_root_dir', vtype=str, default=os.getcwd(), private=True)

        return params

    def __init__(self, *args, **kwargs):
        MooseObject.__init__(self, *args, **kwargs)









    def discover(self):
        pass


    def run(self):
        pass
