#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import enum
import math
import collections
import time
import shutil
import textwrap
from moosetools.moosetest.base import Formatter, TestCase


class ShortenMode(enum.Enum):
    BEGIN = 0
    MIDDLE = 1
    END = 2


def shorten_line(text, max_length, mode=ShortenMode.MIDDLE, replace='...'):
    """
    Function for shortening single lines of content in *text*.

    The *text* string will be shortened to the length provided in *max_length* when the removed
    content replaced with the string in *replace*. The shortened string is returned and will have
    a total length of *max_length* plus the length of *replace*. Any leading or trailing white space
    surrounding the replaced text will be removed.

    The *mode* dictates where the replacement will happen, the begging, middle, or end of the string.
    """
    if '\n' in text:
        raise RuntimeError("The supplied text must be a single line, thus should not include '\n'.")
    if len(text) < max_length:
        return text

    if mode == ShortenMode.BEGIN:
        return '{}{}'.format(replace, text[-max_length:].lstrip())
    elif mode == ShortenMode.END:
        return '{}{}'.format(text[:max_length].rstrip(), replace)
    elif mode == ShortenMode.MIDDLE:
        n = math.floor(max_length / 2)
        return '{}{}{}'.format(text[:n].rstrip(), replace, text[-n:].lstrip())


def shorten_text(text, max_lines=10, mode=ShortenMode.MIDDLE, replace='...'):
    """
    Function for shortening multiple lines of text.

    The multiline *text* will be shortened to the *max_lines*. The removed content is replaced with
    the string in *replace*. The *mode* dictates where the replacement occurs: beginning, middle, or
    end.
    """
    lines = text.splitlines()
    if len(lines) < max_lines:
        return text

    if mode == ShortenMode.BEGIN:
        return '{replace}\n{}'.format('\n'.join(lines[-max_lines:]), replace=replace)
    elif mode == ShortenMode.END:
        return '{}\n{replace}'.format('\n'.join(lines[:max_lines]), replace=replace)
    elif mode == ShortenMode.MIDDLE:
        n = math.floor(max_lines / 2)
        return '{}\n{replace}\n{}'.format('\n'.join(lines[:n]),
                                          '\n'.join(lines[-n:]),
                                          replace=replace)


