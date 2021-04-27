import os
import io
import sys
import time
import traceback
import concurrent.futures
import queue
import logging
import collections
from moosetools.moosetest.base import State, TestCase
#from moosetools.moosetest.base import Runner
from moosetools.moosetest.runners import ProcessRunner
from moosetools.moosetest.differs import TextDiff

def execute_testcases(testcases, controllers, comm):
    # TODO: document that this should not throw, but if it does...catch it as above


    for tc in testcases:
        unique_id = tc.getParam('_unique_id')
        #print(tc.name(), TestCase.Progress.RUNNING)
        #print('PUT:', (unique_id, TestCase.Progress.RUNNING, None, None))
        comm.put((unique_id, TestCase.Progress.RUNNING, None, None))

        try:
            # TODO: document that this should not throw, but if it does...
            state, results = tc.execute()
        except Exception as ex:
            state = TestCase.Result.FATAL
            results = {tc._runner.name(): (TestCase.Result.FATAL, 1, '', traceback.format_exc())}

        #print('PUT:', (unique_id, TestCase.Progress.FINISHED, state, results))
        comm.put((unique_id, TestCase.Progress.FINISHED, state, results))


def run(groups, controllers, n_threads=None):

    comm = queue.SimpleQueue()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=n_threads)

    futures = list() # Future object returned from `pool.submit`
    testcase_map = dict() # unique_id to Runner object
    for testcases in groups:
        futures.append(pool.submit(execute_testcases, testcases, None, comm))
        for tc in testcases:
            testcase_map[tc.getParam('_unique_id')] = tc


    while any(not f.done() for f in futures) or len(testcase_map) > 0:

        try:
            unique_id, progress, state, results = comm.get_nowait()
            #print((unique_id, progress, state, results))
            if results is None:
                tc =  testcase_map.get(unique_id)
                tc.setProgress(progress)

            else:
                tc = testcase_map.pop(unique_id)
                tc.setResult(state, results)
                tc.reportResult()

        except queue.Empty:
            pass

    #while any(not f.done() for f in futures) or (not comm.empty()):
        #while not comm.empty():
        """
        unique_id, progress, state, results = comm.get()
        print('GET:', (unique_id, progress, state, results))
        tc = testcase_map.get(unique_id)
        tc.setProgress(progress)
        if results is not None:
            tc.setResult(state, results)
            tc.reportResult()
            completed += 1
        """

        for tc in testcase_map.values():
            tc.reportProgress()

    # TODO: SUM Results, track total time

if __name__ == '__main__':
    """
    import random
    import logging

    handler = logging.StreamHandler()
    #logging.basicConfig(handlers=[handler])#, format='%(levelname)s: %(message)s')
    logging.basicConfig(handlers=[handler], format='%(message)s')

    sleep_range = (1,2)
    n_groups = 4
    n_per_group = 3
    groups = list()

    for i in range(n_groups):
        local = list()
        for j in range(n_per_group):
            t =  random.randint(*sleep_range)
            runner = ProcessRunner(name='{}/{}.rand_{}'.format(i, j, t), command=('sleep', str(t)))
            differs = (TextDiff(name=runner.name() + '.text', text_in='sleep'),
                       TextDiff(name=runner.name() + '.text2', text_in='sleep 2'))
            local.append(TestCase(runner=runner, differs=differs))
        groups.append(local)
    """

    # TODO: Create TestCases inside of run command

    logging.basicConfig()
    groups = [[TestCase(runner=ProcessRunner(name='first', command=('sleep', '4')))],
              [TestCase(runner=ProcessRunner(name='second', command=('sleep', '3')))]]

    #groups = [[TestCase(runner=ProcessRunner(name='first', command=('sleep', '4')))]]

    #print(groups)
    sys.exit(run(groups, None, n_threads=2))
