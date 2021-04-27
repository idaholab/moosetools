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
from moosetools.moosetest.formatters import SimpleFormatter

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


def run(groups, controllers, formatter, n_threads=None, progress_interval=None):

    tc_kwargs = dict()
    tc_kwargs['progress_interval'] = progress_interval
    tc_kwargs['formatter'] = formatter

    comm = queue.SimpleQueue()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=n_threads)

    futures = list() # Future object returned from `pool.submit`
    testcase_map = dict() # unique_id to Runner object
    for runners in groups:
        testcases = [TestCase(runner=runner, **tc_kwargs) for runner in runners]

        futures.append(pool.submit(execute_testcases, testcases, None, comm))
        for tc in testcases:
            testcase_map[tc.getParam('_unique_id')] = tc


    while any(not f.done() for f in futures) or len(testcase_map) > 0:

        try:
            unique_id, progress, state, results = comm.get_nowait()
            if results is None:
                tc =  testcase_map.get(unique_id)
                tc.setProgress(progress)

            else:
                tc = testcase_map.pop(unique_id)
                tc.setState(state)
                tc.setResult(results)
                tc.reportResult()

        except queue.Empty:
            pass

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
    groups = [[ProcessRunner(name='filename:test/1', command=('sleep', '4'),
                             differs=(TextDiff(name='diff', text_in_stderr='sleep'),
                                      TextDiff(name='diff2', text_in_stderr='2')))],
              [ProcessRunner(name='filename:test/2', command=('sleep', '3'))],
              [ProcessRunner(name='test.3', command=('sleep', '13'))]]

    #groups = [[TestCase(runner=ProcessRunner(name='first', command=('sleep', '4')))]]

    #print(groups)
    sys.exit(run(groups, None, SimpleFormatter(), n_threads=2))
