



def run_testcases(testcase):
    return testcase.execute()




def main():
    n_threads = 5
    #tc = TestCase(None, None)
    #tc.evaluate()


    waiting = list()
    for i in range(4):
        waiting.append(TestCase(Runner(i), [Differ(i+1), Differ(i+2)]))

    num = len(waiting)
    pool = concurrent.futures.ThreadPoolExecutor(n_threads)
    futures = [None]*num
    for i, testcase in enumerate(waiting):
        futures[i] = pool.submit(run_test_case, testcase)
        futures[i].add_done_callback(testcase.done)

    num_finished = 0
    while num_finished < num:
        for testcase, future in zip(waiting, futures):
            if future.done() and testcase.state() == State.DONE:
                print(testcase.results())
                num_finished += 1
            elif testcase.state() == State.RUNNING:
                update = testcase.update()
                if update is not None:
                    print(update)




    #running = list()

    #finished = list()

    """
    max_running = 4
    num = len(waiting)
    num_finished = 0#len(waiting)
    num_running = 0
    while num_finished < num:
        #time.sleep(0.1)
        num_running = 0
        for testcase in waiting:

            if (num_running < max_running) and (testcase.state() == State.WAITING):
                testcase.execute()
                num_running += 1

            if testcase.state() == State.FINISHED:
                num_finished += 1
                #print(testcase.results())

    for testcase in waiting:
        for d in testcase._differs:
            d._process.join()
        print(testcase.results())
    """



if __name__ == '__main__':
    sys.exit(main())
