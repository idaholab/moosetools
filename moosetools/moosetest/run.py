import os
import io
import sys
import copy
import time
import traceback
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




#def execute_testcase(tc, output):
#    state, results = tc.execute()
#    output[0] = state
#    output[1] = results

def execute_testcases(testcases, comm):
    for tc in testcases:
        unique_id = tc.getParam('_unique_id')
        comm.send((unique_id, TestCase.Progress.RUNNING, None, None))
        try:
            state, results = tc.execute()
        except Exception as ex:
            state = TestCase.Result.FATAL
            results = {tc._runner.name(): (TestCase.Result.FATAL, 1, '', traceback.format_exception(type(ex), ex, True))}

        comm.send((unique_id, TestCase.Progress.FINISHED, state, results))
    comm.close()

def _tmp(testcases, comm):

    # TODO: document that this should not throw, but if it does...catch it as above


    #skip_remaining = False


    for tc in testcases:
        #if skip_remaining:
        #    state = TestCase.Result.SKIP
        #    results = {tc._runner.name(): (TestCase.Result.SKIP, 1, None, None)}
        #    comm.put((unique_id, TestCase.Progress.FINISHED, state, results))
        #    continue

        unique_id = tc.getParam('_unique_id')

        #comm.send((unique_id, TestCase.Progress.RUNNING, None, None))


        #print(tc.name(), TestCase.Progress.RUNNING)
        #print('PUT:', (unique_id, TestCase.Progress.RUNNING, None, None))
        #comm.put((unique_id, TestCase.Progress.RUNNING, None, None))
        #results[unique_id] = (TestCase.Progress.RUNNING, None, None)

        try:
            # TODO: document that this should not throw, but if it does...
            """
            output = [None]*2
            tid = threading.Thread(target=execute_testcase, args=(tc,output))
            tid.start()
            tid.join(timeout=5)
            if tid.is_alive():
                state = TestCase.Result.TIMEOUT
                results = {tc._runner.name(): (TestCase.Result.TIMEOUT, 1, '', '')}
            else:
                state = output[0]
                results = output[1]
            """
            state, local_results = tc.execute()


        except Exception as ex:
            state = TestCase.Result.FATAL
            local_results = {tc._runner.name(): (TestCase.Result.FATAL, 1, '', traceback.format_exc())}


        #print('here')
        #results[unique_id] = (TestCase.Progress.FINISHED, state, local_results)
        #print('PUT:', (unique_id, TestCase.Progress.FINISHED, state, results))
        #comm.put((unique_id, TestCase.Progress.FINISHED, state, results))
        #comm.send((unique_id, TestCase.Progress.FINISHED, state, results))

        #comm.close()
        #if state > 0 or state == TestCase.Result.SKIP:
        #    skip_remaining = True

def on_error(exc, comm):
    print(multiprocessing.current_process(), multiprocessing.parent_process())
    comm.send((None, None, None, None))
    #raise exc

def run(groups, controllers, formatter, n_threads=None, progress_interval=None):

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
        comm_recv, comm_send = multiprocessing.Pipe(False)
        pipes.append(comm_recv)

        #execute_testcases(testcases, None)
        #futures.append(pool.submit(execute_testcases, testcases, None))
        futures.append(pool.apply_async(execute_testcases, args=(testcases, comm_send),
                                        error_callback=lambda x: on_error(x, comm_send)))
        #comm_send.close()
        for tc in testcases:
            #tc.parameters().set('formatter', formatter)
            testcase_map[tc.getParam('_unique_id')] = tc

    #pool.shutdown()

    pool.close()
    force = False
    while any(not f.ready() for f in futures):# or multiprocessing.connection.wait(pipes):
        for r in pipes:
            if r.poll():
                try:
                    unique_id, progress, state, results = r.recv()
                    if progress == TestCase.Progress.RUNNING:
                        tc = testcase_map.get(unique_id)
                        tc.setProgress(progress)
                    elif progress == TestCase.Progress.FINISHED:
                        tc = testcase_map.pop(unique_id)
                        tc.setProgress(progress)
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
    grp_b[1] = ProcessRunner(name='B:test/2', command=('sleep', '1'))
    grp_b[2] = ProcessRunner(name='B:test/3', command=('sleep', '1'))


    grp_c = [None]*2
    grp_c[0] = ProcessRunner(name='C:test/1', command=('sleep', '13'))
    grp_c[1] = ProcessRunner(name='C:test/2', command=('sleep', '1'))


    groups = [grp_a, grp_b, grp_c]

    sys.exit(run(groups, None, SimpleFormatter(), n_threads=2))
