"""Pytest configuration and fixtures for django-turnstile-site-protect tests."""
import os
import sys

import pytest
from django.conf import settings, global_settings
from django.test import RequestFactory, TestCase

# Configure Django settings for tests
if not settings.configured:
    # Set the default Django settings module for the 'django' tests.
    settings.configure(
        SECRET_KEY='test-secret-key',
        ROOT_URLCONF='django_turnstile_site_protect.urls',
        INSTALLED_APPS=[
            'django.contrib.sessions',
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django.contrib.messages',
            'django_turnstile_site_protect',
        ],
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django_turnstile_site_protect.middleware.TurnstileMiddleware',
        ],
        MESSAGE_STORAGE='django.contrib.messages.storage.fallback.FallbackStorage',
        TURNSTILE_SITE_KEY='test-site-key',
        TURNSTILE_SECRET_KEY='test-secret-key',
        TURNSTILE_EXCLUDED_PATHS=['/excluded/path/'],
        TURNSTILE_EXCLUDED_IPS=['192.168.1.1', '10.0.0.0-10.0.0.255'],
        TURNSTILE_EXCLUDED_DOMAINS=['example.com', '*.test.com'],
        ALLOWED_HOSTS=['testserver', 'example.com', 'test.com', 'subdomain.test.com', 'example.org'],
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.request',
                    ],
                },
            },
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE,
    )

    # Set up Django
    import django
    django.setup()


@pytest.fixture
def rf():
    """RequestFactory instance."""
    return RequestFactory()


@pytest.fixture
def turnstile_settings():
    """Fixture to modify Turnstile settings for testing."""
    from django.test import override_settings
    return override_settings(
        TURNSTILE_SITE_KEY='test-site-key',
        TURNSTILE_SECRET_KEY='test-secret-key',
        TURNSTILE_EXCLUDED_PATHS=['/excluded/path/'],
        TURNSTILE_EXCLUDED_IPS=['192.168.1.1', '10.0.0.0-10.0.0.255'],
        TURNSTILE_EXCLUDED_DOMAINS=['example.com', '*.test.com'],
    )
