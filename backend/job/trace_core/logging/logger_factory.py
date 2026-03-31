"""Logger factory – creates named loggers with rotating file + console handlers."""
import logging
import logging.handlers
import os
from .formatters import StructuredFormatter

_LOGS_DIR = "logs"
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5

_LOG_FILES = {
    "scanner": "scanner.log",
    "parser": "parser.log",
    "trace": "trace.log",
    "audit": "audit.log",
    "api": "application.log",
}
_DEFAULT_FILE = "application.log"

_initialised: set = set()


class LoggerFactory:
    """Creates and caches structured loggers."""

    @staticmethod
    def get(name: str, level: int = logging.DEBUG) -> logging.Logger:
        logger = logging.getLogger(name)
        if name in _initialised:
            return logger
        _initialised.add(name)
        logger.setLevel(level)
        logger.propagate = False

        fmt = StructuredFormatter()

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        # File handler
        os.makedirs(_LOGS_DIR, exist_ok=True)
        log_file = os.path.join(_LOGS_DIR, _LOG_FILES.get(name.split(".")[0], _DEFAULT_FILE))
        fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        # Error file handler for WARN+
        err_fh = logging.handlers.RotatingFileHandler(
            os.path.join(_LOGS_DIR, "error.log"), maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT
        )
        err_fh.setLevel(logging.WARNING)
        err_fh.setFormatter(fmt)
        logger.addHandler(err_fh)

        return logger
