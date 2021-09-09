#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moosetools/blob/main/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import sys
import io
import collections
import threading
import logging
import platform


class RedirectOutput(object):
    """
    A context for redirecting sys.stdout/sys.stderr and logs to thread specific streams.

    If *merge* is true both sys.stdout and sys.stderr will be redirected to the `stdout` property.

    The logging package stores sys.stdout/sys.stderr as a member variable within it's objects as
    such simply redirecting them does not influence logging. This class accounts for that by
    setting the stream of all logging.StreamHander objects within the context.
    """

    SYS_STDOUT = sys.stdout
    SYS_STDERR = sys.stderr

    class SysRedirect(object):
        """
        A replacement IO object for sys.stdout/err that stores content based on thread id.

        The supplied *io*, should be a `dict` of `io.TextIOWrapper` objects.
        """
        def __init__(self, io):
            self._io = io
            self._tid = threading.get_native_id(
            ) if platform.python_version() >= '3.8.0' else threading.get_ident()

        def write(self, message):
            self._io[self._tid].write(message)

        def flush(self):
            self._io[self._tid].flush()

    def __init__(self, *, merge=False):
        self._merge = merge
        self._tid = threading.get_native_id(
        ) if platform.python_version() >= '3.8.0' else threading.get_ident()
        self._stdout = collections.defaultdict(
            lambda: io.TextIOWrapper(io.BytesIO(), RedirectOutput.SYS_STDOUT.encoding))
        self._stderr = collections.defaultdict(
            lambda: io.TextIOWrapper(io.BytesIO(), RedirectOutput.SYS_STDERR.encoding))

        # logging Handler/Formatter/Stream pairs for redirecting logging output
        logger = logging.getLogger()
        self._handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]

    @property
    def stdout(self):
        """
        Return the redirect output to `sys.stdout` for the current process.
        """
        buf = self._stdout[self._tid]
        buf.seek(0)
        return buf.read()

    @property
    def stderr(self):
        """
        Return the redirect output to `sys.stderr` for the current process.
        """
        buf = self._stderr[self._tid]
        buf.seek(0)
        return buf.read()

    def __enter__(self):
        """
        Re-assign sys.stdout/sys.stderr upon entering context.
        """
        sys.stdout = RedirectOutput.SysRedirect(self._stdout)
        sys.stderr = sys.stdout if self._merge else RedirectOutput.SysRedirect(self._stderr)

        if platform.python_version() < '3.7.0':
            for h in self._handlers:
                h.stream = sys.stderr
        else:
            for h in self._handlers:
                h.setStream(sys.stderr)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Restore sys.stdout/sys.stderr upon exiting the context.
        """

        sys.stdout = RedirectOutput.SYS_STDOUT
        sys.stderr = RedirectOutput.SYS_STDERR

        if platform.python_version() < '3.7.0':
            for h in self._handlers:
                h.stream = RedirectOutput.SYS_STDERR
        else:
            for h in self._handlers:
                h.setStream(RedirectOutput.SYS_STDERR)
