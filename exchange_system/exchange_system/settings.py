import os
from dotenv import load_dotenv
from pathlib import Path
from django.conf import settings
from django.conf.urls.static import static
from icecream import ic


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
ENVIRONMENT = os.getenv('ENVIRONMENT', '')
if not ENVIRONMENT:
    raise ValueError("La variable ENVIRONMENT no está definida en el archivo .env")
dotenv_specific_path = os.path.join(BASE_DIR, f".env.{ENVIRONMENT}")
if Path(dotenv_specific_path).is_file():
    load_dotenv(dotenv_specific_path)
else:
    raise ValueError(f"El archivo {dotenv_specific_path} no existe. Asegúrate de tener el archivo correcto para el entorno.")

DB_NAME = os.getenv('DB_NAME')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("La variable SECRET_KEY no está definida en el archivo .env")

DEBUG = os.getenv('DEBUG', "")
ic(f"DEBUG: {DEBUG}")

ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS').split(',') if host.strip()]

if not DEBUG and not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS no está definido en el archivo .env para el entorno de producción")

# Path to the logs directory
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    'rest_framework',
    "rest_framework_simplejwt",
    'drf_spectacular',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "exchange_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'core/templates')], 
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
WSGI_APPLICATION = 'exchange_system.wsgi.application'

# Configuración de la base de datos
REQUIRED_DB_KEYS = ['ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST']
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
for key in REQUIRED_DB_KEYS:
    if not DATABASES['default'].get(key):
        raise ValueError(f"La configuración de la base de datos {key} no está definida en el archivo .env")

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
MEDIA_URL = '/media/'
#STATIC_ROOT = '/home/Elige/ewp/'
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static"),
# ]
if ENVIRONMENT in ['production', 'testing']:
    # Configuración para producción
    STATIC_ROOT = os.getenv('STATIC_ROOT')
    STATICFILES_DIRS = []  # En producción, no necesitas STATICFILES_DIRS
    MEDIA_ROOT = os.getenv('MEDIA_ROOT')  # Producción: ruta dedicada para archivos subidos
else:
    # Configuración para desarrollo/pruebas
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
        # os.path.join(
        #     BASE_DIR,
        #     'venv3.10/lib/python3.10/site-packages/django_ckeditor_5/static',
        # ),
    ]

    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
# Para verificar la configuración aplicada
if DEBUG:
    ic(f"Env: {ENVIRONMENT}")
    ic(f"STATICFILES_DIRS: {STATICFILES_DIRS}")
    ic(f"STATIC_ROOT: {STATIC_ROOT}")
    ic(f"MEDIA_ROOT: {MEDIA_ROOT}")
    ic(f"BASE_DIR: {BASE_DIR}")
    ic(f"TEMPLATES: {TEMPLATES[0]['DIRS']}")

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],

}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),  # Directory where cache files will be stored
        'TIMEOUT': 86400,  # Cache expires after 24 hours
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Maximum number of cache entries
        },
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/exchange_system.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'core': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

MIDDLEWARE += ['core.middleware.GlobalExceptionMiddleware']

FIXER_API_KEY = os.getenv("FIXER_API_KEY")

