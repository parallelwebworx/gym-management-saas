"""Development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Run Celery tasks inline in dev/tests so no broker is required.
CELERY_TASK_ALWAYS_EAGER = True
