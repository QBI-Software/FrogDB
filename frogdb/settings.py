"""
QBI Frog Database

*******************************************************************************
Developer Contact: e.cooperwilliams@uq.edu.au

Copyright (C) 2016  QBI Software, The University of Queensland

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
--------------------------------------------------------------------------------
Django settings for frogdb project.

Generated by 'django-admin startproject' using Django 1.9.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/

"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = 'md^dz3_%^e1zxycka2#_9cq=o170h9bhvk^f-8x(%a$8+_lhce'
with open(os.path.join(BASE_DIR,'frogdb/secret.txt')) as f:
    SECRET_KEY = f.read().strip()
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# OVERRIDE EMAIL SETTINGS
ADMINS =[('LizCW','e.cooperwilliams@uq.edu.au')]
ALLOWED_HOSTS = ['127.0.0.1',]

# Application definition

INSTALLED_APPS = [
    'frogs.apps.FrogsConfig',
    'solo.apps.SoloAppConfig',
    'suit',
    'suit_ckeditor',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
    'django_filters',
    'axes',
    'captcha',
    'django_cleanup',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.FailedLoginMiddleware',
]

ROOT_URLCONF = 'frogdb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

            ],
         },
    },
]

WSGI_APPLICATION = 'frogdb.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'qbifrogdb',
        'USER' : 'postgres',
        'PASSWORD' : 'superfrog',
        'HOST' : 'localhost',
        'PORT' : 5432
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Australia/Brisbane'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
# https://docs.djangoproject.com/en/1.9/howto/static-files/deployment/
STATIC_ROOT = os.path.join(BASE_DIR, 'frogs/static')
STATIC_URL = '/static/'
#PDF_URL='/static/pdfjs/web/viewer.html?file='
MEDIA_URL = '/frogs/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'frogs/media')
LOGIN_REDIRECT_URL ='/'
LOGIN_URL ='/'

#Lockout params
AXES_LOGIN_FAILURE_LIMIT = 3
AXES_COOLOFF_TIME = 1 #hours
AXES_LOCKOUT_URL ='/frogs/locked'