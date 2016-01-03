#!/usr/bin/env python
import sys
import os
from os.path import dirname, abspath
from optparse import OptionParser

from django.conf import settings, global_settings

if not settings.configured and not os.environ.get('DJANGO_SETTINGS_MODULE'):
    settings.configure(
        DATABASES={
            'default': {
                "ENGINE": 'django.db.backends.mysql',
                "NAME": 'conference',
                "USER": 'conferenceUser',
                "PASSWORD": 'conferencePass',
            }
        },
        INSTALLED_APPS=[
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

        DJANGO_MODERATION_MODERATORS = (
            'test@example.com',
        ),
        DEBUG=True,
        SITE_ID=1,
    )

from django.test.simple import DjangoTestSuiteRunner

def runtests(*test_args, **kwargs):
    if not test_args:
        test_args = ['django_conference']
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    test_runner = DjangoTestSuiteRunner(
        verbosity=kwargs.get('verbosity', 1),
        interactive=kwargs.get('interactive', False),
        failfast=kwargs.get('failfast')
    )
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--failfast', action='store_true', default=False, dest='failfast')

    (options, args) = parser.parse_args()

    runtests(failfast=options.failfast, *args)
