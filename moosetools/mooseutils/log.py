import logging
import multiprocessing
from .color_text import color_text

__LOG_COLOR__ = {
    logging.DEBUG: 'cyan_1',
    logging.INFO: None,
    logging.WARNING: 'orange_1',
    logging.ERROR: 'red_1',
    logging.CRITICAL: 'magenta_1'
}


def color_log(msg, level):
    return color_text(msg, __LOG_COLOR__[level])


class MooseDocsFormatter(logging.Formatter):
    def format(self, record):
        tid = multiprocessing.current_process().name
        msg = '{} ({}): {}'.format(record.name, tid, logging.Formatter.format(self, record))
        return mooseutils.colorText(msg, self.COLOR[record.levelname])


class MultiprocessingHandler(logging.StreamHandler):

    COUNTS = {
        logging.CRITICAL: multiprocessing.Value('I', 0, lock=True),
        logging.ERROR: multiprocessing.Value('I', 0, lock=True),
        logging.WARNING: multiprocessing.Value('I', 0, lock=True),
        logging.INFO: multiprocessing.Value('I', 0, lock=True),
        logging.DEBUG: multiprocessing.Value('I', 0, lock=True)
    }

    def getCount(self, level):
        return MultiprocessingHandler.COUNTS[level].value

    def handle(self, record):
        super().handle(record)
        with MultiprocessingHandler.COUNTS[record.levelno].get_lock():
            MultiprocessingHandler.COUNTS[record.levelno].value += 1

    def flush(self):
        """Lock when flushing logging messages."""
        if self._lock:
            with self._lock:
                super(MultiprocessingHandler, self).flush()
        else:
            super(MultiprocessingHandler, self).flush()

    def createLock(self):
        """logging by default uses threading, use a multiprocessing lock instead."""
        self.lock = None
        self._lock = multiprocessing.Lock()

    def aquire(self):
        """Disable."""
        pass

    def release(self):
        """Disable."""
        pass


def init(level=logging.INFO, silent=False):

    # Custom format that colors and counts errors/warnings
    #if silent:
    #    handler = moosesqa.SilentRecordHandler()
    #else:
    handler = MultiprocessingHandler()
    #formatter = MooseToolsFormatter()
    #handler.setFormatter(formatter)

    # Setup the custom formatter
    log = logging.getLogger('moosetools')
    log.addHandler(handler)
    log.setLevel(level)

    MooseDocs.LOG_LEVEL = level
