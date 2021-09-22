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
import collections
import faulthandler
import contextlib
import signal
import io
from moosetools.moosetest.base import TestCase



# By default macOS use 'spawn' for creating processes. However, I had problems with the following
# warning being produced. I couldn't figure out that root cause of the warning with respect to the
# code here. It might be related to https://bugs.python.org/issue38119. Using 'fork' does not result
# in the warning, so I went with that until I figure out the reason.
#
# UserWarning: resource_tracker: There appear to be 5 leaked semaphore objects to clean up at shutdown
MULTIPROCESSING_CONTEXT = 'fork'

class SharedData(object):
    def __init__(self, manager, min_fail_state, max_fails):
        self.testcases = manager.list()
        self.lock = manager.Lock()
        self.num_failed = manager.Value('i', 0)
        self.min_fail_state = min_fail_state
        self.max_fails = max_fails


class Timer(object):
    def __init__(self):
        self.__start_time = None
        self.__execute_time = None
        #self.__thread_timer = threading.Timer()

    @property
    def time(self):
        return self.__execute_time

    def __enter__(self):
        self.__start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            raise
        self.__execute_time = time.perf_counter() - self.__start_time



#print_lock = threading.Lock()

def run(groups,
        controllers,
        formatter,
        *,
        n_threads=os.cpu_count(),
        max_fails=sys.maxsize,
        min_fail_state=TestCase.Result.TIMEOUT, # TODO: Make this a Runner?
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
    number returned by `os.cpu_count`. Each `Runner` object will execute and wait for the timeout
    (in seconds) as specified in the `Runner` to complete, before a timeout error is produced.
    Execution will continue until all objects had executed or timeout, unless the number of failures
    exceeds *max_fails*. If this is triggered all running objects will continue to run and all
    objects waiting will be canceled.

    The function will return 1 if any test case has a state with a level greater than
    *min_fail_state*, otherwise a 0 is returned.
    """
    #faulthandler.enable()

    if platform.python_version() < '3.7':
        raise RuntimeError("Python 3.7 or greater required.")

    # Capture for computing the total execution time for all test cases
    start_time = time.perf_counter()

    # Arguments that will be passed to the `TestCase` object created
    tc_kwargs = dict()
    tc_kwargs['controllers'] = controllers
    tc_kwargs['min_fail_state'] = min_fail_state



    #data = queue.Queue()
    #data = collections.deque()


    #async_results = list()
    #pool = multiprocessing.pool.ThreadPool(processes=28)
    #for runners in groups:
    #    local = [TestCase(runner=runner, **tc_kwargs) for runner in runners]
    #    async_results.append(pool.apply_async(_execute_testcases, args=(local, formatter)))
    #    print(local)

    testcases = list()
    futures = list()
    lock = threading.Lock()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=n_threads)

    for runners in groups:
        local = [TestCase(runner=runner, **tc_kwargs) for runner in runners]
        f = executor.submit(_execute_testcases, local, formatter, lock)
        #f.add_done_callback(_future_done_callback)
        futures.append(f)
        testcases += local

    #monitor = threading.Thread(target=_monitor, args=(formatter, testcases))
    #monitor.start()

   # print('here0')
    concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.ALL_COMPLETED)

    #data.append((None, None, None, None, None))
    #data.put((None, None, None, None, None))
    #monitor.join()
    #monitor.cancel()
    #concurrent.futures.wait([monitor], timeout=None, return_when=concurrent.futures.ALL_COMPLETED)
    #raise Exception('here1')

    executor.shutdown()
    #monitor.cancel()

    #pool.close()
    #print('here1')

    #pool.join()
    #print('here2')



    # Setup process pool, the result_map is used to collecting results returned from workers
    #ctx = multiprocessing.get_context(MULTIPROCESSING_CONTEXT)
    #executor = concurrent.futures.ProcessPoolExecutor()
    #executor = concurrent.futures.ThreadPoolExecutor(max_workers=16)
    #executor = MPIPoolExecutor(max_workers=None)
    #manager = ctx.Manager()
    #shared = None#SharedData(manager, min_fail_state, max_fails)
    #testcases = manager.list()
    #lock = manager.Lock()
    #num_failed = manager.Value('i', 0)

    #testcases = collections.deque() # see comment at end of https://docs.python.org/3/library/queue.html
    #lock = threading.Lock()

    #testcases = list()#collections.deque()

    #monitor = executor

    #print('here0')

    #futures = list()  # pool workers
    #with concurrent.futures.ThreadPoolExecutor() as executor:
    #for runners in groups:
    #    local = [TestCase(runner=runner, **tc_kwargs) for runner in runners]
    #    _execute_testcase(local, None)



    #print(testcases)
    #concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.ALL_COMPLETED)

    #futures = list()
    #with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
    #    for runners in groups:
    #        local = [TestCase(runner=runner, **tc_kwargs) for runner in runners]
    #        f = executor.submit(_execute_testcases, local, data)
    #        futures.append(f)

    #print("WTF")
    #for f in futures:
    #    print(f)
    #    for tc in f.result():
    #        print(tc.name())
    #        formatter.reportResults(tc)

    #print(data)

    #print('here')

    """
    while any(f.running() for f in futures):
        for conn in pipes:
            if conn.poll():
                try:
                    unique_id, progress, state, results = conn.recv()
                except EOFError:
                    pass
                else:
                    tc = testcases.get(unique_id)
                    _report_progress_and_results(tc, formatter, progress, state, results)


        #n_fails = sum(int(tc.state.level >= min_fail_state.level) for tc in testcases.values() if tc.finished)

        #for tc in filter(lambda obj: obj.running, testcases.values()):
        #    formatter.reportProgress(tc)

        #if n_fails >= max_fails:
        #    for f in futures:
        #        f.cancel()

    for conn in pipes:
        conn.close()
    """

    # Shutdown the pool of workers.
   # executor.shutdown()


    # Raise any exceptions from Future objects
    for f_obj in filter(lambda f: not f.cancelled(), futures):
        exc = f_obj.exception()
        if exc is not None:
            raise exc

    """
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
    """

    # Produce exit code and return
    formatter.reportComplete(testcases, start_time)
    failed = 0#sum(tc.state.level >= min_fail_state.level for tc in testcases)
    return 1 if failed > 0 else 0


def _monitor(formatter, testcases):

    finished = 0
    num_testcases = len(testcases)
    while finished < num_testcases:
        for tc in testcases:
            if tc.finished:
                formatter.reportResults(tc)
                tc.setInfo(progress=TestCase.Progress.REPORTED)
                finished += 1
            #elif tc.running:
            #    formatter.reportProgress(tc)

        time.sleep(0.1)







    """
    while True:
        try:
            unique_id, progress, state, results, t = data.popleft()
            #unique_id, progress, state, results, t = data.get_nowait()#get(timeout=0.01)
        except queue.Empty:
            pass
        except IndexError:
            pass
        else:
            if unique_id is None:
                return

            tc = testcases[unique_id]
            tc.setInfo(progress=progress, state=state, results=results)
            if progress == TestCase.Progress.RUNNING:
                tc.setStartTime(t)
            elif progress == TestCase.Progress.FINISHED:
                tc.setExecuteTime(t)
                formatter.reportResults(tc)

        for tc in testcases.values():
            if tc.running:
                formatter.reportProgress(tc)

        time.sleep(0.02)
    """

    """
    while True:#any(not f.done() for f in futures):
        try:
            unique_id, progress, state, results, t = data.get_nowait()
        except queue.Empty:
            pass
        else:
            data.task_done()

            if unique_id is None:
                return

            tc = testcases[unique_id]
            tc.setInfo(progress=progress, state=state, results=results)
            if progress == TestCase.Progress.RUNNING:
                tc.setStartTime(t)
            elif progress == TestCase.Progress.FINISHED:
                tc.setExecuteTime(t)
                formatter.reportResults(tc)

        for tc in testcases.values():
            if tc.running:
                formatter.reportProgress(tc)
    """

def _future_done_callback(f_obj):
    exc = f_obj.exception()
    if exc is not None:
        raise exc

"""
def _error_callback(*args):
    print('_error_callback', args)

def _callback(*args):
    print('_callback', args)
"""

def _execute_testcases(local, formatter, lock):
    """
    Function for executing groups of `TestCase` objects, *testcases*, each within a subprocess.

    This function is expected to be called from `concurrent.futures.ProcessPoolExecutor`. The *q*,
    which is a `multiprocessing.Queue` is used to send the results from the run of +each+ `TestCase`
    to the main process. This is done to allow the main process to report the results without
    waiting for the entire group to complete.

    See the `run` function for use.

    TODO: Create a Class for this?

    """
    for tc in local:
        #print(tc.name())

        #if shared.num_failed.value > shared.max_fails:
        #    results = {tc.name():TestCase.Data(TestCase.Result.SKIP, None, '', f"Max failures of {max_fails} exceeded.", ['max failures reached'])}
        #    tc.setInfo(progress=TestCase.Progress.FINISHED, state=state, results=results)
        #    formatter.reportResults(tc)
        #    continue

        """
        # If a TestCase Runner object has a 'requires' parameter, make sure that those tests have
        # run and passed.
        requires = tc.runner.getParam('requires')
        if (requires is not None):

            finished = set(tc.name() for tc in local if tc.finished)
            finished_and_passed = set(tc.name() for tc in local if (tc.finished and tc.state.level == 0))

            # Case where the names do not exist, thus cannot have run. The 'discover' method creates
            # the names for the Runner (i.e., TestCase) using HIT information. However, it is desired
            # that handling 'requires' have no knowledge of HIT. Thus, the just check that the
            # known names end with names in 'requires'.
            if not any(x.endswith(requires) for x in finished):
                msg = "For the test '{}', the required test(s) '{}' have not executed. Either the names provided the the 'requires' parameter are incorrect or the tests are in the wrong order.".format(
                    tc.name(), requires)
                state = TestCase.Result.FATAL
                results = {
                    tc.name(): TestCase.Data(state, None, None, msg, ['unknown required test'])
                }
                tc.setInfo(progress=TestCase.Progress.FINISHED, state=state, results=results)
                formatter.reportResults(tc)
                continue

            # Case when names do exist, but have not passed. See comment above for "not_in" variable.
            if not any(x.endswith(requires) for x in finished_and_passed):
                msg = "For the test '{}', the required test(s) '{}' have not executed and passed.".format(
                    tc.name(), requires)
                state = TestCase.Result.SKIP
                results = {tc.name(): TestCase.Data(state, None, None, msg, ['failed dependency'])}
                tc.setInfo(progress=TestCase.Progress.FINISHED, state=state, results=results)
                formatter.reportResults(tc)
                continue
        """

        #timeout = tc.runner.getParam('timeout')

        #data.put((tc.unique_id, TestCase.Progress.RUNNING, None, None, time.time()))
        #data.append((tc.unique_id, TestCase.Progress.RUNNING, None, None, time.time()))

        start_time = time.perf_counter()
        with lock:
            tc.setInfo(progress=TestCase.Progress.RUNNING, start_time=start_time)

        #stdout = io.StringIO()
        #stderr = io.StringIO()





        #with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        #tc.runner.execute()
        # TODO: Add timeout option to Timer
        try:
            state, results = tc.execute()
        except Exception:
            state = TestCase.Result.FATAL
            results = {
                tc.name(): TestCase.Data(TestCase.Result.FATAL, None, traceback.format_exc(), None)
            }

        #print(tc.name())
        #state, results = _execute_testcase(tc)
        #print("WTF")
        #raise Exception('WTF')

        #data.put((tc.unique_id, TestCase.Progress.FINISHED, state, results, tm.time))
        #data.append((tc.unique_id, TestCase.Progress.FINISHED, state, results, tm.time))

        #tc.setInfo(progress=TestCase.Progress.FINISHED, state=state, results=results)
        #with lock:
        tc.setInfo(progress=TestCase.Progress.FINISHED, state=state, results=results,
                   execute_time=start_time-time.perf_counter())
        formatter.reportResults(tc)

        #if int(tc.state.level >= shared.min_fail_state.level):
        #    with shared.lock:
        #        shared.num_failed += 1

def _execute_testcase_with_timeout(tc):
    """
    Function for executing the `TestCase` object *tc* with exception and timeout support.
    """
    timeout = tc.runner.getParam('timeout')
    mp_mode = tc.runner.getParam('multiprocessing_context') or MULTIPROCESSING_CONTEXT

    ctx = multiprocessing.get_context('fork')
    conn_recv, conn_send = ctx.Pipe(False)
    proc = ctx.Process(target=_execute_testcase, args=(tc, conn_send))
    proc.start()

    if conn_recv.poll(timeout):
        state, results = conn_recv.recv()
    else:
        state = TestCase.Result.TIMEOUT
        results = {
            tc.name():
            TestCase.Data(TestCase.Result.TIMEOUT, None, None, None,
                          [f'max time ({timeout}) exceeded'])
        }
    proc.join()
    return state, results


def _execute_testcase(tc):
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
    return state, results
    #conn_send.send((state, results))
    #conn.put((state, results))
    #conn_send.close()


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
