import logging


class AuditFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == "audit"


class NonAuditFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name != "audit"


class ErrorFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR