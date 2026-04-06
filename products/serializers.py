import logging

from rest_framework import serializers

from core.security_audit import emit_bitacora, emit_security_event
from core.security_patterns import is_severe_injection, is_suspicious_only

from products.models import Product

log = logging.getLogger("products.api")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "nombre", "precio", "stock")
        read_only_fields = ("id",)

    def validate_nombre(self, value):
        request = self.context.get("request")
        if request and value:
            if is_severe_injection(value):
                emit_security_event(
                    request,
                    "Inyección SQL/XSS bloqueada en campo nombre (producto)",
                    400,
                )
                raise serializers.ValidationError(
                    "El nombre contiene caracteres o patrones no permitidos."
                )
            if is_suspicious_only(value):
                emit_bitacora(
                    request,
                    logging.WARNING,
                    "Patrón sospechoso en nombre de producto (revisión recomendada)",
                    "---",
                )
                log.warning(
                    "Validación heurística: nombre de producto marcado como sospechoso",
                    extra={
                        "extra_fields": {
                            "operation": "products.suspicious_nombre",
                        }
                    },
                )
        return value
