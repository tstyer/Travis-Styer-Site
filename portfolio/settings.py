import json
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local env.py if present (local development only)
if os.path.isfile(BASE_DIR / "env.py"):
    import env  # noqa: F401

# -------------------------------------------------------------------
# Debug + Security / Secret Key
# -------------------------------------------------------------------

# DEBUG from env (supports common truthy values)
DEBUG = False

# Security / Secret Key
SECRET_KEY = os.getenv("SECRET_KEY")

# Fail hard if production is misconfigured
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set.")

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "[::1]",
    ".herokuapp.com",
]

# -------------------------------------------------------------------
# Google credentials (service account)
# -------------------------------------------------------------------
GOOGLE_CREDS_DICT = None
GOOGLE_SERVICE_ACCOUNT_FILE = None

if os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"):
    GOOGLE_CREDS_DICT = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
else:
    # Fallback for local development
    GOOGLE_SERVICE_ACCOUNT_FILE = BASE_DIR / "creds.json"

# -------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main.apps.MainConfig",
    # For Images
    "storages",
]

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------
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

ROOT_URLCONF = "portfolio.urls"

# -------------------------------------------------------------------
# Templates
# -------------------------------------------------------------------
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

WSGI_APPLICATION = "portfolio.wsgi.application"

# -------------------------------------------------------------------
# Database
# -------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# -------------------------------------------------------------------
# Password validation
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# -------------------------------------------------------------------
# Internationalisation
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Static & media files
# -------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "main" / "static",
]

# -------------------------------------------------------------------
# Main Media - S3
# -------------------------------------------------------------------

AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = (
    f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
)
AWS_QUERYSTRING_AUTH = False

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
            "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "default_acl": None,
            "querystring_auth": False,
            "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

# -------------------------------------------------------------------
# Defaults
# -------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# Google Sheet config
# -------------------------------------------------------------------
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# -------------------------------------------------------------------
# Logging (console-friendly even with DEBUG=False)
# -------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
