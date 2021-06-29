#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
import os
import random
import string
from moosetools import moosetest

sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))
from _helpers import TestController, TestRunner, TestDiffer


def _gen_name(rng):
    """
    Return a name with length in the range of *rng*.

    The *rng* variable is expected to be a pair integers to be passed `random.randint` function.
    """
    return ''.join(random.sample(string.ascii_letters, random.randint(*rng)))


def _gen_platform(ctrls, prob, kwargs):
    """
    Randomly set the "platform" that `TestCase` should execute.

    The *kwargs* for the supplied `Controller` objects in *ctrls* are randomly assigned an OS
    platform restriction if a generated random number is less then the desired probability of *prob*.
    """
    if _gen_bool_with_odds(prob):
        prefix = "{}_platform".format(random.choice(ctrls).getParam('prefix'))
        value = tuple(
            set(random.choices(['Darwin', 'Linux', 'Windows'], k=random.randint(1, 3))))
        kwargs[prefix] = value


def _gen_bool_with_odds(prob):
    """
    Return True if a generated random integer (0,1) is less than the desired probability of *prob*.
    """
    return random.uniform(0, 1) < prob


def fuzzer(timeout=(3, 10),
           max_fails=(int(15), int(100)),
           progress_interval=(3, 15),
           group_num=(int(15), int(50)),
           group_name_len=(int(6), int(25)),
           controller_num=(int(1), int(6)),
           controller_skip=0.05,
           controller_raise=0.05,
           controller_error=0.1,
           differ_num=(int(0), int(3)),
           differ_raise=0.01,
           differ_error=0.1,
           differ_fatal=0.1,
           differ_platform=0.1,
           differ_name_len=(int(6), int(15)),
           runner_num=(int(1), int(5)),
           runner_raise=0.01,
           runner_error=0.1,
           runner_fatal=0.05,
           runner_sleep=(0.5, 10),
           runner_platform=0.1,
           runner_name_len=(int(4), int(29)),
           requires_error=0.01,
           requires_use=0.25):
    """
    A tool for calling `run` function with randomized test cases.
    """

    # Controller objects
    controllers = list()
    for i, n_controllers in enumerate(range(random.randint(*controller_num))):
        name_start = random.choice(string.ascii_letters)
        kwargs = dict()
        kwargs['stdout'] = True
        kwargs['stderr'] = True
        kwargs['prefix'] = "ctrl{:0.0f}".format(i)
        kwargs['skip'] = _gen_bool_with_odds(controller_skip)
        kwargs['error'] = _gen_bool_with_odds(controller_error)
        kwargs['raise'] = _gen_bool_with_odds(controller_raise)
        controllers.append(TestController(object_name=name_start, **kwargs))
    controllers = tuple(controllers)

    # Runners/Differs
    groups = list()
    for n_groups in range(random.randint(*group_num)):
        runners = list()
        group_name = _gen_name(group_name_len)
        for n_runners in range(random.randint(*runner_num)):
            differs = list()
            for n_differs in range(random.randint(*differ_num)):
                kwargs = dict()
                kwargs['name'] = _gen_name(differ_name_len)
                kwargs['stdout'] = True
                kwargs['stderr'] = True
                kwargs['error'] = _gen_bool_with_odds(differ_error)
                kwargs['raise'] = _gen_bool_with_odds(differ_raise)
                kwargs['fatal'] = _gen_bool_with_odds(differ_fatal)
                _gen_platform(controllers, differ_platform, kwargs)
                differs.append(moosetest.base.make_differ(TestDiffer, controllers, **kwargs))

            kwargs = dict()
            kwargs['name'] = f"{group_name}/{_gen_name(runner_name_len)}"
            kwargs['differs'] = tuple(differs)
            kwargs['stdout'] = True
            kwargs['stderr'] = True
            kwargs['error'] = _gen_bool_with_odds(runner_error)
            kwargs['raise'] = _gen_bool_with_odds(runner_raise)
            kwargs['fatal'] = _gen_bool_with_odds(runner_fatal)
            kwargs['sleep'] = random.uniform(*runner_sleep)
            _gen_platform(controllers, runner_platform, kwargs)
            runners.append(moosetest.base.make_runner(TestRunner, controllers, **kwargs))

            if _gen_bool_with_odds(requires_error):
                index = random.randint(0, len(runners) - 1)
                runners[index].parameters().setValue('requires', (_gen_name((3, 8)), ))

        if _gen_bool_with_odds(requires_use) and len(runners) > 2:
            index = random.randint(0, len(runners) - 1)
            count = random.randint(0, len(runners) - 2)
            names = list(set(r.name() for r in runners
                             if r.name() != runners[index].name()))[:count]
            runners[index].parameters().setValue('requires', tuple(names))

        groups.append(runners)

    # Formatter
    kwargs = dict()
    kwargs['progress_interval'] = random.randint(*progress_interval)
    formatter = moosetest.formatters.BasicFormatter(**kwargs)

    # Run
    kwargs = dict()
    kwargs['timeout'] = random.randint(*timeout)
    kwargs['max_fails'] = random.randint(*max_fails)
    kwargs['min_fail_state'] = random.choice([r for r in moosetest.base.TestCase.Result])
    return moosetest.run(groups, controllers, formatter, **kwargs)
