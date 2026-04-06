"""Registra el nivel de log SECURITY (25) para la bitácora forense."""
import logging

SECURITY = 25
logging.addLevelName(SECURITY, "SECURITY")


def _security(self, message, *args, **kwargs):
    if self.isEnabledFor(SECURITY):
        self._log(SECURITY, message, args, **kwargs)


logging.Logger.security = _security  # type: ignore[attr-defined]
