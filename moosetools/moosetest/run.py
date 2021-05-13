import os
import io
import sys
import copy
import time
import traceback
import queue
import concurrent.futures
import multiprocessing

from moosetools.mooseutils import color_text
from moosetools.moosetest.base import TestCase

def run(groups, controllers, formatter, n_threads=None, timeout=None, max_fails=None, min_fail_state=TestCase.Result.TIMEOUT):

    start_time = time.time()

    tc_kwargs = dict()
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

    while any(not tc.finished for tc in testcase_map.values()):
        _running_results(testcase_map, formatter, result_queue)
        _running_progress(testcase_map, formatter, futures, max_fails)

    print(formatter.formatComplete(testcase_map.values(), duration=time.time() - start_time))

    failed = sum(tc.state.level > min_fail_state.level for tc in testcase_map.values())
    return 1 if failed > 0 else 0

def _execute_testcase(tc, conn):
    """
    Function for executing the `TestCase` *tc* with exception handling from within a subprocess.

    This function is expected to be called by a `multiprocessing.Process`, as such the *conn* is
    expected to be a `multiprocessing.Pipe` that the be used to send the results to the spawning
    process.

    See the `_execute_testcases` for use.
    """
    try:
        state, results = tc.execute()
    except Exception:
        state = TestCase.Result.FATAL
        results = {tc.name(): TestCase.Data(TestCase.Result.FATAL, 1, '', traceback.format_exc(), None)}
    conn.send((state, results))
    conn.close()


def _execute_testcases(testcases, q, timeout):
    """
    Function for executing groups of `TestCase` objects, *testcases*, each within a subprocess.

    This function is expected to be called from `concurrent.futures.ProcessPoolExecutor`. The *q*,
    which is a `multiprocessing.Queue` is used to send the results from the run of +each+ `TestCase`
    to the main process. This is done to allow the main process to report the results without
    waiting for the entire group to complete.

    The *timeout* is the number of seconds that each `TestCase` is allowed to run before it is
    aborted. This is accomplished by running the cases in another process.

    See the `run` function for use.
    """
    skip_message = None

    for tc in testcases:
        unique_id = tc.getParam('_unique_id')
        if skip_message:
            state = TestCase.Result.SKIP
            results = {tc.name(): TestCase.Data(TestCase.Result.SKIP, 0, '', skip_message, ['dependency'])}
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
            results = {tc.name(): TestCase.Data(TestCase.Result.TIMEOUT, 1, '', '', [f'max time ({timeout}) exceeded'])}

        q.put((unique_id, TestCase.Progress.FINISHED, state, results))

        if (state.level > 0):
            skip_message = f"A previous `TestCase` ({tc.name()}) in the group returned a non-zero state of {state}."


def _running_results(testcase_map, formatter, result_queue):
    """
    Helper function for reporting results as obtained during a call to `run` function.

    The results are obtained from the *result_queue* for `TestCase` objects within the
    *testcase_map*.

    See `run` function for use.
    """
    try:
        unique_id, progress, state, results = result_queue.get_nowait()
        tc = testcase_map.get(unique_id)
        tc.setProgress(progress)
        if progress == TestCase.Progress.FINISHED:
            tc.setState(state)
            tc.setResults(results)
            formatter.reportResult(tc)
        result_queue.task_done()

    except queue.Empty:
        pass


def _running_progress(testcase_map, formatter, futures, max_fails):
    """
    Helper function for reporting state of the `TestCase` objects.

    The supplied `TestCase` objects *testcase_map* are each checked, if the case is running the
    progress is reporte. If more than *max_fails* is reached the processes in *futures* are canceled.
    """

    num_fail = 0
    for tc in testcase_map.values():
        if tc.finished and tc.state.level > 1: # above skip
            num_fail += 1

        if (num_fail >= max_fails) and tc.waiting:
            tc.setProgress(TestCase.Progress.FINISHED)
            tc.setState(TestCase.Result.SKIP)
            tc.setResults({tc.name(): TestCase.Data(TestCase.Result.SKIP, 0, '', f"Max failures of {max_fails} exceeded.", ['max failures reached'])})
            formatter.reportResult(tc)

        if tc.running:
            formatter.reportProgress(tc)

    if num_fail >= max_fails:
        for f in futures:
            f.cancel()


if  __name__ == '__main__':
    import logging
    from moosetools.moosetest.base import make_runner, make_differ
    from moosetools.moosetest.runners import RunCommand
    from moosetools.moosetest.differs import ConsoleDiff
    from moosetools.moosetest.formatters import BasicFormatter
    from moosetools.moosetest.controllers import EnvironmentController
    logging.basicConfig()

    controllers = (EnvironmentController(),)
    formatter = BasicFormatter()

    grp_a = [None]*3
    grp_a[0] = make_runner(RunCommand, controllers, name='A:test/with/a/long/name/1', command=('sleep', '4'),
                          differs=(make_differ(ConsoleDiff, controllers, name='diff', text_in_stderr='sleep'),
                                   make_differ(ConsoleDiff, controllers, name='diff2', text_in_stderr='2')))
    grp_a[1] = make_runner(RunCommand, controllers, name='A:test/with/a/long/name/2', command=('sleep', '2'))
    grp_a[2] = make_runner(RunCommand, controllers, name='A:test/with/a/long/name/3', command=('sleep', '1'))

    grp_b = [None]*5
    grp_b[0] = make_runner(RunCommand, controllers, name='B:test/1', command=('sleep', '3'),
                             differs=(make_differ(ConsoleDiff, controllers, name='diff', text_in_stderr='sleep'),
                                      make_differ(ConsoleDiff, controllers, name='diff2', text_in_stderr='3')))
    grp_b[1] = make_runner(RunCommand, controllers, name='B:test/2', command=('sleep', '5'),
                             differs=(make_differ(ConsoleDiff, controllers, name='diff', text_in_stderr='sleep'),
                                      make_differ(ConsoleDiff, controllers, name='diff2', text_in_stderr='2')))
    grp_b[2] = make_runner(RunCommand, controllers, name='B:test/3', command=('sleep', '1'))
    grp_b[3] = make_runner(RunCommand, controllers, name='B:test/4', command=('wrong', ))
    grp_b[4] = make_runner(RunCommand, controllers, name='B:test/5', command=('sleep', '3'))

    grp_c = [None]*2
    grp_c[0] = make_runner(RunCommand, controllers, name='C:test/1', command=('sleep', '13'))
    grp_c[1] = make_runner(RunCommand, controllers, name='C:test/2', command=('sleep', '1'), env_platform=('Linux',))

    grp_d = [None]*2
    grp_d[0] = make_runner(RunCommand, controllers, name='D:test/1', command=('sleep', '2'))
    grp_d[1] = make_runner(RunCommand, controllers, name='D:test/2', command=('sleep', '1'), env_platform=('Linux',))


    groups = [grp_a, grp_b, grp_c, grp_d]

    sys.exit(run(groups, controllers, formatter, n_threads=4, timeout=10, max_fails=5))
