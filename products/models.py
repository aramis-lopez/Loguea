from django.db import models


class Product(models.Model):
    nombre = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self) -> str:
        return f"{self.nombre} ({self.pk})"
