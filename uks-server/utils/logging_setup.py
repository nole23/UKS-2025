import logging
import logging.handlers
from pathlib import Path
from django.conf import settings

from .filters import AuditFilter, NonAuditFilter, ErrorFilter
from .formatters import JsonFormatter


class LoggingBootstrapper:
    _started = False

    @classmethod
    def start(cls):
        if cls._started:
            return

        cls._started = True

        base_dir = Path(settings.BASE_DIR)
        log_dir = base_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        formatter = JsonFormatter()

        system_handler = logging.handlers.RotatingFileHandler(
            log_dir / "system.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        system_handler.setFormatter(formatter)
        system_handler.addFilter(NonAuditFilter())

        audit_handler = logging.handlers.RotatingFileHandler(
            log_dir / "audit.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        audit_handler.setFormatter(formatter)
        audit_handler.addFilter(AuditFilter())

        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        error_handler.setFormatter(formatter)
        error_handler.addFilter(ErrorFilter())

        cls.listener = logging.handlers.QueueListener(
            settings.LOG_QUEUE,
            system_handler,
            audit_handler,
            error_handler,
            respect_handler_level=True
        )

        cls.listener.start()

        print(f"Logovi će biti u: {log_dir.resolve()}")