
"""
Django settings for Weather Routing.

Django 6.1.2
Supports local development and Render production deployment.
"""

from pathlib import Path
import os

from dotenv import load_dotenv


# ============================================================
# BASE DIRECTORY & ENVIRONMENT VARIABLES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    raise ValueError(
        "DJANGO_SECRET_KEY environment variable must be configured."
    )

DEBUG = os.getenv(
    "DJANGO_DEBUG", "False"
).lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]

SECURE_CONTENT_TYPE_NOSNIFF = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SECURE_SSL_REDIRECT = not DEBUG

# Trust this header only when deployed behind a trusted
# reverse proxy, such as the intended Render deployment.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

# Leave HSTS disabled during initial deployment.
# Enable gradually after verifying production HTTPS.
SECURE_HSTS_SECONDS = int(
    os.getenv("DJANGO_HSTS_SECONDS", "0")
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


# ============================================================
# THIRD-PARTY API CONFIGURATION
# ============================================================

# OpenRouteService geocoding
ORS_API_KEY = os.getenv("ORS_API_KEY", "")

ORS_BASE_URL = os.getenv(
    "ORS_BASE_URL",
    "https://api.openrouteservice.org",
)

# Mapbox Directions
MAPBOX_ACCESS_TOKEN = os.getenv(
    "MAPBOX_ACCESS_TOKEN", ""
)

MAPBOX_BASE_URL = os.getenv(
    "MAPBOX_BASE_URL",
    "https://api.mapbox.com",
)

# Open-Meteo Forecast
OPEN_METEO_BASE_URL = os.getenv(
    "OPEN_METEO_BASE_URL",
    "https://api.open-meteo.com/v1/forecast",
)

# ============================================================
# WEATHER API PERFORMANCE CONFIGURATION
# ============================================================

WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "")

WEATHERAPI_BASE_URL = os.getenv(
    "WEATHERAPI_BASE_URL",
    "https://api.weatherapi.com/v1",
)

# Weather forecast spatial grid
WEATHER_GRID_DEGREES = float(
    os.getenv("WEATHER_GRID_DEGREES", "0.35")
)

# Maximum concurrent WeatherAPI requests
WEATHER_MAX_WORKERS = int(
    os.getenv("WEATHER_MAX_WORKERS", "6")
)

# Forecast cache duration (seconds)
WEATHER_CACHE_SECONDS = int(
    os.getenv("WEATHER_CACHE_SECONDS", "1800")
)

WEATHER_MAX_LOCATIONS = int(
    os.getenv("WEATHER_MAX_LOCATIONS", "35")
)

WEATHER_MAX_SAMPLE_DISTANCE_KM = float(
    os.getenv("WEATHER_MAX_SAMPLE_DISTANCE_KM", "90")
)


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",

    # Local apps
    "routing",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URLS & WSGI
# ============================================================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# TEMPLATES
# ============================================================

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


# ============================================================
# DATABASE
# ============================================================

# SQLite is sufficient for this stateless assessment MVP.
# For persistent production application data, use PostgreSQL.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


# ============================================================
# CORS CONFIGURATION
# ============================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        (
            "http://localhost:5173,"
            "http://127.0.0.1:5173"
        ),
    ).split(",")
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = False


# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],

    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],

    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/hour",
    },
}


# ============================================================
# CACHING
# ============================================================

# Suitable for a single-process development/MVP environment.
# Use Redis for shared caching across production workers.

REDIS_URL = os.getenv("REDIS_URL", "")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "weather-routing",
            "TIMEOUT": 900,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": (
                "django.core.cache.backends.locmem.LocMemCache"
            ),
            "LOCATION": "weather-routing-local",
            "TIMEOUT": 900,
        }
    }

# ============================================================
# API REQUEST LIMITS
# ============================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

# Email delivery is not used in this assessment.
# SMTP settings must be configured if email is introduced.

MAILERS = {
    "default": {
        "BACKEND": (
            "django.core.mail.backends.smtp.EmailBackend"
        ),
    }
}


# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "simple": {
            "format": (
                "[{levelname}] {asctime} "
                "{name}: {message}"
            ),
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },

    "root": {
        "handlers": ["console"],
        "level": os.getenv(
            "DJANGO_LOG_LEVEL", "INFO"
        ),
    },

    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "routing": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
