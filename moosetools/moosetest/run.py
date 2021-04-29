import os
import io
import sys
import copy
import time
import traceback
import queue
import concurrent.futures
import multiprocessing
multiprocessing.set_start_method('fork')

from moosetools.mooseutils import color_text
from moosetools.moosetest.base import TestCase

def _execute_testcase(tc, conn):
    try:
        state, results = tc.execute()
    except Exception:
        state = TestCase.Result.FATAL
        results = {tc.name(): (TestCase.Result.FATAL, 1, '', traceback.format_exc())}
    conn.send((state, results))
    conn.close()

def _execute_testcases(testcases, q, timeout):

    skip_message = None

    for tc in testcases:
        unique_id = tc.getParam('_unique_id')
        if skip_message:
            state = TestCase.Result.SKIP
            results = {tc.name(): (TestCase.Result.SKIP, 0, '', skip_message)}
            q.put((unique_id, TestCase.Progress.FINISHED, state, results))
            continue

        q.put((unique_id, TestCase.Progress.RUNNING, None, None))

        conn_recv, conn_send = multiprocessing.Pipe(False)
        proc = multiprocessing.Process(target=_execute_testcase, args=(tc, conn_send))
        proc.start()

        if conn_recv.poll(timeout):
            state, results = conn_recv.recv()
        else:
            proc.terminate()
            state = TestCase.Result.TIMEOUT
            results = {tc.name(): (TestCase.Result.TIMEOUT, 1, '', '')}

        q.put((unique_id, TestCase.Progress.FINISHED, state, results))

        if (state.level > 0):
            skip_message = f"A previous `TestCase` ({tc.name()}) in the group returned a non-zero state of {state}."


def _running_results(testcase_map, result_queue):

    try:
        unique_id, progress, state, results = result_queue.get_nowait()
        tc = testcase_map.get(unique_id)
        tc.setProgress(progress)
        if progress == TestCase.Progress.FINISHED:
            tc.setState(state)
            tc.setResult(results)
            tc.reportResult()
        result_queue.task_done()

    except queue.Empty:
        pass

def _running_progress(testcase_map, futures, progress_interval, max_fails):

    num_fail = 0
    for tc in testcase_map.values():
        if tc.finished and tc.state.level > 1: # above skip
            num_fail += 1

        if (num_fail >= max_fails) and tc.waiting:
            tc.setProgress(TestCase.Progress.FINISHED)
            tc.setState(TestCase.Result.SKIP)
            tc.setResult({tc.name(): (TestCase.Result.SKIP, 0, '', f"Max failures of {max_fails} exceeded.")})
            tc.reportResult()

        if tc.running and (tc.time > progress_interval):
            tc.reportProgress()

    if num_fail >= max_fails:
        for f in futures:
            f.cancel()

def run(groups, controllers, formatter, n_threads=None, timeout=None, progress_interval=None, max_fails=None):

    start_time = time.time()

    tc_kwargs = dict()
    tc_kwargs['formatter'] = formatter
    tc_kwargs['controllers'] = controllers


    executor = concurrent.futures.ProcessPoolExecutor(max_workers=n_threads)
    manager = multiprocessing.Manager()
    result_queue = manager.Queue()

    futures = list()
    testcase_map = dict()
    for runners in groups:
        testcases = [TestCase(runner=runner, **tc_kwargs) for runner in runners]
        #_execute_testcases(testcases, result_queue, timeout)
        futures.append(executor.submit(_execute_testcases, testcases, result_queue, timeout))
        for tc in testcases:
            testcase_map[tc.getParam('_unique_id')] = tc

    while any(not tc.finished for tc in testcase_map.values()):#len(testcase_map) > 0:
        _running_results(testcase_map, result_queue)
        _running_progress(testcase_map, futures, progress_interval, max_fails)

    print(formatter.formatComplete(testcase_map.values(), duration=time.time() - start_time))

if __name__ == '__main__':
    import logging
    from moosetools.moosetest.runners import ProcessRunner
    from moosetools.moosetest.differs import TextDiff
    from moosetools.moosetest.formatters import SimpleFormatter
    from moosetools.moosetest.controllers import EnvironmentController
    logging.basicConfig()

    controllers = (EnvironmentController(),)
    formatter = SimpleFormatter()

    grp_a = [None]*3
    grp_a[0] = ProcessRunner(None, controllers, name='A:test/1', command=('sleep', '4'),
                          differs=(TextDiff(None, controllers, name='diff', text_in_stderr='sleep'),
                                   TextDiff(None, controllers, name='diff2', text_in_stderr='2')))
    grp_a[1] = ProcessRunner(None, controllers, name='A:test/2', command=('sleep', '2'))
    grp_a[2] = ProcessRunner(None, controllers, name='A:test/3', command=('sleep', '1'))

    grp_b = [None]*5
    grp_b[0] = ProcessRunner(None, controllers, name='B:test/1', command=('sleep', '3'),
                             differs=(TextDiff(None, controllers, name='diff', text_in_stderr='sleep'),
                                      TextDiff(None, controllers, name='diff2', text_in_stderr='3')))
    grp_b[1] = ProcessRunner(None, controllers, name='B:test/2', command=('sleep', '5'), env_platform=('Linux',),
                             differs=(TextDiff(None, controllers, name='diff', text_in_stderr='sleep'),
                                      TextDiff(None, controllers, name='diff2', text_in_stderr='2')))
    grp_b[2] = ProcessRunner(None, controllers, name='B:test/3', command=('sleep', '1'))
    grp_b[3] = ProcessRunner(None, controllers, name='B:test/4', command=('wrong', ))
    grp_b[4] = ProcessRunner(None, controllers, name='B:test/5', command=('sleep', '3'))

    grp_c = [None]*2
    grp_c[0] = ProcessRunner(None, controllers, name='C:test/1', command=('sleep', '13'))
    grp_c[1] = ProcessRunner(None, controllers, name='C:test/2', command=('sleep', '1'))


    groups = [grp_a, grp_b, grp_c]

    sys.exit(run(groups, controllers, formatter, n_threads=1, timeout=10, max_fails=5, progress_interval=4))
