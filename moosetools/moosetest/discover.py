import os
import concurrent.futures
from moosetools import moosetree
from moosetools import pyhit
from moosetools import factory
from moosetools.moosetest.base import Controller, TestCase


# TODO:
# - Perform factory.status() checks() and make sure error messages are usable
# - Name objects using _hit_path



class MooseTestFactory(factory.Factory):
    @staticmethod
    def validParams():
        params = factory.Factory.validParams()
        params.add('controllers', vtype=Controller, array=True,
                   doc="Controller objects for injecting into validParams of Runner/Differ objects.")
        return params

    def params(self, *args, **kwargs):
        params = factory.Factory.params(self, *args, **kwargs)

        for controller in self.getParam('controllers') or list():

            params.add(controller.getParam('prefix'),
                       default=controller.validObjectParams(),
                       doc="Parameters for determining execute state from the '{}' control object.".format(type(controller).__name__))

        return params






def create_testcases(filename, spec_file_blocks, obj_factory):

    root = pyhit.load(filename)


    runners = list()
    parser = factory.Parser(obj_factory, runners)
    for node in moosetree.findall(root, func=lambda n: n.name in spec_file_blocks):
        parser.parse(filename, node)

    testcases = list()
    for runner in runners:
        node = moosetree.find(root, func=lambda n: n.fullpath == runner.getParam('_hit_path'))
        differs = list()
        parser = factory.Parser(obj_factory, differs)
        for child in node:
            parser.parse(filename, child)

        testcases.append(TestCase(runner=runner, differs=tuple(differs)))

    return testcases



#def _create_testcases(filename):








def discover(start, spec_file_names, spec_file_blocks, plugin_dirs=None, controllers=None, n_threads=None):
    """
    Return groups of `TestCase` objects to execute.
    """
    if n_threads is None: n_threads = os.cpu_count()

    # Create a list of files
    spec_files = list()
    for root, _, files in os.walk(start):
        spec_files += [os.path.join(root, f) for f in files if f in spec_file_names]

    from moosetools.moosetest.base import Runner, Differ
    obj_factory = MooseTestFactory(plugin_dirs=plugin_dirs, plugin_types=(Runner, Differ), controllers=controllers)
    obj_factory.load()

    with concurrent.futures.ThreadPoolExecutor(n_threads) as pool:
        futures = [pool.submit(create_testcases, filename, spec_file_blocks, obj_factory) for filename in spec_files]

    return [f.result() for f in futures]
