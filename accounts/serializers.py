"""
Serializers de login JWT.
Nunca se registra contraseña, hash ni tokens emitidos.
"""
import logging

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

log = logging.getLogger("accounts.auth")


class LoginTokenSerializer(TokenObtainPairSerializer):
    """Emite pares access/refresh; el logging solo usa user_id tras éxito."""

    def validate(self, attrs):
        log.info(
            "Inicio validación de credenciales",
            extra={"extra_fields": {"operation": "auth.validate_start"}},
        )
        try:
            data = super().validate(attrs)
        except Exception as exc:
            log.warning(
                "Validación de credenciales fallida",
                extra={
                    "extra_fields": {
                        "operation": "auth.validate_failed",
                        "error_type": type(exc).__name__,
                    }
                },
            )
            raise
        log.info(
            "Validación de credenciales correcta; tokens emitidos (no registrados)",
            extra={
                "extra_fields": {
                    "operation": "auth.validate_ok",
                    "user_id": self.user.pk,
                }
            },
        )
        return data
