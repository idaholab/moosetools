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
    executor = concurrent.futures.ProcessPoolExecutor(mp_context=ctx,
                                                      max_workers=min(n_threads, len(groups)))

    futures = list()  # pool workers
    testcases = dict()  # unique_id to TestCase object
    readers = list()
    for runners in groups:
        result_recv, result_send = ctx.Pipe(False)
        readers.append(result_recv)
        local = [TestCase(runner=runner, **tc_kwargs) for runner in runners]
        futures.append(executor.submit(_execute_testcases, local, result_send, timeout))
        testcases.update({tc.unique_id:tc for tc in local})

    # Loop until all the test cases are finished, the number of failures is reached, or the Future
    # objects are complete
    n_fails = 0
    while any(f.running() for f in futures):
        for reader in multiprocessing.connection.wait(readers, 0.1):
            try:
                unique_id, progress, state, results = reader.recv()
                tc = testcases.get(unique_id)
                _report_progress_and_results(tc, formatter, progress, state, results)
                if tc.finished:
                    n_fails += int(tc.state.level >= min_fail_state.level)
            except EOFError:
                pass

        #if n_fails >= max_fails:
        #    break
    #for conn in multiprocessing.connection.wait(readers):
    #    unique_id, progress, state, results = conn.recv()
    #    tc = testcase_map.get(unique_id)
    #    _report_progress_and_results(tc, formatter, progress, state, results)
    #print("HERE")

    # TODO: Make sure all connections are closes


    """
        n_fails = 0
        count = 0
        for tc in testcases:
            if tc.finished:
                n_fails += int(tc.state.level >= min_fail_state.level)
            else:
                count += 1

            #if tc.unique_id in result_map:
                #progress, state, results = result_map.get(tc.unique_id)
                #_report_progress_and_results(tc, formatter, progress, state, results)

            # TODO: this is causing a deadlock
            progress, state, results = result_map.pop(tc.unique_id, (None, None, None))
            _report_progress_and_results(tc, formatter, progress, state, results)

        if n_fails >= max_fails:
            break
    """

    # Shutdown the pool of workers.
    if platform.python_version() >= '3.9.0':
        executor.shutdown(cancel_futures=True)
    else:
        for f in futures:
            f.cancel()
        executor.shutdown()

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


def _execute_testcase(tc, conn, legacy=False):
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
            tc.name(): TestCase.Data(TestCase.Result.FATAL, None, '', traceback.format_exc(), None)
        }

    return state, results
    #conn.send((state, results))

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
    skip_message = None


    for tc in testcases:
        unique_id = tc.unique_id

        if skip_message:
            state = TestCase.Result.SKIP
            results = {
                tc.name(): TestCase.Data(TestCase.Result.SKIP, None, '', skip_message,
                                         ['dependency'])
            }
            #result_map[unique_id] = (TestCase.Progress.FINISHED, state, results)
            result_send.send((unique_id, TestCase.Progress.FINISHED, state, results))
            continue

        result_send.send((unique_id, TestCase.Progress.RUNNING, None, None))
        #result_map[unique_id] = (TestCase.Progress.RUNNING, None, None)

        state, results = _execute_testcase(tc, None)

        """
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
                TestCase.Data(TestCase.Result.TIMEOUT, None, '', '',
                              [f'max time ({timeout}) exceeded'])
            }

        proc.join()
        proc.close()
        """
        #result_map[unique_id] = (TestCase.Progress.FINISHED, state, results)
        result_send.send((unique_id, TestCase.Progress.FINISHED, state, results))
        if (state.level > 0):
            skip_message = f"A previous test case ({tc.name()}) in the group returned a non-zero state of {state}."


    #result_send.send((None, None, None, None)) # close


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

    elif tc.running:
        formatter.reportProgress(tc)


