import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Security & Secret Keys
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-this-secret-key-before-production")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"

# Allowed Hosts & CSRF Settings for Render & Cloudflare Tunnels
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

if os.getenv("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.getenv("RENDER_EXTERNAL_HOSTNAME"))

CSRF_TRUSTED_ORIGINS = [
    "https://*.trycloudflare.com",
    "https://*.onrender.com",
]

# Security headers for Cloudflare / Render proxy forwarding
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# INSTALLED_APPS = [
#     'daphne',  # staticfiles र अन्य app भन्दा माथि हुनुपर्छ
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'cloudinary_storage',
#     'django.contrib.staticfiles',
#     'cloudinary',
#     'channels',
#     'chat',  # तपाईंको app नाम
# ]

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    
    # Cloudinary र Staticfiles को सही क्रम:
    'cloudinary',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    
    'channels',
    'chat',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Static files serving for Render
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ludochat.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]
    },
}]

WSGI_APPLICATION = "ludochat.wsgi.application"
ASGI_APPLICATION = "ludochat.asgi.application"

# Database Configuration
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = []

# Localization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

# Static Files (CSS, JavaScript, Images) Setup
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = []
if (BASE_DIR / "static").exists():
    STATICFILES_DIRS.append(BASE_DIR / "static")

# Django 4.2+ Compatible Storage Settings
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        # CompressedStaticFilesStorage ले कुनै फाइल मिसिए पनि साइटको CSS बिगार्दैन
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth Redirects
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

# Channel Layer Configuration (WebSocket Connection Expiry: 10s)
REDIS_URL = os.getenv("REDIS_URL", "").strip()

if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
                "expiry": 10,
            },
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
            "CONFIG": {
                "expiry": 10,
            },
        }
    }

# Session & Device Slot Management
MAX_ACTIVE_SESSIONS = 2
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SESSION_COOKIE_NAME = 'render_lschat_sessionid'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True

# Cloudinary Configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dxgemaqq',
    'API_KEY': '678431561825283',
    'API_SECRET': 'PW47GOeThcK6iyK2VSzdMSLn0Cc'
}