import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")

DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or ("dev-only-insecure-key" if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError("Set DJANGO_SECRET_KEY (or DJANGO_DEBUG=true for local development).")
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

DB_ENGINE = os.environ.get("DB_ENGINE", "postgres")
INSTALLED_APPS = [
    "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.staticfiles",
    "corsheaders", "rest_framework",
    "apps.common", "apps.videos", "apps.processing", "apps.ai_engine", "apps.search", "apps.dashboard",
]
if DB_ENGINE == "postgres":
    INSTALLED_APPS.append("django.contrib.postgres")
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = []

if DB_ENGINE == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "rewind"), "USER": os.environ.get("DB_USER", "rewind"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""), "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
STATIC_URL = "static/"

MEDIA_URL = "media/"          # media is NOT served publicly; videos stream via /api/videos/<id>/stream/
MEDIA_ROOT = BASE_DIR / "media"
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 500))
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # larger uploads spool to disk
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
SUPPORTED_FORMATS = ["mp4", "mov", "avi"]
DATA_RETENTION_DAYS = os.environ.get("DATA_RETENTION_DAYS") or None

FRAME_INTERVAL_SECONDS = float(os.environ.get("FRAME_INTERVAL_SECONDS", 2))
FRAME_MAX_SIDE_PX = int(os.environ.get("FRAME_MAX_SIDE_PX", 1024))
SEARCH_MAX_RESULTS = int(os.environ.get("SEARCH_MAX_RESULTS", 50))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "gemma-4-26b-a4b-it")
GEMINI_TIMEOUT_SECONDS = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", 60))
GEMINI_MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", 3))

PROCESSING_MODE = os.environ.get("PROCESSING_MODE", "celery")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

CORS_ALLOWED_ORIGINS = [o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o]
CORS_EXPOSE_HEADERS = ["Content-Range", "Accept-Ranges", "Content-Length"]

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated" if env_bool("API_REQUIRE_AUTH") else "rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser", "rest_framework.parsers.MultiPartParser"],
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
}
LOGGING = {
    "version": 1, "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
