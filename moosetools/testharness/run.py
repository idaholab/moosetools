import os
import io
import sys
import time
import concurrent.futures
import multiprocessing
import threading
from moosetools.moosetest.base import State, TestCase
from moosetools.moosetest.runners import ProcessRunner



# TODO
# - implement timeout failsafe to avoid handing
# - show run time information in Runner/Testers (probably add to output from TestCase.execute)
# - pass lists of testers to "run_testcases"
# - add percent complete to output

def run_testcases(testcase):
    return testcase.execute()

def main():
    n_threads = 3
    #tc = TestCase(None, None)
    #tc.evaluate()


    pool = concurrent.futures.ThreadPoolExecutor(n_threads)

    queue = list()
    for i in range(5):
        runner = ProcessRunner(name='foo/bar.{}'.format(i), command=('sleep', str(i)))
        tc = TestCase(runner=runner)
        f = pool.submit(run_testcases, tc)
        f.add_done_callback(tc.doneCallback)
        #print(dir(f))
        queue.append(tc)

    #futures = list()
    #for testcase in queue:
    #    f = pool.submit(run_testcases, testcase)
    #    f.add_done_callback(testcase.done)
        #futures.append(f)



    finished = list()
    while len(queue) > 0:
        indices_to_remove = list()
        for i, tc in enumerate(queue):
            tc.report()

            if tc.getProgress() == TestCase.Progress.FINISHED:
                indices_to_remove.append(i)

        for i in reversed(indices_to_remove):
            queue.pop(i)
        time.sleep(0.5)



    # LOOP THROUGH TEST CASES AND POP CLOSED
    # while waiting, if pop the finished probably don't need done and closed
    #num_finished = 0
    #while num_finished < num:
    #    for testcase, future in zip(waiting, futures):
    #        if testcase.getProgress() == TestCase.Progress.DONE:
    #            num_finished += 1
    #
    #        testcase.report()
            #state = testcase.getState()
            #if state != State.CLOSED:
            #    print(state)
            #if state == State.DONE:
            #    print(testcase.results())

            #elif testcase.state() == State.RUNNING:
            #    update = testcase.update()
            #    if update is not None:
            #        print(update)



if __name__ == '__main__':
    import logging
    logging.basicConfig()
    sys.exit(main())


"""
Setup TestCase to stream during execute and execute into sections and be sure to return a
status and stream
"""
