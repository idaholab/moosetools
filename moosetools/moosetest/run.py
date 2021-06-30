#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import sys
import time
import traceback
import queue
import platform
import concurrent.futures
import threading
import multiprocessing
import time
import enum
from moosetools.moosetest.base import TestCase

# By default macOS use 'spawn' for creating processes. However, I had problems with the following
# warning being produced. I couldn't figure out that root cause of the warning with respect to the
# code here. It might be related to https://bugs.python.org/issue38119. Using 'fork' does not result
# in the warning, so I went with that until I figure out the reason.
#
# UserWarning: resource_tracker: There appear to be 5 leaked semaphore objects to clean up at shutdown
MULTIPROCESSING_CONTEXT = 'fork'


def run(groups,
        controllers,
        formatter,
        filters,
        *,
        n_threads=os.cpu_count(),
        timeout=None,
        max_fails=sys.maxsize,
        min_fail_state=TestCase.Result.TIMEOUT,
        method=None):
    """
    Primary function for running tests.

    The *groups* is a `list` of `list` of `Runner` object to be executed. The outer list is
    distributed for execution using a process pool. The inner list is executed sequentially within
    that pool.

    The *controllers* is a list of `Controller` objects to be used during execution. The
    sub-parameters for each should already be injected into the `Runner` objects (i.e., they
    should be created with the `make_runner` function).

    The *formatter* is a `Formatter` object used to format all output of progress and results.

    The process pool will execute with *n_threads*, if provided, otherwise it will utilize the
    number returned by `os.cpu_count`. Each `Runner` object will execute and wait for *timeout*
    seconds to complete, before a timeout error is produced. Execution will continue until all
    objects had executed or timeout, unless the number of failures exceeds *max_fails*. If this
    is triggered all running objects will continue to run and all objects waiting will be canceled.

    The function will return 1 if any test case has a state with a level greater than
    *min_fail_state*, otherwise a 0 is returned.
    """
    if platform.python_version() < '3.7':
        raise RuntimeError("Python 3.7 or greater required.")

    # Capture for computing the total execution time for all test cases
    start_time = time.time()

    # Arguments that will be passed to the `TestCase` object created
    tc_kwargs = dict()
    tc_kwargs['controllers'] = controllers
    tc_kwargs['min_fail_state'] = min_fail_state

    # Setup process pool, the result_map is used to collecting results returned from workers
    ctx = multiprocessing.get_context(MULTIPROCESSING_CONTEXT)
    manager = ctx.Manager()
    executor = concurrent.futures.ProcessPoolExecutor(mp_context=ctx, max_workers=n_threads)

    futures = list()  # pool workers
    testcases = dict()  # unique_id to TestCase object
    readers = list()
    for runners in groups:
        result_send = manager.Queue()
        readers.append(result_send)
        local = [
            TestCase(runner=runner, **tc_kwargs) for runner in runners
            if _apply_filters(filters, runner)
        ]
        futures.append(executor.submit(_execute_testcases, local, result_send, timeout))
        testcases.update({tc.unique_id: tc for tc in local})

    # Loop until the Future objects are complete
    n_fails = 0
    while any(f.running() for f in futures):
        for reader in readers:
            try:
                unique_id, progress, state, results = reader.get_nowait()
                tc = testcases.get(unique_id)
                _report_progress_and_results(tc, formatter, progress, state, results)
                if tc.finished:
                    n_fails += int(tc.state.level >= min_fail_state.level)
            except queue.Empty:
                pass

            for tc in filter(lambda obj: obj.running, testcases.values()):
                formatter.reportProgress(tc)

        if n_fails >= max_fails:
            for f in futures:
                f.cancel()

    # Shutdown the pool of workers.
    executor.shutdown()

    # Raise any exceptions from Future objects
    for f_obj in filter(lambda f: not f.cancelled(), futures):
        exc = f_obj.exception()
        if exc is not None:
            raise exc

    # Report any messages that remain in the Queues
    while any(not r.empty() for r in readers):
        for reader in [r for r in readers if not r.empty()]:
            unique_id, progress, state, results = reader.get_nowait()
            tc = testcases.get(unique_id)
            _report_progress_and_results(tc, formatter, progress, state, results)

    # If there are test cases not finished they must have been skipped because of the early max
    # failures exit, So, mark them as finished and report.
    for tc in filter(lambda tc: not tc.finished, testcases.values()):
        tc.setProgress(TestCase.Progress.FINISHED)
        tc.setState(TestCase.Result.SKIP)
        tc.setResults({
            tc.name():
            TestCase.Data(TestCase.Result.SKIP, None, '', f"Max failures of {max_fails} exceeded.",
                          ['max failures reached'])
        })
        formatter.reportProgress(tc)
        formatter.reportResults(tc)

    # Produce exit code and return
    print(formatter.reportComplete(testcases.values(), start_time))
    failed = sum(tc.state.level >= min_fail_state.level for tc in testcases.values())
    return 1 if failed > 0 else 0


