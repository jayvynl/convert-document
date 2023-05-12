import logging
import os
import time
from tempfile import gettempdir

from psutil import pid_exists

LOCK_FILE = os.path.join(gettempdir(), "convert.lock")
INSTANCE_DIR = os.path.join(gettempdir(), "soffice")
logger = logging.getLogger(__name__)


class ConversionFailure(Exception):
    # A failure related to the content or structure of the document
    # given, which is expected to re-occur with consecutive attempts
    # to process the document.
    pass


class SystemFailure(Exception):
    # A failure of the service that lead to a failed conversion of
    # the document which may or may not re-occur when the document
    # is processed again.
    pass


class FileLock:
    def __init__(self, file=LOCK_FILE):
        self.file = file

    def lock(self):
        # Race conditions galore, but how likely
        # are requests at that rate?
        try:
            with open(self.file) as fh:
                pid = int(fh.read())
        except (ValueError, FileNotFoundError):
            pass
        else:
            # Already acquired.
            if pid == os.getpid():
                return True
        if self.is_locked():
            return False
        with open(self.file, "w") as fh:
            fh.write(str(os.getpid()))
        return True

    def unlock(self):
        if os.path.exists(self.file):
            os.unlink(self.file)

    def is_locked(self):
        try:
            with open(self.file) as fh:
                pid = int(fh.read())
        except (ValueError, FileNotFoundError):
            return False
        if not pid_exists(pid):
            return False
        return True

    def __enter__(self):
        while not self.lock():
            logger.info("waiting lock")
            time.sleep(1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unlock()
