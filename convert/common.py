import logging

from psutil import process_iter, TimeoutExpired, NoSuchProcess

from convert.util import FileLock, LOCK_FILE

log = logging.getLogger(__name__)


class Converter(object):
    """Generic libreoffice converter class."""

    def __init__(self, lock_file=LOCK_FILE):
        self.lock = FileLock(lock_file)

    def convert_file(self, infile, outfile, timeout):
        raise NotImplementedError()

    def kill(self):
        # The Alfred Hitchcock approach to task management:
        # https://www.youtube.com/watch?v=0WtDmbr9xyY
        for i in range(10):
            proc = self.get_proc()
            if proc is None:
                break
            log.info("Disposing converter process.")
            try:
                proc.kill()
                proc.wait(timeout=3)
            except NoSuchProcess:
                log.info("Process has disappeared")
            except (TimeoutExpired, Exception) as exc:
                log.error("Failed to kill: %r (%s)", proc, exc)
                # os._exit(23)

    def get_proc(self):
        for proc in process_iter(["cmdline"]):
            name = " ".join(proc.cmdline())
            if "soffice.bin" in name:
                return proc
