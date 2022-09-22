"""
Copyright 2022 Secureworks, Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

"""
Django settings for azure project.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-i6_@mw%he&2j#u0+_5696n32-00f8x)&3h=!rl!6=v%ezcdzv^"

# AZURE CONFIG FROM ENVIRONMENT
AUTH_DNS = os.getenv("AUTH_DNS") or "login.microsoft.com"
ISSUER_DNS = os.getenv("ISSUER_DNS") or "login.microsoftonline.com"
OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID") or "HardCode"
OAUTH2_TENANT_ID = os.getenv("OAUTH2_TENANT_ID") or "HardCode"

# Not typically required but included to demo requesting a service token / session
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET") or "Service Only"

# This is found under the service principal of the Enterprise Application and is not
# the Object ID under your app registration.
OAUTH2_APP_OID = os.getenv("OAUTH2_APP_OID") or "Top level id corresponding to ent app"

# Note that the iss in the token is NOT the same as the AUTH_DNS url
OAUTH2_AUTHORITY = (
    os.getenv("OAUTH2_AUTHORITY") or f"https://{AUTH_DNS}/{OAUTH2_TENANT_ID}"
)
OAUTH2_JWKS_URI = (
    os.getenv("OAUTH2_JWS_URI")
    or f"https://{AUTH_DNS}/{OAUTH2_TENANT_ID}/discovery/v2.0/keys"
)
OAUTH2_ISSUER = (
    os.getenv("OAUTH2_ISSUER") or f"https://{ISSUER_DNS}/{OAUTH2_TENANT_ID}/v2.0"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# It needs to allow the host that is provided from the azure proxy host headers.
ALLOWED_HOSTS = [
    "127.0.0.1",  # For heartbeat
    "localhost",
    os.getenv("SERVER_NAME"),
    os.getenv("INTERNAL_SERVER_NAME"),
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
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

ROOT_URLCONF = "azure.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "azure.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
