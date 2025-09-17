import os
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from pathlib import Path
from decouple import config

# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security configuration
SECRET_KEY = config("SECRET_KEY", default="replace_me_with_a_secure_key")

# Use a boolean for `IN_PRODUCTION` for easier checks
IN_PRODUCTION = config("IN_PRODUCTION", default=True, cast=bool)

# CSRF trusted origins and CORS configuration
CSRF_TRUSTED_ORIGINS = ["http://localhost:*"]
CORS_ALLOW_CREDENTIALS = True

# Custom Middleware configuration
CUSTOM_MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
]

# Enable debug-related middleware in non-production environments
if not IN_PRODUCTION:
    DEBUG = True
    ALLOWED_HOSTS = ["*"]
    CORS_ALLOWED_ORIGINS = ["http://localhost:*"]
    CUSTOM_MIDDLEWARE.extend(
        [
            "external.middleware.ip_address.PrintIpAddressMiddleware",
            "external.middleware.raw_query.SQLLoggingMiddleware",
            # "external.middleware.request_logging.RequestLoggingMiddleware",
        ]
    )
else:
    DEBUG = False
    ALLOWED_HOSTS = [""]
    CORS_ALLOW_ALL_ORIGINS = True


# Custom and third-party app configurations
CUSTOM_APPS = []  # Add your custom apps here

INSTALLED_LIBRARIES = [
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "rest_framework_simplejwt.token_blacklist",
    "django_ckeditor_5",
]


INSTALLED_APPS = (
    [
        "jazzmin",  # For admin UI customization
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ]
    + CUSTOM_APPS
    + INSTALLED_LIBRARIES
)


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
] + CUSTOM_MIDDLEWARE


# Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# URL and WSGI configurations
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", cast=str),
        "NAME": config("DB_NAME", cast=str),
        "USER": config("DB_USER", cast=str),
        "PASSWORD": config("DB_PASSWORD", cast=str),
        "HOST": config("DB_HOST", cast=str),
        "PORT": config("DB_PORT", cast=int),
    }
}

# Authentication and password validation
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

# Django Rest Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

# Language and timezone settings
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

# Static and media file settings
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static/collect_static"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Auto field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User model
# AUTH_USER_MODEL = ""

# File upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB
FILE_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB

SESSION_COOKIE_AGE = 30000


# JWT configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=60),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# CKEditor configuration
CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "full",
        "height": 300,
        "width": "100%",
    },
}

# Spectacular settings for API schema generation
SPECTACULAR_SETTINGS = {
    "TITLE": "REST API",
    "DESCRIPTION": "A fine product built with Django",
    "VERSION": "1.0.0",
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "docExpansion": "none",
        # To prevent schema to be appeared uncomment the following
        # 'defaultModelsExpandDepth': -1,
    },
    "DEFAULT_AUTO_SCHEMA": "drf_spectacular.openapi.AutoSchema",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PUBLIC": True,
    "USE_SESSION_AUTH": False,
    "REDUCER": "drf_spectacular.reducing.RouterDepthReducer",
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_DIST": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest",
    "SWAGGER_UI_FAVICON_HREF": STATIC_URL + "images/api.ico",
}

# Jazzmin configuration for admin UI
JAZZMIN_SETTINGS = {
    "site_brand": "Admin",
    "login_logo": "images/mr_robot.png",
    "jazzy_logo": "images/mr_robot.png",
    "site_logo": "images/mr_robot.png",
    "site_logo_classes": "img-circle elevation-3",
    "welcome_sign": "Welcome",
    "hide_models": [
        "auth.Group",
        "auth.Permission",
        "authtoken.Token",
        "token_blacklist.BlacklistedToken",
        "token_blacklist.OutstandingToken",
    ],
    "hide_apps": [
        "auth",
        "token_blacklist",
    ],
    "show_sidebar": True,
    "navigation_expanded": False,
    "show_ui_builder": False,
    "default_icon_parents": "fas fa-chevron-circle-down",
    "default_icon_children": "fas fa-arrow-right",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "litera",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
