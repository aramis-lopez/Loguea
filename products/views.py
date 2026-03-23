"""
API REST de productos con logging por operación.
No se registran cuerpos completos de petición; solo campos necesarios para trazabilidad.
"""
import logging

from django.db import DatabaseError
from rest_framework import status, viewsets
from rest_framework.response import Response

from products.models import Product
from products.serializers import ProductSerializer

log = logging.getLogger("products.api")


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def list(self, request, *args, **kwargs):
        log.info(
            "Inicio listado de productos",
            extra={"extra_fields": {"operation": "products.list_start"}},
        )
        try:
            response = super().list(request, *args, **kwargs)
            data = response.data
            if isinstance(data, list):
                count = len(data)
            elif isinstance(data, dict) and "results" in data:
                count = len(data["results"])
            else:
                count = None
            log.info(
                "Listado de productos completado",
                extra={
                    "extra_fields": {
                        "operation": "products.list_ok",
                        "result_count": count,
                    }
                },
            )
            return response
        except DatabaseError:
            log.critical(
                "Fallo de base de datos al listar productos",
                exc_info=True,
                extra={"extra_fields": {"operation": "products.list_db_critical"}},
            )
            raise
        except Exception:
            log.error(
                "Error al listar productos",
                exc_info=True,
                extra={"extra_fields": {"operation": "products.list_error"}},
            )
            raise

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        log.info(
            "Inicio obtención de producto",
            extra={"extra_fields": {"operation": "products.retrieve_start", "product_id": pk}},
        )
        try:
            response = super().retrieve(request, *args, **kwargs)
            log.info(
                "Producto obtenido",
                extra={"extra_fields": {"operation": "products.retrieve_ok", "product_id": pk}},
            )
            return response
        except DatabaseError:
            log.critical(
                "Fallo de base de datos al obtener producto",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "operation": "products.retrieve_db_critical",
                        "product_id": pk,
                    }
                },
            )
            raise
        except Exception:
            log.error(
                "Error al obtener producto",
                exc_info=True,
                extra={"extra_fields": {"operation": "products.retrieve_error", "product_id": pk}},
            )
            raise

    def create(self, request, *args, **kwargs):
        log.info(
            "Inicio creación de producto",
            extra={"extra_fields": {"operation": "products.create_start"}},
        )
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            log.warning(
                "Validación de datos fallida al crear producto",
                extra={
                    "extra_fields": {
                        "operation": "products.create_validation_failed",
                        "field_errors": list(serializer.errors.keys()),
                    }
                },
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_create(serializer)
            pid = serializer.instance.pk if serializer.instance else None
            log.info(
                "Producto creado",
                extra={"extra_fields": {"operation": "products.create_ok", "product_id": pid}},
            )
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except DatabaseError:
            log.critical(
                "Fallo de base de datos al crear producto",
                exc_info=True,
                extra={"extra_fields": {"operation": "products.create_db_critical"}},
            )
            raise
        except Exception:
            log.error(
                "Error al crear producto",
                exc_info=True,
                extra={"extra_fields": {"operation": "products.create_error"}},
            )
            raise

    def update(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        log.info(
            "Inicio actualización de producto",
            extra={"extra_fields": {"operation": "products.update_start", "product_id": pk}},
        )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            log.warning(
                "Validación de datos fallida al actualizar producto",
                extra={
                    "extra_fields": {
                        "operation": "products.update_validation_failed",
                        "product_id": pk,
                        "field_errors": list(serializer.errors.keys()),
                    }
                },
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_update(serializer)
            log.info(
                "Producto actualizado",
                extra={"extra_fields": {"operation": "products.update_ok", "product_id": pk}},
            )
            return Response(serializer.data)
        except DatabaseError:
            log.critical(
                "Fallo de base de datos al actualizar producto",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "operation": "products.update_db_critical",
                        "product_id": pk,
                    }
                },
            )
            raise
        except Exception:
            log.error(
                "Error al actualizar producto",
                exc_info=True,
                extra={"extra_fields": {"operation": "products.update_error", "product_id": pk}},
            )
            raise

    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        log.info(
            "Inicio eliminación de producto",
            extra={"extra_fields": {"operation": "products.delete_start", "product_id": pk}},
        )
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            log.info(
                "Producto eliminado",
                extra={"extra_fields": {"operation": "products.delete_ok", "product_id": pk}},
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DatabaseError:
            log.critical(
                "Fallo de base de datos al eliminar producto",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "operation": "products.delete_db_critical",
                        "product_id": pk,
                    }
                },
            )
            raise
        except Exception:
            log.error(
                "Error al eliminar producto",
                exc_info=True,
                extra={"extra_fields": {"operation": "products.delete_error", "product_id": pk}},
            )
            raise
