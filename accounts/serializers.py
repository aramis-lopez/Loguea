"""
Serializers de login JWT.
Bitácora forense: inyección en usuario (SECURITY), fuerza bruta por IP.
"""
import logging

from rest_framework import serializers
from rest_framework.exceptions import Throttled
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.security_audit import emit_security_event
from core.security_bruteforce import clear_login_attempts, record_failed_login
from core.security_patterns import is_severe_injection

log = logging.getLogger("accounts.auth")


class LoginTokenSerializer(TokenObtainPairSerializer):
    """Emite pares access/refresh; registra intentos fallidos y bloqueos por fuerza bruta."""

    def validate(self, attrs):
        request = self.context.get("request")
        username = (attrs.get("username") or "").strip()

        if request and is_severe_injection(username):
            emit_security_event(
                request,
                "Intento de inyección SQL/XSS detectado en campo usuario (login)",
                400,
            )
            raise serializers.ValidationError(
                {"username": "Entrada no permitida por política de seguridad."}
            )

        log.info(
            "Inicio validación de credenciales",
            extra={"extra_fields": {"operation": "auth.validate_start"}},
        )
        try:
            data = super().validate(attrs)
        except Exception as exc:
            if request:
                bf = record_failed_login(request)
                if bf == "just_blocked":
                    from django.conf import settings

                    wait = int(getattr(settings, "SECURITY_BF_BLOCK_SEC", 1800))
                    raise Throttled(wait=wait) from exc
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

        if request:
            clear_login_attempts(request)

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
