#!/usr/bin/env python
"""Punto de entrada de Django; la configuración de logging se carga en settings."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "loguea_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y activo el entorno virtual?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