def fuzzer(seed=1980,
           timeout=(3, 10),
           max_fails=(15, 100),
           progress_interval=(3, 15),
           group_num=(15, 50),
           group_name_len=(6, 25),
           controller_num=(1, 6),
           controller_skip=0.05,
           controller_raise=0.05,
           controller_error=0.1,
           differ_num=(0, 3),
           differ_raise=0.01,
           differ_error=0.1,
           differ_fatal=0.1,
           differ_platform=0.1,
           differ_name_len=(6, 15),
           runner_num=(1, 3),
           runner_raise=0.01,
           runner_error=0.1,
           runner_fatal=0.05,
           runner_sleep=(0.5, 10),
           runner_platform=0.1,
           runner_name_len=(4, 29)):
    """
    A tool for calling `run` function with randomized test cases.
    """
    # This is more of a test object, so I wanted to keep the testing related import out of the
    # main functions for the run command.
    import random
    import string
    from moosetools.moosetest.formatters import BasicFormatter
    from moosetools.moosetest.base import make_runner, make_differ
    sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))
    from _helpers import TestController, TestRunner, TestDiffer

    def gen_name(rng):
        return ''.join(random.sample(string.ascii_letters, random.randint(*rng)))

    def gen_platform(ctrls, prob, kwargs):
        if random.uniform(0, 1) < prob:
            prefix = "{}_platform".format(random.choice(ctrls).getParam('prefix'))
            value = tuple(
                set(random.choices(['Darwin', 'Linux', 'Windows'], k=random.randint(1, 3))))
            kwargs[prefix] = value

    def gen_bool_with_odds(prob):
        return random.uniform(0, 1) < prob

    # Controller objects
    controllers = list()
    for i, n_controllers in enumerate(range(random.randint(*controller_num))):
        name_start = random.choice(string.ascii_letters)
        kwargs = dict()
        kwargs['stdout'] = True
        kwargs['stderr'] = True
        kwargs['prefix'] = "ctrl{:0.0f}".format(i)
        kwargs['skip'] = gen_bool_with_odds(controller_skip)
        kwargs['error'] = gen_bool_with_odds(controller_error)
        kwargs['raise'] = gen_bool_with_odds(controller_raise)
        controllers.append(TestController(object_name=name_start, **kwargs))
    controllers = tuple(controllers)

    # Runners/Differs
    groups = list()
    for n_groups in range(random.randint(*group_num)):
        runners = list()
        group_name = gen_name(group_name_len)
        for n_runners in range(random.randint(*runner_num)):
            differs = list()
            for n_differs in range(random.randint(*differ_num)):
                kwargs = dict()
                kwargs['name'] = gen_name(differ_name_len)
                kwargs['stdout'] = True
                kwargs['stderr'] = True
                kwargs['error'] = gen_bool_with_odds(differ_error)
                kwargs['raise'] = gen_bool_with_odds(differ_raise)
                kwargs['fatal'] = gen_bool_with_odds(differ_fatal)
                gen_platform(controllers, differ_platform, kwargs)
                differs.append(make_differ(TestDiffer, controllers, **kwargs))

            kwargs = dict()
            kwargs['name'] = f"{group_name}/{gen_name(runner_name_len)}"
            kwargs['differs'] = tuple(differs)
            kwargs['stdout'] = True
            kwargs['stderr'] = True
            kwargs['error'] = gen_bool_with_odds(runner_error)
            kwargs['raise'] = gen_bool_with_odds(runner_raise)
            kwargs['fatal'] = gen_bool_with_odds(runner_fatal)
            kwargs['sleep'] = random.uniform(*runner_sleep)
            gen_platform(controllers, runner_platform, kwargs)
            runners.append(make_runner(TestRunner, controllers, **kwargs))

        groups.append(runners)

    # Formatter
    kwargs = dict()
    kwargs['progress_interval'] = random.randint(*progress_interval)
    formatter = BasicFormatter(**kwargs)

    # Run
    kwargs = dict()
    kwargs['timeout'] = random.randint(*timeout)
    kwargs['max_fails'] = random.randint(*max_fails)
    kwargs['min_fail_state'] = random.choice([r for r in TestCase.Result])
    return run(groups, controllers, formatter, **kwargs)


if __name__ == '__main__':
    from moosetools.moosetest.formatters import BasicFormatter
    from moosetools.moosetest.base import make_runner, make_differ
    sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))
    from _helpers import TestController, TestRunner, TestDiffer

    fm = BasicFormatter()
    groups = [None] * 3
    groups[0] = [TestRunner(name='a.a', sleep=1), TestRunner(name='a.b', sleep=2)]
    groups[1] = [TestRunner(name='b.a', sleep=1), TestRunner(name='b.b', sleep=2)]
    groups[2] = [TestRunner(name='c.a', sleep=1), TestRunner(name='c.b', sleep=2)]

    run(groups, tuple(), fm, n_threads=2)
