import os
import io
import sys
import time
import concurrent.futures
import multiprocessing
import threading
import queue
from moosetools.moosetest.base import State, TestCase
from moosetools.moosetest.runners import ProcessRunner

"""
TODO:
- Create discover function to return the test case groups, use ThreadPool and return TestCase  objects
- Run should run the groups
"""

# TODO
# - implement timeout failsafe to avoid handing
# - show run time information in Runner/Testers (probably add to output from TestCase.execute)
# - pass lists of testers to "run_testcases"
# - add percent complete to output

def run_testcases(testcases, pipe):
    for tc in testcases:
        result = tc.execute()
        #pipe.send(tc.get('_job_id'), result)



def make_runner(i, r=None):
    return ProcessRunner(name='foo/bar.i'.format(i), command=('sleep', str(i)))


def not_main():

    """
       # Tokenization
        jobs = []
        conn1, conn2 = multiprocessing.Pipe(False)
        for chunk in mooseutils.make_chunks(nodes, num_threads):
            p = multiprocessing.Process(target=target, args=(chunk, conn2))
            p.start()
            jobs.append(p)

        while any(job.is_alive() for job in jobs):
            if conn1.poll():
                data = conn1.recv()
                for uid, attributes, out in data:
                    node = self._page_objects[uid]
                    Executioner.setMutable(node, True)
                    node.attributes.update(attributes)
                    Executioner.setMutable(node, False)

                    if container is not None:
                        container[uid] = out

        LOG.info('Finished %s [%s sec.]', prefix, time.time() - t)
    """

    #jobs = multiprocessing.JoinableQueue()

    #manager = multiprocessing.Manager()
    #jobs = manager.Queue()
    #state = multiprocessing.dict()
    #recv, send = multiprocessing.Pipe(False) # unidirectional

    send = None


    #conn1, conn2 = multiprocessing.Pipe(False)

    n_threads = 2

    count = 4

    test_cases = list()

    pool = concurrent.futures.ProcessPoolExecutor(n_threads)

    futures = list()
    for i in range(count):
        r = make_runner(i)
        tc = [TestCase(runner=r, _job_id=i)]
        test_cases += tc

        f = pool.submit(run_testcases, tc, initargs=(send, ))
        #f.add_done_callback()
        futures.append(f)



        #futures.append(f)



    #pool = multiprocessing.pool.ProcessPool(n_threads)


    """
    for tid in range(n_threads):
        p = multiprocessing.Process(target=run_testcase, args=(jobs, send))
        p.start()
        processes.append(p)



    while any(p.is_alive() for p in processes):
        if recv.poll():
            data = recv.recv()
            print(data)

    """



    #queue = list()
    #for i in range(5):
    #    runner = ProcessRunner(name='foo/bar.{}'.format(i), command=('sleep', str(i)))
    #    tc = TestCase(runner=runner)
    #    f = pool.submit(run_testcases, tc)
    #    f.add_done_callback(tc.doneCallback)
    #    #print(dir(f))
    #    queue.append(tc)




def run_the_testcases(testcases, comm):
    for tc in testcases:
        r = tc.execute()
        comm.put((tc._runner.name(), r))



def main():
    n_threads = 2
    #tc = TestCase(None, None)
    #tc.evaluate()


    comm = queue.Queue()
    pool = concurrent.futures.ThreadPoolExecutor(n_threads)
    #pool = concurrent.futures.ProcessPoolExecutor(n_threads)

    jobs = dict()
    for i in range(5):
        runner = ProcessRunner(name='foo/bar.{}'.format(i), command=('sleep', str(i)))
        tc = TestCase(runner=runner)
        f = pool.submit(run_the_testcases, [tc], comm)
        #f.add_done_callback(tc.doneCallback)
        #print(dir(f))
        jobs[tc._runner.name()] = tc

    #futures = list()
    #for testcase in queue:
    #    f = pool.submit(run_testcases, testcase)
    #    f.add_done_callback(testcase.done)
        #futures.append(f)



    finished = list()
    while len(jobs) > 0:
        if not comm.empty():
            name, r = comm.get()
            testcase = jobs[name]
            testcase.setResult(r)


        indices_to_remove = list()
        for key in list(jobs.keys()):
            tc = jobs[key]
            tc.report()

            if tc.getProgress() == TestCase.Progress.FINISHED:
                jobs.pop(key)
        #or i in reversed(indices_to_remove):
        #    jobs.pop(i)
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
