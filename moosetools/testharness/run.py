import os
import io
import sys
import time
import traceback
import concurrent.futures
import multiprocessing
import threading
import queue
from moosetools.moosetest.base import State, TestCase
from moosetools.moosetest.runners import ProcessRunner

"""
TODO:
- Create discover function to return the test case groups, use ThreadPool and return TestCase  objects
- Run should run the groups
"""

# TODO
# - implement timeout failsafe to avoid handing
# - show run time information in Runner/Testers (probably add to output from TestCase.execute)
# - add percent complete to output


def make_runner(i, r=None):
    return ProcessRunner(name='foo/bar.i'.format(i), command=('sleep', str(i)))

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

    jobs = dict()
    futures = list()
    for testcases in groups:
        futures.append(pool.submit(run_the_testcases, testcases, comm))
        for tc in testcases:
            jobs[tc.getParam('_unique_id')] = tc


    while any(not f.done() for f in futures):
        if not comm.empty():
            unique_id, result = comm.get()
            jobs[unique_id].setResult(result)

        for key in list(jobs.keys()):
            tc = jobs[key]
            tc.report()
            if tc.getProgress() == TestCase.Progress.FINISHED:
                jobs.pop(key)






    """
    while len(jobs) > 0:
        #if not comm.empty():
        #    unique_id, result = comm.get()
        #    jobs.pop(unique_id).setResult(result)
        #    print(unique_id)

        for key in list(jobs.keys()):
            tc = jobs[key]
            tc.report()

            if tc.getProgress() == TestCase.Progress.FINISHED:
                jobs.pop(key)

        time.sleep(0.5)
    """


if __name__ == '__main__':
    import random
    import logging
    logging.basicConfig()


    sleep_range = (2,20)
    n_groups = 4
    n_per_group = 3
    groups = list()

    for i in range(n_groups):
        local = list()
        for j in range(n_per_group):
            t =  random.randint(*sleep_range)
            runner = ProcessRunner(name='{}/{}.rand_{}'.format(i, j, t), command=('sleep', str(t)))
            local.append(TestCase(controller=None, runner=runner))
        groups.append(local)

    sys.exit(run(groups, n_threads=4))
