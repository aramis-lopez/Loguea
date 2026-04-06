"""
Configuración Django con logging estructurado JSON y JWT.
No se registran contraseñas, tokens ni payloads completos en logs.
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Registra nivel SECURITY para logging (debe ejecutarse antes de configurar handlers).
import core.security_levels  # noqa: E402, F401

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-change-in-production-use-env",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "core",
    "accounts",
    "products",
    "web",
]

MIDDLEWARE = [
    "core.middleware.RequestContextMiddleware",
    "core.security_middleware.SecurityForensicsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.AuthenticatedUserContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "loguea_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "loguea_project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.authentication.JWTAuthenticationWithContext",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "UNAUTHENTICATED_USER": None,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Fuerza bruta (login): intentos en ventana y bloqueo en segundos
SECURITY_BF_THRESHOLD = int(os.environ.get("SECURITY_BF_THRESHOLD", "5"))
SECURITY_BF_WINDOW_SEC = int(os.environ.get("SECURITY_BF_WINDOW_SEC", "900"))
SECURITY_BF_BLOCK_SEC = int(os.environ.get("SECURITY_BF_BLOCK_SEC", "1800"))

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "loguea-forensics",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "core.logging_filters.RequestContextFilter",
        },
    },
    "formatters": {
        "json": {
            "()": "core.json_formatter.AppJsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            "json_ensure_ascii": False,
        },
        "bitacora": {
            "()": "core.bitacora_formatter.BitacoraFormatter",
        },
    },
    "handlers": {
        "console_json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["request_context"],
        },
        "security_bitacora_file": {
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "security_bitacora.log"),
            "formatter": "bitacora",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console_json"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console_json"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console_json"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console_json"],
            "level": "WARNING",
            "propagate": False,
        },
        "core": {"handlers": ["console_json"], "level": "INFO", "propagate": False},
        "accounts": {"handlers": ["console_json"], "level": "INFO", "propagate": False},
        "products": {"handlers": ["console_json"], "level": "INFO", "propagate": False},
        "security.audit": {
            "handlers": ["security_bitacora_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
