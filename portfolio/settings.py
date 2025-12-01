"""
Django settings for portfolio project.
"""

from pathlib import Path
import json, os
import dj_database_url
if os.path.isfile('env.py'):
    import env

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

GOOGLE_CREDS_DICT = None
GOOGLE_SERVICE_ACCOUNT_FILE = None

if os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"):
    GOOGLE_CREDS_DICT = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
else:
    # Fallback for local dev with a file
    GOOGLE_SERVICE_ACCOUNT_FILE = BASE_DIR / "creds.json"

# Security
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    # Local-only fallback. Never use in production.
    SECRET_KEY = "dev-secret-key-change-me"
    print(
        "WARNING: Using fallback SECRET_KEY. "
        "Set SECRET_KEY in the environment for production."
    )

# DEBUG: default True for local dev; override with env DEBUG=false in prod.
DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]", ".herokuapp.com"]

# Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",
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

ROOT_URLCONF = "portfolio.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # add BASE_DIR / "templates" if you keep project-level templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                # Needed because your templates use `request`
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "portfolio.wsgi.application"


# Database (sqlite local)
#DATABASES = {
#    "default": {
#        "ENGINE": "django.db.backends.sqlite3",
#        "NAME": BASE_DIR / "db.sqlite3",
#    }
#}

DATABASES = {
    'default': dj_database_url.parse(os.environ.get("DATABASE_URL"))
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# I18N
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "main" / "static",
    ]

# Use Manifest storage only when not DEBUG (prevents 500s in dev if collectstatic not run)
if DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Google 
GOOGLE_SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "creds.json")
GOOGLE_SHEET_ID = "1NaIYrKXeWzqj9zHOwyd8vR0sTMlXG0mdmiDu-BNCSQU"

# Helpful logging to console (even if DEBUG=False)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
