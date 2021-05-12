import os
import concurrent.futures
from moosetools import moosetree
from moosetools import pyhit
from moosetools import factory
from moosetools.moosetest.base import Controller, TestCase
from moosetools.moosetest.base import Runner, Differ


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


class MooseTestWarehouse(factory.Warehouse):
    @staticmethod
    def validParams():
        params = factory.Warehouse.validParams()
        params.add('common_prefix', vtype=str, default=None,
                   doc="The common prefix to remove from the filename when adding the object.")
        return params

    def append(self, obj):

        if isinstance(obj, Differ):
            self.objects[-1].getParam('differs').append(obj)
        else:
            prefix = obj.getParam('_hit_filename').replace(self.getParam('common_prefix'), '')
            name = "{}:{}".format(prefix, obj.getParam('_hit_path'))
            obj.parameters().setValue('name', name)

            factory.Warehouse.append(self, obj)

def create_runners(filename, spec_file_blocks, obj_factory, common_prefix):

    root = pyhit.load(filename)
    wh = MooseTestWarehouse(common_prefix=common_prefix)
    parser = factory.Parser(obj_factory, wh)
    for node in moosetree.findall(root, func=lambda n: n.name in spec_file_blocks):
        parser.parse(filename, node)

    # TODO: return list of lists, by default [testcases], but should detect parameter in
    #       the runner block to run separate to allow for dependencies to be removed

    return wh.objects


def discover(start, spec_file_names, spec_file_blocks, plugin_dirs=None, controllers=None, n_threads=None):
    """
    Return groups of `TestCase` objects to execute.
    """
    if n_threads is None: n_threads = os.cpu_count()

    # Create a list of files
    spec_files = list()
    for root, _, files in os.walk(start):
        spec_files += [os.path.join(root, f) for f in files if f in spec_file_names]
    common_prefix = os.path.commonprefix(spec_files)

    obj_factory = MooseTestFactory(plugin_dirs=tuple(plugin_dirs), plugin_types=(Runner, Differ), controllers=tuple(controllers))
    obj_factory.load()

    with concurrent.futures.ThreadPoolExecutor(n_threads) as pool:
        futures = [pool.submit(create_runners, filename, spec_file_blocks, obj_factory, common_prefix) for filename in spec_files]

    #testcases = [f.result() for f in futures]


    #paths = [tc.name() for tc in [group for group in testcases]]
    #print(paths)

    return [f.result() for f in futures]

    #return [create_runners(filename, spec_file_blocks, obj_factory) for filename in spec_files]