def _apply_filters(filters, runner):
    """
    Return False if any of supplied `base.Filter` object(s) in *filters* apply to the *runner*.


    If *filters* is `None` then True is also returned.
    """
    remove = any(f.apply(runner) for f in filters) if (filters is not None) else False
    return not remove


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
        results = {
            tc.name(): TestCase.Data(TestCase.Result.FATAL, None, None, traceback.format_exc(),
                                     None)
        }
    conn.send((state, results))


def _execute_testcases(testcases, result_send, timeout):
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

    # Storage for the state of complete TestCase. This is used to make sure that tests with
    # 'requires' parameter have executed and passed.
    test_results = dict()

    # TestCase objects are executed in order recieved
    for tc in testcases:

        # If a TestCase Runner object has a 'requires' parameter, make sure that those tests have
        # run and passed.
        requires = tc.runner.getParam('requires')
        if (requires is not None):

            # Case where the names do not exist, thus cannot have run. The 'discover' method creates
            # the names for the Runner (i.e., TestCase) using HIT information. However, it is desired
            # that handling 'requires' have no knowledge of HIT. Thus, the just check that the
            # known names end with names in 'requires'.
            not_in = [
                name for name in requires if not any(k.endswith(name) for k in test_results.keys())
            ]
            if not_in:
                msg = "For the test '{}', the required test(s) '{}' have not executed. Either the names provided the the 'requires' parameter are incorrect or the tests are in the wrong order.".format(
                    tc.name(), ', '.join(not_in))
                state = TestCase.Result.FATAL
                results = {
                    tc.name(): TestCase.Data(state, None, None, msg, ['unknown required test(s)'])
                }
                test_results[tc.name()] = state
                result_send.put((tc.unique_id, TestCase.Progress.FINISHED, state, results))
                continue

            # Case when names do exist, but have not passed. See comment above for "not_in" variable.
            not_pass = [
                name for name in requires
                if any((k.endswith(name) and v.level > 0) for k, v in test_results.items())
            ]
            if not_pass:
                msg = "For the test '{}', the required test(s) '{}' have not executed and passed.".format(
                    tc.name(), ', '.join(not_pass))
                state = TestCase.Result.SKIP
                results = {tc.name(): TestCase.Data(state, None, None, msg, ['failed dependency'])}
                test_results[tc.name()] = state
                result_send.put((tc.unique_id, TestCase.Progress.FINISHED, state, results))
                continue

        # Execute the TestCase object, this is done in separate process to allow for the timeout
        # to be applied to the execution
        result_send.put((tc.unique_id, TestCase.Progress.RUNNING, None, None))
        ctx = multiprocessing.get_context(MULTIPROCESSING_CONTEXT)
        conn_recv, conn_send = ctx.Pipe(False)
        proc = ctx.Process(target=_execute_testcase, args=(tc, conn_send))
        proc.start()

        if conn_recv.poll(timeout):
            state, results = conn_recv.recv()
        else:
            proc.terminate()
            state = TestCase.Result.TIMEOUT
            results = {
                tc.name():
                TestCase.Data(TestCase.Result.TIMEOUT, None, None, None,
                              [f'max time ({timeout}) exceeded'])
            }

        proc.join()
        proc.close()

        test_results[tc.name()] = state
        result_send.put((tc.unique_id, TestCase.Progress.FINISHED, state, results))


def _report_progress_and_results(tc, formatter, progress, state, results):
    """
    Helper function for reporting results/progress during a call to the `run` function.

    The `TestCase` object in *tc* if updated with *progress*, *state*, and *results* if the supplied
    progress differs from the existing progress in the object. The progress and results are
    displayed to the screen using the `Formatter` object supplied in *formatter*.
    """
    if (progress is not None) and (tc.progress != progress):
        tc.setProgress(progress)
        if progress == TestCase.Progress.FINISHED:
            tc.setState(state)
            tc.setResults(results)
            formatter.reportResults(tc)


if __name__ == '__main__':  # pragma: no cover
    # This is here for quick testing
    from moosetools.moosetest.formatters import BasicFormatter
    from moosetools.moosetest.base import make_runner, make_differ
    sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))
    from _helpers import TestController, TestRunner, TestDiffer

    fm = BasicFormatter(progress_interval=3)
    groups = [None] * 3
    groups[0] = [TestRunner(name='a.a', sleep=1), TestRunner(name='a.b', sleep=4)]
    groups[1] = [TestRunner(name='b.a', sleep=1), TestRunner(name='b.b', sleep=5)]
    groups[2] = [TestRunner(name='c.a', sleep=1), TestRunner(name='c.b', sleep=6)]

    Run(groups, tuple(), fm, n_threads=2)
