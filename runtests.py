#!/usr/bin/env python
import sys
import os
from os.path import dirname, abspath
from optparse import OptionParser

from django.conf import settings

if not settings.configured and not os.environ.get('DJANGO_SETTINGS_MODULE'):
    settings.configure(
        DATABASES = {
            'default': {
                "ENGINE": 'django.db.backends.mysql',
                "NAME": 'conference',
                "USER": 'conferenceUser',
                "PASSWORD": 'conferencePass',
            }
        },
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',

            'django_conference',
        ],
        SERIALIZATION_MODULES = {},
        MEDIA_URL = '/media/',
        STATIC_URL = '/media/',
        ROOT_URLCONF = 'django_conference.urls',
        DJANGO_CONFERENCE_ABSTRACT_MAX_WORDS = 10,
        DJANGO_CONFERENCE_DISABLE_PAYMENT_PROCESSING = True,
        DEBUG = True,
        SITE_ID = 1,
    )

from django.test.utils import setup_test_environment
from django.test.simple import DjangoTestSuiteRunner

def runtests(options):
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    setup_test_environment()
    test_runner = DjangoTestSuiteRunner(**options)
    failures = test_runner.run_tests(['django_conference'])
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--verbosity', default=1, dest='verbosity')
    parser.add_option('--interactive', action='store_true', default=False,
        dest='interactive')
    parser.add_option('--failfast', action='store_true', default=False,
        dest='failfast')

    (options, args) = parser.parse_args()

    runtests(vars(options))
