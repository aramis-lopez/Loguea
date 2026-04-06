"""
Middleware forense: escaneo temprano de inyección (query/form),
registro automático de respuestas 4xx/5xx en bitácora.
"""
import logging

from django.http import HttpRequest, HttpResponse, JsonResponse

from core.security_audit import emit_bitacora, emit_security_event
from core.security_patterns import is_severe_injection

log = logging.getLogger("core.security_middleware")

# Rutas donde no escaneamos cuerpo form (login JSON no pasa por POST form)
SKIP_INJECTION_SCAN_PREFIXES = (
    "/static/",
    "/media/",
)


def _should_scan_path(path: str) -> bool:
    return not any(path.startswith(p) for p in SKIP_INJECTION_SCAN_PREFIXES)


def _iter_query_values(request: HttpRequest):
    for _key, values in request.GET.lists():
        for v in values:
            yield str(v)
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            for _key, values in request.POST.lists():
                for v in values:
                    yield str(v)
        except Exception:
            pass


class SecurityForensicsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if _should_scan_path(request.path):
            try:
                for chunk in _iter_query_values(request):
                    if len(chunk) > 12000:
                        chunk = chunk[:12000]
                    if is_severe_injection(chunk):
                        emit_security_event(
                            request,
                            "Patrón de inyección (SQLi/XSS) detectado en parámetros de petición",
                            400,
                        )
                        return JsonResponse(
                            {"detail": "Solicitud rechazada por política de seguridad."},
                            status=400,
                        )
            except Exception:
                log.error(
                    "Error en escaneo de seguridad de entrada",
                    exc_info=True,
                    extra={"extra_fields": {"operation": "security.scan_error"}},
                )

        response = self.get_response(request)
        self._audit_http_response(request, response)
        return response

    def _audit_http_response(self, request: HttpRequest, response: HttpResponse) -> None:
        if not _should_scan_path(request.path):
            return
        try:
            status = getattr(response, "status_code", 200)
        except Exception:
            return

        if status < 400:
            return

        if status == 401:
            emit_bitacora(
                request,
                logging.WARNING,
                "Acceso no autenticado (falta o token JWT inválido)",
                status,
            )
        elif status == 403:
            emit_bitacora(
                request,
                logging.WARNING,
                "Acceso prohibido (permisos insuficientes)",
                status,
            )
        elif status == 404:
            emit_bitacora(
                request,
                logging.INFO,
                "Recurso no encontrado",
                status,
            )
        elif 400 <= status < 500:
            emit_bitacora(
                request,
                logging.WARNING,
                f"Respuesta HTTP cliente {status}",
                status,
            )
        else:
            emit_bitacora(
                request,
                logging.ERROR,
                "Error interno del servidor (posible fuga de información si DEBUG expone trazas)",
                status,
            )
