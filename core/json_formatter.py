"""Formatter JSON para análisis en herramientas externas; sin datos sensibles."""
from pythonjsonlogger import jsonlogger


class AppJsonFormatter(jsonlogger.JsonFormatter):
    """Incluye timestamp, level, request_id, user_id y contexto operativo opcional."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record.pop("asctime", None)
        log_record.pop("levelname", None)
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record.setdefault("request_id", getattr(record, "request_id", "n/a"))
        log_record.setdefault("user_id", getattr(record, "user_id", "anonymous"))
        ef = getattr(record, "extra_fields", None)
        if ef is not None:
            log_record["context"] = ef
