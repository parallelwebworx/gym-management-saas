"""
Base Django settings for the Gym Management SaaS backend.

Environment-driven (django-environ). Secrets are read from the environment
only — never hard-coded. `dev.py` / `prod.py` layer on top of this.
"""
from datetime import timedelta
from pathlib import Path

import environ

# backend/ (contains manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
# Load a .env file if present (dev convenience; prod uses real env vars).
environ.Env.read_env(BASE_DIR.parent / ".env")

# --- Core -----------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # third-party
    "rest_framework",
    "corsheaders",
    # local
    "common",
    "tenants",
    "catalogue",
    "members",
    "memberships",
    "payments",
    "audit",
    "engagement",
    "reports",
    "notifications",
    "invoices",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # resolves request.gym / request.branch / request.role from the JWT user
    "common.middleware.TenantMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database -------------------------------------------------------------
# DATABASE_URL, e.g. postgres://user:pass@host:5432/dbname
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/gym_saas",
    ),
}

# --- Auth -----------------------------------------------------------------
AUTH_USER_MODEL = "tenants.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N / TZ ------------------------------------------------------------
# Store UTC; the frontend renders IST. (Domain convention from source app.)
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static ---------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 25,
    "EXCEPTION_HANDLER": "common.exceptions.envelope_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "20/min",
        "user": "1000/min",
        "anon": "60/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- CORS -----------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://localhost:3000"],
)

# --- Domain constants -----------------------------------------------------
# Money is stored as integer paise everywhere. GST @ 18%, HSN 999723.
GST_RATE_BPS = 1800  # 18.00%
GST_HSN_CODE = "999723"

# --- Celery ---------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="")
# When true, tasks run inline (no broker needed) — handy for dev/tests.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True

# --- Notifications --------------------------------------------------------
# Provider: "stub" (logs, always succeeds) or "msg91". Secrets come from env only.
NOTIFICATION_PROVIDER = env("NOTIFICATION_PROVIDER", default="stub")
MSG91_API_KEY = env("MSG91_API_KEY", default="")
MSG91_SENDER_ID = env("MSG91_SENDER_ID", default="GYMAPP")
NOTIFICATION_MAX_ATTEMPTS = 3
