import os
import io
import sys
import copy
import time
import asyncio
import traceback
import threading
import multiprocessing
multiprocessing.set_start_method('fork')

import concurrent.futures

#import threading

import dill

import queue
import logging
import collections
from moosetools.moosetest.base import State, TestCase
#from moosetools.moosetest.base import Runner
from moosetools.moosetest.runners import ProcessRunner
from moosetools.moosetest.differs import TextDiff
from moosetools.moosetest.formatters import SimpleFormatter


def execute_testcases(testcases, conn, timeout):
    for tc in testcases:
        unique_id = tc.getParam('_unique_id')
        conn.send((unique_id, TestCase.Progress.RUNNING, time.time(), None, None))
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                f = executor.submit(tc.execute)
                try:
                    state, results = f.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    state = TestCase.Result.TIMEOUT
                    results = {tc.name(): (TestCase.Result.TIMEOUT, 1, '', '')}

            #state, results = tc.execute()
        except Exception as ex:
            state = TestCase.Result.FATAL
            results = {tc.name(): (TestCase.Result.FATAL, 1, '', traceback.format_exc())}

        conn.send((unique_id, TestCase.Progress.FINISHED, time.time(), state, results))

    conn.close()

def _on_error(*args):
    print(args)


def run(groups, controllers, formatter, n_threads=None, timeout=None, progress_interval=None):

    tc_kwargs = dict()
    tc_kwargs['progress_interval'] = progress_interval
    tc_kwargs['formatter'] = formatter

    #comm = queue.SimpleQueue()
    #pool = concurrent.futures.ThreadPoolExecutor(max_workers=n_threads)

    #manager = multiprocessing.Manager()
    #data = manager.dict()
    #pool = concurrent.futures.ProcessPoolExecutor(max_workers=n_threads)
    pool = multiprocessing.Pool(processes=n_threads)

    pipes = list()


    futures = list() # Future object returned from `pool.submit`
    testcase_map = dict() # unique_id to Runner object
    for runners in groups:
        testcases = [TestCase(runner=runner, **tc_kwargs) for runner in runners]
        p_recv, p_send = multiprocessing.Pipe(False)
        pipes.append(p_recv)

        #execute_testcases(testcases, None)
        #futures.append(pool.submit(execute_testcases, testcases, None))
        futures.append(pool.apply_async(execute_testcases, args=(testcases, p_send, timeout),
                                        error_callback=_on_error))
        #comm_send.close()
        for tc in testcases:
            #tc.parameters().set('formatter', formatter)
            testcase_map[tc.getParam('_unique_id')] = tc

    #pool.shutdown()

    pool.close()
    while any(not f.ready() for f in futures):
        for pipe in pipes:
            if pipe.poll():
                try:
                    unique_id, progress, t, state, results = pipe.recv()
                    if progress == TestCase.Progress.RUNNING:
                        tc = testcase_map.get(unique_id)
                        tc.setProgress(progress, t)
                    else:
                        tc = testcase_map.pop(unique_id)
                        tc.setProgress(progress, t)
                        tc.setState(state)
                        tc.setResult(results)
                        tc.reportResult()
                except EOFError:
                    pass

        for tc in testcase_map.values():
            tc.reportProgress()
    """
    print(futures)
    time.sleep(1)
    print([f.ready() for f in futures])
    time.sleep(1)
    print([f.ready() for f in futures])

    while any(not f.ready() for f in futures):# or len(testcase_map) > 0:
        print('here')
    #    for comm, _ in pipes:
    #        if comm.poll():
    #            unique_id, progress, state, results = comm.recv()
    #            print(unique_id, progress)

    print(any(not f.ready() for f in futures))
    """

    """
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
    """


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

    grp_a = [None]*2
    grp_a[0] = ProcessRunner(name='A:test/1', command=('sleep', '4'),
                          differs=(TextDiff(name='diff', text_in_stderr='sleep'),
                                   TextDiff(name='diff2', text_in_stderr='2')))
    grp_a[1] = ProcessRunner(name='A:test/2', command=('sleep', '1'))


    grp_b = [None]*3
    grp_b[0] = ProcessRunner(name='B:test/1', command=('sleep', '3'))
    grp_b[1] = ProcessRunner(name='B:test/2', command=('sleep', '5'))
    grp_b[2] = ProcessRunner(name='B:test/3', command=('sleep', '1'))


    grp_c = [None]*2
    grp_c[0] = ProcessRunner(name='C:test/1', command=('sleep', '13'))
    grp_c[1] = ProcessRunner(name='C:test/2', command=('sleep', '1'))


    groups = [grp_a, grp_b, grp_c]

    sys.exit(run(groups, None, SimpleFormatter(), n_threads=2, timeout=10))
