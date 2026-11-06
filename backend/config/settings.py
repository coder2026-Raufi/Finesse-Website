"""
Finesse backend settings.

Everything that changes between your laptop and the real server comes from
environment variables (the .env file), never from the code.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent  # .../Finesse Website/backend
SITE_DIR = BASE_DIR.parent  # .../Finesse Website  (index.html lives here)

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        raise ImproperlyConfigured(f"{name} must be a whole number")


# ---------------------------------------------------------------- core
DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY in the environment / .env file.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
ADMIN_URL = os.environ.get("ADMIN_URL", "admin").strip("/")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inquiries",
    "portfolio",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves admin CSS/JS in production
    "inquiries.middleware.ApiOriginMiddleware",  # CORS + origin check for /api/
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dashboard.context.nav",
            ]
        },
    }
]

# ---------------------------------------------------------------- database
# SQLite is fine for a company website (one file, zero setup, easy backup).
# If traffic grows, switch to PostgreSQL by changing only this block.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    # PostgreSQL in production; SQLite remains the zero-configuration local option.
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("DB_PATH", str(BASE_DIR / "db.sqlite3")),
        }
    }
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Local development uses in-memory cache. For production, configure a shared
# cache so login throttling works across Gunicorn workers and server instances.
CACHE_BACKEND = os.environ.get("DJANGO_CACHE_BACKEND", "").strip()
if CACHE_BACKEND == "database":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": os.environ.get("DJANGO_CACHE_LOCATION", "django_cache"),
            "TIMEOUT": 300,
        }
    }
elif CACHE_BACKEND == "redis":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
            "TIMEOUT": 300,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "finesse-local-cache",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kabul"
USE_I18N = True
USE_TZ = True

# Uploaded project photos (added from the dashboard). On the real server this
# folder must be on a disk that is NOT erased on deploy.
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media")))

LOGIN_URL = "dashboard:login"
LOGIN_REDIRECT_URL = "dashboard:overview"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)  # avoids a harmless warning before the first collectstatic

# Reject huge request bodies early (a contact message is a few KB at most).
DATA_UPLOAD_MAX_MEMORY_SIZE = 20_000

# ---------------------------------------------------------------- email
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 10  # seconds: never let a slow mail server hang a visitor's request

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    # No credentials yet: print emails in the terminal instead of failing.
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "noreply@localhost"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
CONTACT_NOTIFY_TO = env_list("CONTACT_NOTIFY_TO", "finesse.researchmc@gmail.com")

# ---------------------------------------------------------------- anti-spam
CONTACT_RATE_LIMIT = env_int("CONTACT_RATE_LIMIT", 5)
CONTACT_RATE_WINDOW_MIN = env_int("CONTACT_RATE_WINDOW_MIN", 60)
NUM_PROXIES = env_int("NUM_PROXIES", 0)

# ---------------------------------------------------------------- production security
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"std": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "std"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