class BasicFormatter(Formatter):
    """
    The default `Formatter` for reporting progress and results of test cases.
    """
    @staticmethod
    def validParams():
        params = Formatter.validParams()
        params.add('width', vtype=int,
                   doc="The width of the state output (the results output is not altered), if not " \
                       "provided terminal width is inferred, if possible, otherwise a default width of 80 is utilized.")
        params.add('min_print_result',
                   vtype=TestCase.Result,
                   default=TestCase.Result.DIFF,
                   doc="The minimum TestCase.Result state necessary to show results.")
        params.add('min_print_progress',
                   vtype=TestCase.Result,
                   default=TestCase.Result.SKIP,
                   doc="The minimum TestCase.Result state necessary to show progress.")
        params.add('differ_indent',
                   default=' ' * 4,
                   vtype=str,
                   doc="The text to use for indenting the differ state/result output.")
        params.add('max_lines',
                   default=500,
                   vtype=int,
                   doc="Maximum number of lines to show in sys.stdout/sys.stderr in result output.")
        params.add('print_longest_running_tests',
                   default=5,
                   vtype=int,
                   doc="Print the given number of the longest running test cases.")
        return params

    @staticmethod
    def validCommandLineArguments(parser, params):
        parser.add_argument('--verbose',
                            action='store_true',
                            help=("Enable complete output, this will override the use of "
                                  "'--min_print_result' and '--min_print_progress'."))
        parser.add_argument('--min_print_result',
                            choices=[e.name for e in TestCase.Result],
                            default='DIFF',
                            help="The minimum status to show when reporting test results.")
        parser.add_argument('--min_print_progress',
                            choices=[e.name for e in TestCase.Result],
                            default='SKIP',
                            help="The minimum status to show when reporting test progress.")

    def __init__(self, *args, **kwargs):
        Formatter.__init__(self, *args, **kwargs)
        max_state = max([len(e.text) for e in list(TestCase.Progress)])
        max_result = max([len(e.text) for e in list(TestCase.Result)])
        self._max_state_width = max(max_state, max_result)
        self._extra_width = 16  # extract width for percent complete and duration

    def _setup(self, args):
        """
        Apply command line arguments.
        """
        Formatter._setup(self, args)
        if args.min_print_result:
            self.parameters().setValue('min_print_result', TestCase.Result[args.min_print_result])
        if args.min_print_progress:
            self.parameters().setValue('min_print_progress',
                                       TestCase.Result[args.min_print_progress])
        if args.verbose:
            self.parameters().setValue('min_print_progress', TestCase.Result.REMOVE)
            self.parameters().setValue('min_print_result', TestCase.Result.REMOVE)

    def width(self):
        """
        Return the character line width to use for reporting progress.
        """
        width = self.getParam('width')
        if width is None:
            width, _ = shutil.get_terminal_size()
        return width

    def fill(self, *args):
        """
        Return a string of dots ('.') with a length based on the width less any space to be occupied
        by items in *\*args* and any extra width.
        """
        width = self.width() - self._extra_width
        return '.' * (width - sum([len(a) for a in args]))

    def shortenLines(self, content):
        """
        Return the supplied *content* shortened to the number of lines as defined in 'max_lines'
        parameter.
        """
        n = self.getParam('max_lines')
        return shorten_text(content, n, replace=f'...OUTPUT REMOVED (MAX LINES: {n})...')

    def shortenLine(self, content, max_length, **kwargs):
        """
        Return the supplied *line* shortened to the number to *max_length*.

        The *\*\*kwargs* are keyword arguments passed the `shorten_line` function.
        """
        return shorten_line(content, max_length, **kwargs)

    def formatRunnerProgress(self, **kwargs):
        """
        Return the progress line from a `Runner` object. (override)
        """
        return self._formatProgress(**kwargs)

    def formatDifferProgress(self, **kwargs):
        """
        Return the progress line from a `Differ` object. (override)
        """
        kwargs.pop('percent')
        kwargs.pop('duration')
        kwargs['indent'] = self.getParam('differ_indent')
        return self._formatProgress(**kwargs)

    def formatRunnerResult(self, **kwargs):
        """
        Return the results text from a `Runner` object. (override)
        """
        return self._formatResult(**kwargs)

    def formatDifferResult(self, **kwargs):
        """
        Return the results text from a `Differ` object. (override)
        """
        kwargs['indent'] = self.getParam('differ_indent')
        kwargs['name']
        return self._formatResult(**kwargs)

    def formatComplete(self, complete, **kwargs):
        """
        Return the output after all `TestCase` objects in *complete* have finished. (override)
        """
        # Add visible break for summary
        out = list()
        out.append("-" * self.width())

        # Number of tests executed
        t = kwargs.get('duration', None)
        if t is not None:
            out.append(f"Executed {len(complete)} tests in {t:.1f} seconds.")
        else:
            out.append(f"Executed {len(complete)} tests.")

        # Display the TestCase result counts
        counts = collections.defaultdict(int)
        for tc in complete:
            counts[tc.state] += 1
        out.append(' '.join(f"{s.display}:{counts[s]}" for s in TestCase.Result))

        # Longest running tests
        longest = self.getParam('print_longest_running_tests')
        if (longest is not None) and (longest > 0):
            shown = 0
            out.append('\nLongest running test(s):')
            for tc in reversed(sorted(complete, key=lambda tc: tc.time)):
                out.append(f'  {tc.time:.2f}s {tc.name()}')
                shown += 1
                if shown > longest:
                    break

        return '\n'.join(out)

    def _formatProgress(self, **kwargs):
        """
        Helper method for printing the progress line.
        """
        state = kwargs.get('state')
        min_progress = self.getParam('min_print_progress')
        if state.level < min_progress.level:
            return None

        # Build suffix string that contains percent/duration information
        percent = kwargs.get('percent', None)
        percent = f"{percent:>3.0f}%" if (percent is not None) else ''

        duration = kwargs.get('duration', None)
        duration = f"[{duration:3.1f}s]" if (duration is not None) and (duration > 0) else ''

        suffix = " {:<{width}}".format(percent + ' ' + duration, width=self._extra_width - 1)

        # Build the main status line
        indent = kwargs.get('indent', '')
        status = f"{state.text:<{self._max_state_width}}"
        width_avail = self.width() - sum(len(x) for x in [indent, status]) - self._extra_width
        name = self.shortenLine(kwargs.get('name'), math.floor(0.66 * width_avail))

        # Create reasons and handle long reasons
        width_avail = self.width() - sum(len(x) for x in [indent, status, name]) - self._extra_width
        reasons = kwargs.get('reasons') or ''  # use or to account for `None` being passed in
        if reasons:
            reasons = '; '.join(reasons)
            if len(reasons) > width_avail - 8:
                reasons = self.shortenLine(reasons, width_avail - 8, mode=ShortenMode.BEGIN)
            reasons = f"[{reasons}] "

        fill = self.fill(indent, name, reasons, status)
        msg = f"{indent}{state.format(name)}{fill}{state.format(reasons)}{state.format(status)}{suffix}"
        return msg

    def _formatResult(self, **kwargs):
        """
        Helper method for printing the results.
        """
        state = kwargs.get('state')
        min_state = self.getParam('min_print_result')
        if state.level < min_state.level:
            return None

        indent = kwargs.get('indent', '')
        name = kwargs.get('name')
        stdout = kwargs.get('stdout')
        if stdout is not None:
            prefix = indent + state.format(name) + ' '
            stdout = textwrap.indent(self.shortenLines(kwargs.get('stdout')), prefix,
                                     lambda *args: True)
        else:
            stdout = ''

        stderr = kwargs.get('stderr')
        if stderr is not None:
            prefix = indent + state.format(name) + ' '
            stderr = textwrap.indent(self.shortenLines(kwargs.get('stderr')), prefix,
                                     lambda *args: True)
        else:
            stderr = ''

        return (stdout + stderr).strip('\n')
