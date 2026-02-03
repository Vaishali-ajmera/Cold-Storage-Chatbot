from decouple import config

from advisory.settings.base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-local-+p%rziio8*k4l05-v^3)zr+t+$13!$7-#v!2s^hi^6)s+i*rx("

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cold_storage_advisory',  
        'USER': 'myuser',      
        'PASSWORD': config('DB_PASSWORD'),  
        'HOST': 'localhost',   
        'PORT': '5432',       
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# CORS Configurationd
CORS_ALLOW_ALL_ORIGINS = True

# Allow credentials
CORS_ALLOW_CREDENTIALS = True

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

# This would allow you to set this configuration
#  export DJANGO_SETTINGS_MODULE=advisory.settings.local_settings