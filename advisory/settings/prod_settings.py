from decouple import config

from advisory.settings.base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-local-+p%rziio8*k4l05-v^3)zr+t+$13!$7-#v!2s^hi^6)s+i*rx("

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DBNAME"),
        "USER": config("DBUSER"),
        "PASSWORD": config("DBPASSWORD"),
        "HOST": config("DBHOST"),
        "PORT": config("DBPORT"),  # Default PostgreSQL port
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://72.62.248.39",
]

# CORS Configurationd
CORS_ALLOW_ALL_ORIGINS = True

# Allow credentials
CORS_ALLOW_CREDENTIALS = True

STATIC_URL = "/static/"
STATIC_ROOT = "/var/www/cold_storage_static"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/var/www/cold_storage_media"
SESSION_COOKIE_NAME = "cold_storage_sessionid"
CSRF_COOKIE_NAME = "cold_storage_csrftoken"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
CSRF_TRUSTED_ORIGINS = [
    "http://72.62.248.39:8007",
]

# This would allow you to set this configuration
#  export DJANGO_SETTINGS_MODULE=advisory.settings.prod_settings
