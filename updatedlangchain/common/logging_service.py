"""Shared app logger: write ALL run logs (info, warnings, errors + tracebacks)
to ONE rotating file, plus the console.

Cron-safe: file opened in append mode; rotates at 5 MB x5 backups so it never
grows unbounded across repeated runs. Path is ABSOLUTE
(`<repo-root>/logs/contract_mailer.log`) so it's the same file no matter the
working directory cron uses. Override with `APP_LOG_PATH`.

Usage:

    from common.logging_service import get_logger
    log = get_logger()
    log.info('started')
    try:
        ...
    except Exception:
        log.exception('it broke')   # logs message + full traceback
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# this file lives at <repo-root>/updatedlangchain/common/
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_LOG = _REPO_ROOT / 'logs' / 'contract_mailer.log'


def get_logger(name: str = 'contract_mailer') -> logging.Logger:
    """Return a configured logger; safe to call repeatedly (no duplicate handlers)."""
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured (notebook re-run / repeated import)
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    path = Path(os.getenv('APP_LOG_PATH', _DEFAULT_LOG))
    path.parent.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        '%(asctime)s %(levelname)-7s %(name)s: %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S%z',
    )

    file_handler = RotatingFileHandler(
        path, mode='a', maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(fmt)

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console)
    return logger
