"""Utility functions."""
from types import FrameType
from typing import Callable
import logging
import subprocess as sp
import sys

from loguru import logger

__all__ = ('setup_logging',)


class InterceptHandler(logging.Handler):  # pragma: no cover
    """Intercept handler taken from Loguru's documentation."""
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # Find caller from where originated the logged message
        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_log_intercept_handler() -> None:  # pragma: no cover
    """Sets up Loguru to intercept records from the logging module."""
    logging.basicConfig(handlers=(InterceptHandler(),), level=0)


def setup_logging(debug: bool | None = False) -> None:
    """Shared function to enable logging."""
    if debug:  # pragma: no cover
        setup_log_intercept_handler()
        logger.enable('')
    else:
        logger.configure(handlers=(dict(
            format='<level>{message}</level>',
            level='INFO',
            sink=sys.stderr,
        ),))


def runner(name: str,
           *,
           stderr: int | None = None,
           stdout: int | None = sp.PIPE,
           check: bool = True) -> Callable[[list[str] | tuple[str, ...]], sp.CompletedProcess[str]]:
    def cb(args: list[str] | tuple[str, ...]) -> sp.CompletedProcess[str]:
        return sp.run((name,) + tuple(args), text=True, check=check, stdout=stdout, stderr=stderr)

    return cb
