"""Formato estándar de bitácora: Timestamp | Nivel | Evento | Usuario | IP | Endpoint | Status | User-Agent"""
import logging


class BitacoraFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(datefmt="%Y-%m-%dT%H:%M:%SZ")

    def format(self, record: logging.LogRecord) -> str:
        ts = self.formatTime(record, self.datefmt)
        level = record.levelname
        if level.startswith("Level "):
            level = "SECURITY"
        event = getattr(record, "bitacora_event", record.getMessage())
        user = getattr(record, "bitacora_user", "Anónimo")
        ip = getattr(record, "bitacora_ip", "-")
        endpoint = getattr(record, "bitacora_endpoint", "-")
        status = getattr(record, "bitacora_status", "-")
        ua = getattr(record, "bitacora_ua", "-")
        return (
            f"[{ts}] | [{level}] | [{event}] | [Usuario: {user}] | [{ip}] | "
            f"[{endpoint}] | [{status}] | [{ua}]"
        )
