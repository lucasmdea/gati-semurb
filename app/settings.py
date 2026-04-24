"""app/settings.py

Configuração do Django para o projeto atendimentos-ti.

Meta:
- Rodar bem em container (Docker) e também local.
- Static confiável com WhiteNoise/collectstatic.
- Variáveis sensíveis/configuráveis via env.
"""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _env_csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts


# Segurança / ambiente
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = _env_bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = _env_csv("ALLOWED_HOSTS", "*") or ["*"]
CSRF_TRUSTED_ORIGINS = _env_csv("CSRF_TRUSTED_ORIGINS", "")


INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "app.urls"


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
                "core.context_processors.ui",
            ],
        },
    }
]


WSGI_APPLICATION = "app.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "atendimentos"),
        "USER": os.getenv("DB_USER", "SI"),
        "PASSWORD": os.getenv("DB_PASSWORD", "SI@s3mur8"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internacionalização
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True


# Static (WhiteNoise)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Auth
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "ticket_list"
LOGOUT_REDIRECT_URL = "login"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Convenção interna
TECHNICIANS_GROUP_NAME = os.getenv("TECHNICIANS_GROUP_NAME", "Tecnicos")
REQUESTERS_GROUP_NAME = os.getenv("REQUESTERS_GROUP_NAME", "Usuarios")


JAZZMIN_SETTINGS = {
    "site_title": "Atendimentos TI",
    "site_header": "SEMURB Natal — Atendimentos TI",
    "site_brand": "SEMURB Natal",
    "welcome_sign": "Painel Administrativo",
    "site_logo": "img/logo_semurb.png",
    "login_logo": "img/logo_semurb.png",
    "show_sidebar": True,
    "navigation_expanded": True,
    "custom_css": "admin/css/semurb_admin.css",
    "icons": {
        "core.Sector": "fas fa-building",
        "core.ServiceType": "fas fa-screwdriver-wrench",
        "core.Supply": "fas fa-box-open",
        "core.Ticket": "fas fa-ticket",
        "core.AssetItem": "fas fa-barcode",
        "core.StockItem": "fas fa-warehouse",
        "auth.User": "fas fa-users",
        "auth.Group": "fas fa-user-shield",
    },
    # Admin mais limpo (técnico não precisa ver o resto)
    "hide_apps": ["auth"],
    "hide_models": [
        "core.AssetMovement",
        "core.StockMovement",
        "core.TicketAsset",
        "core.TicketStockUsage",
        "core.TicketSupply",
    ],
}


JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "navbar": "navbar-white navbar-light",
    "sidebar": "sidebar-dark-primary",
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
}
