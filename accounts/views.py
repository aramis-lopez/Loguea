"""Vistas de autenticación JWT con observabilidad sin fugas de secretos."""
import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers import LoginTokenSerializer
from core.security_audit import emit_security_event
from core.security_bruteforce import is_login_blocked

log = logging.getLogger("accounts.auth")


class LoginView(TokenObtainPairView):
    """POST credenciales → access + refresh (cuerpo de respuesta no se loguea)."""

    permission_classes = [AllowAny]
    serializer_class = LoginTokenSerializer

    def post(self, request, *args, **kwargs):
        if is_login_blocked(request):
            emit_security_event(
                request,
                "Login rechazado: IP en periodo de bloqueo por fuerza bruta",
                429,
            )
            return Response(
                {
                    "detail": "Demasiados intentos fallidos. "
                    "Espere antes de volver a intentar o contacte al administrador."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        log.info(
            "Inicio operación login",
            extra={"extra_fields": {"operation": "auth.login_start"}},
        )
        try:
            return super().post(request, *args, **kwargs)
        except Exception:
            log.error(
                "Error no controlado en login",
                exc_info=True,
                extra={"extra_fields": {"operation": "auth.login_error"}},
            )
            raise


class RefreshTokenView(TokenRefreshView):
    """Renovación de access; el refresh token nunca aparece en logs."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        log.info(
            "Solicitud de renovación de token (payload no registrado)",
            extra={"extra_fields": {"operation": "auth.refresh_start"}},
        )
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                log.info(
                    "Token renovado correctamente (valor no registrado)",
                    extra={"extra_fields": {"operation": "auth.refresh_ok"}},
                )
            else:
                log.warning(
                    "Renovación de token rechazada",
                    extra={
                        "extra_fields": {
                            "operation": "auth.refresh_failed",
                            "status_code": response.status_code,
                        }
                    },
                )
            return response
        except Exception:
            log.error(
                "Error en renovación de token",
                exc_info=True,
                extra={"extra_fields": {"operation": "auth.refresh_error"}},
            )
            raise


class HealthView(APIView):
    """Endpoint sin autenticación para comprobar que el servicio responde."""

    permission_classes = [AllowAny]

    def get(self, request):
        log.info(
            "Health check",
            extra={"extra_fields": {"operation": "health"}},
        )
        return Response({"status": "ok"})
