"""
JWT con actualización del contexto de logging (solo user_id numérico, nunca el token).
"""
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.context import user_id_var


class JWTAuthenticationWithContext(JWTAuthentication):
    """Tras validar el JWT, expone user_id para los logs de la petición actual."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            user_id_var.set(None)
            return None
        user, _validated_token = result
        user_id_var.set(user.pk)
        return user, _validated_token
