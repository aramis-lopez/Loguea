"""
Middleware de trazabilidad: asigna request_id por petición.
No registra cabeceras Authorization ni cuerpos de petición (evita fugas de JWT/contraseñas).
"""
import logging
import uuid

from django.http import HttpRequest, HttpResponse

from core.context import request_id_var, user_id_var

log = logging.getLogger("core.middleware")


class RequestContextMiddleware:
    """Genera un request_id único y lo expone al logger vía context vars."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        rid = str(uuid.uuid4())
        token_rid = request_id_var.set(rid)
        token_uid = user_id_var.set(None)
        request.request_id = rid  # type: ignore[attr-defined]
        log.info(
            "Inicio de petición",
            extra={
                "extra_fields": {
                    "path": request.path,
                    "method": request.method,
                }
            },
        )
        try:
            response = self.get_response(request)
            log.info(
                "Fin de petición",
                extra={
                    "extra_fields": {
                        "status_code": getattr(response, "status_code", None),
                        "path": request.path,
                    }
                },
            )
            return response
        finally:
            user_id_var.reset(token_uid)
            request_id_var.reset(token_rid)


class AuthenticatedUserContextMiddleware:
    """
    Debe ir después de AuthenticationMiddleware.
    Expone solo el ID numérico de usuario para correlación (nunca email ni token).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        uid = None
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            uid = user.pk
        token = user_id_var.set(uid)
        try:
            return self.get_response(request)
        finally:
            user_id_var.reset(token)
