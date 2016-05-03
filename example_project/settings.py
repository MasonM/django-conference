# Django settings for election project.
import os

DEBUG = True # Turn this off before releasing!
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": 'django.db.backends.mysql',
        "NAME": 'conference',
        "USER": 'conferenceUser',
        "PASSWORD": 'conferencePass',
        "HOST": '',
        "PORT": '',
    },
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

WEB_ROOT = os.getcwd()

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

STATIC_ROOT = WEB_ROOT + "/static/"
STATICFILES_DIRS = ( WEB_ROOT + 'media/', )

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'sh)ip(^)gy+0!n83ayuk599b1()40-^%m*!$4e*ube61w#8fpi'

ROOT_URLCONF = 'example_project.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    WEB_ROOT + '/templates/',
)

INSTALLED_APPS = (
    'django_conference',
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
)

DJANGO_CONFERENCE_CONTACT_EMAIL = "mason.malone@gmail.com"
DJANGO_CONFERENCE_MEDIA_ROOT = "/media/conference"
DJANGO_CONFERENCE_ADMIN_TASKS = [
   ("receipts.html", "Generate Receipts", ["html"], True),
   ("sessions.html", "Accepted Session Details", ["html"], False),
]
