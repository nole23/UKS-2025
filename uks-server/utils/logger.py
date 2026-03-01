import os

import logging
import inspect


_app_logger = logging.getLogger("uks")
_audit_logger = logging.getLogger("audit")


class _BaseLogger:
    STACK_LEVEL = 3  # koliko stack frame-ova gore tražimo caller

    @classmethod
    def _context(cls):
        try:
            frame = inspect.stack()[cls.STACK_LEVEL]
            module = inspect.getmodule(frame[0])
            instance = frame.frame.f_locals.get("self")

            class_name = (
                instance.__class__.__name__
                if instance
                else (module.__name__ if module else "unknown")
            )

            pid = os.getpid()
            return f"[{pid}] [{class_name}] - [{frame.function}] :"

        except Exception:
            return "[unknown]"

    @classmethod
    def _log(cls, logger, level, message: str):
        logger.log(level, f"{cls._context()} {message}")


class UKSLogger(_BaseLogger):

    @classmethod
    def debug(cls, message: str):
        cls._log(_app_logger, logging.DEBUG, message)

    @classmethod
    def info(cls, message: str):
        cls._log(_app_logger, logging.INFO, message)

    @classmethod
    def warning(cls, message: str):
        cls._log(_app_logger, logging.WARNING, message)

    @classmethod
    def error(cls, message: str):
        cls._log(_app_logger, logging.ERROR, message)

    @classmethod
    def critical(cls, message: str):
        cls._log(_app_logger, logging.CRITICAL, message)


class UKSAuditLogger(_BaseLogger):

    @classmethod
    def info(cls, message: str):
        cls._log(_audit_logger, logging.INFO, message)