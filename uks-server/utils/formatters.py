import logging
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }

        if hasattr(record, "request_id"):
            log_object["request_id"] = record.request_id

        return json.dumps(log_object)