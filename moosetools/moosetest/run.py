import os
import sys
import time
import traceback
import queue
import concurrent.futures
import multiprocessing
import time

from moosetools.moosetest.base import TestCase, RedirectOutput

def run(groups, controllers, formatter, n_threads=None, timeout=None, max_fails=sys.maxsize,
        min_fail_state=TestCase.Result.TIMEOUT):
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
    *min_fail*state*, otherwise a 0 is returned.
    """

    # NOTE: This function is the heart of moosetest. Significant effort went into the design,
    #       including getting 100% test coverage and handling all the corner cases found during
    #       that process. If you are going to change this function make sure you test the changes
    #       thoroughly. If something does not work, please be kind...this was non-trivial (at least
    #       for Andrew).

    # Capture for computing the total execution time for all test cases
    start_time = time.time()

    # Arguments that will be passed to the `TestCase` object created
    tc_kwargs = dict()
    tc_kwargs['controllers'] = controllers
    tc_kwargs['min_fail_state'] = min_fail_state

    # Setup process pool, the result_queue is used to collecting results returned from workers
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=n_threads)
    manager = multiprocessing.Manager()
    result_queue = manager.Queue()

    futures = list() # pool workers
    testcase_map = dict() # individual cases to allow report while others run

    for runners in groups:
        testcases = [TestCase(runner=runner, **tc_kwargs) for runner in runners]
        futures.append(executor.submit(_execute_testcases, testcases, result_queue, timeout))
        for tc in testcases:
            testcase_map[tc.getParam('_unique_id')] = tc

    # Loop until all the test cases are finished or the number of failures is reached
    while any(not tc.finished for tc in testcase_map.values()):#
        #time.sleep(0.1) # no reason to hammer the main process, you can wait 0.1 sec...
        _running_results(testcase_map, result_queue, formatter)
        _running_progress(testcase_map, formatter)

        # If the number of failures has been reached, exit the loop early
        n_fails = sum(tc.state.level >= min_fail_state.level for tc in testcase_map.values() if tc.finished)
        if n_fails >= max_fails:
            break

    # Cancel all workers. There is only something to cancel if the previous loop exited early
    # because of hitting the max failures. After canceling, continue reporting progress/results
    # until all the workers are finished. It is also possible that the queue contains data that
    # was present
    for f in futures: f.cancel()
    while any(f.running() for f in futures) or not result_queue.empty():
        _running_results(testcase_map, result_queue, formatter)
        _running_progress(testcase_map, formatter)

    # Any test cases that are not finished have been skipped because of the early max failures exit
    # of the first loop. So, mark them as finished and report.
    for tc in filter(lambda tc: not tc.finished, testcase_map.values()):
        tc.setProgress(TestCase.Progress.FINISHED)
        tc.setState(TestCase.Result.SKIP)
        tc.setResults({tc.name(): TestCase.Data(TestCase.Result.SKIP, None, '', f"Max failures of {max_fails} exceeded.", ['max failures reached'])})
        formatter.reportProgress(tc)
        formatter.reportResults(tc)

    # At this point all the workers should be done and the data collected from the result_queue.
    # Just to be sure catch the case where there is still data hanging around. This shouldn't be
    # possible to trigger, but it helped catch some bugs when writing and testing the function so
    # is should stay.
    if not result_queue.empty():
        with RedirectOutput() as out:
            while not result_queue.empty():
                _running_results(testcase_map, result_queue, formatter)
                _running_progress(testcase_map, formatter)
        msg = "Unexpected progress/result output found.\nsys.stdout:\n{}\nsys.stderr:\n{}"
        raise RuntimeError(msg.format(out.stdout, out.stderr))

    print(formatter.reportComplete(testcase_map.values(), start_time))

    # When running the tests, there were cases that gave the an error that ended with:
    #
    #     File "/Users/.../lib/python3.8/multiprocessing/popen_fork.py", line 69, in _launch
    #       child_r, parent_w = os.pipe()
    # OSError: [Errno 24] Too many open files
    #
    # Adding a call to shutdown the pool of workers seems to get rid of that problem.
    executor.shutdown()

    failed = sum(tc.state.level >= min_fail_state.level for tc in testcase_map.values())
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
        results = {tc.name(): TestCase.Data(TestCase.Result.FATAL, None, '', traceback.format_exc(), None)}
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
            results = {tc.name(): TestCase.Data(TestCase.Result.SKIP, None, '', skip_message, ['dependency'])}
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
            results = {tc.name(): TestCase.Data(TestCase.Result.TIMEOUT, None, '', '', [f'max time ({timeout}) exceeded'])}

        q.put((unique_id, TestCase.Progress.FINISHED, state, results))

        if (state.level > 0):
            skip_message = f"A previous test case ({tc.name()}) in the group returned a non-zero state of {state}."


def _running_results(testcase_map, result_queue, formatter):
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
            formatter.reportResults(tc)
        result_queue.task_done()

    except queue.Empty:
        pass

def _running_progress(testcase_map, formatter):
    """
    Helper function for reporting state of the `TestCase` objects.

    The supplied `TestCase` objects *testcase_map* are each checked, if the case is running the
    progress is reported. If more than *max_fails* is reached the processes in *futures* are canceled.
    """
    for tc in testcase_map.values():
        if tc.running:
            formatter.reportProgress(tc)



def fuzzer(seed=1980, timeout=(3,10), max_fails=(15,100), progress_interval=(3,15),
           group_num=(15,50), group_name_len=(6,25),
           controller_num=(1,6), controller_skip=0.05, controller_raise=0.05, controller_error=0.1,
           differ_num=(0,3), differ_raise=0.01, differ_error=0.1, differ_fatal=0.1, differ_platform=0.1, differ_name_len=(6,15),
           runner_num=(1,3), runner_raise=0.01, runner_error=0.1, runner_fatal=0.05, runner_sleep=(0.5,10), runner_platform=0.1, runner_name_len=(4,29)):
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
        if random.uniform(0,1) < prob:
            prefix = "{}_platform".format(random.choice(ctrls).getParam('prefix'))
            value = tuple(set(random.choices(['Darwin', 'Linux', 'Windows'], k=random.randint(1,3))))
            kwargs[prefix] = value

    def gen_bool_with_odds(prob):
        return random.uniform(0,1) < prob

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
