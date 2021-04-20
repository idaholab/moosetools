import os
import io
import sys
import time
import traceback
import concurrent.futures
import queue
from moosetools.moosetest.base import State, TestCase
from moosetools.moosetest.runners import ProcessRunner
from moosetools.moosetest.differs import TextDiff

"""
TODO:
- Create discover function to return the test case groups, use ThreadPool and return TestCase  objects
- Run should run the groups
"""

# TODO
# - implement timeout failsafe to avoid handing
# - show run time information in Runner/Testers (probably add to output from TestCase.execute)
# - add percent complete to output


def run_the_testcases(testcases, comm):
    for tc in testcases:
        try:
            # TODO: document that this should not throw, but if it does...
            r = tc.execute()
        except Exception as ex:
            r = ((TestCase.Result.FATAL, traceback.format_exc()))

        comm.put((tc.getParam('_unique_id'), r))



def run(groups, n_threads=None):
    if n_threads is None: n_threads = os.cpu_count()


    comm = queue.Queue()
    pool = concurrent.futures.ThreadPoolExecutor(n_threads)
    #comm = multiprocessing.Queue()
    #pool = concurrent.futures.ProcessPoolExecutor(n_threads)

    jobs = dict()
    futures = list()
    for testcases in groups:
        futures.append(pool.submit(run_the_testcases, testcases, comm))
        for tc in testcases:
            jobs[tc.getParam('_unique_id')] = tc


    while any(not f.done() for f in futures):
        while not comm.empty():
            unique_id, result = comm.get()
            tc = jobs.pop(unique_id)
            tc.setResult(result)
            tc.report()

        for tc in jobs.values():#key in list(jobs.keys()):
            #tc = jobs[key]
            tc.report()
            #if tc.getProgress() == TestCase.Progress.FINISHED:
            #    jobs.pop(key)

        #time.sleep(0.1)

if __name__ == '__main__':
    import random
    import logging

    handler = logging.StreamHandler()
    logging.basicConfig(handlers=[handler], format='%(message)s')


    sleep_range = (1,2)
    n_groups = 4
    n_per_group = 3
    groups = list()

    #for i in range(n_groups):
    #    local = list()
    #    for j in range(n_per_group):
    #        t =  random.randint(*sleep_range)
    #        runner = ProcessRunner(name='{}/{}.rand_{}'.format(i, j, t), command=('sleep', str(t)))
    #        differs = (TextDiff(name=runner.name() + '.text', text_in='sleep'),
    #                   TextDiff(name=runner.name() + '.text2', text_in='sleep 2'))
    #        local.append(TestCase(controller=None, runner=runner, differs=differs))
    #    groups.append(local)


    groups = [[TestCase(differs=tuple(), runner=ProcessRunner(name='bad', command=('wrong',)))],
              [TestCase(differs=tuple(), runner=ProcessRunner(name='bad', command=('sleep', '2')))]]

    sys.exit(run(groups, n_threads=1))
