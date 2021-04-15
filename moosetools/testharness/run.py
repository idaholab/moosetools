import sys
import concurrent.futures
from moosetools.moosetest.base import State, TestCase
from moosetools.moosetest.runners import ProcessRunner



def run_testcases(testcase):

    return testcase.execute()




def main():
    n_threads = 5
    #tc = TestCase(None, None)
    #tc.evaluate()


    waiting = list()
    for i in range(10):
        waiting.append(TestCase(ProcessRunner(name='foo/bar.{}'.format(i), command=('sleep', str(i)))))

    num = len(waiting)
    pool = concurrent.futures.ThreadPoolExecutor(n_threads)
    futures = [None]*num
    for i, testcase in enumerate(waiting):
        futures[i] = pool.submit(run_testcases, testcase)
        futures[i].add_done_callback(testcase.done)

    num_finished = 0
    while num_finished < num:
        for testcase, future in zip(waiting, futures):
            if testcase.getState() == TestCase.Progress.DONE:
                num_finished += 1

            testcase.report()
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
    sys.exit(main())
