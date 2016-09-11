# Overview

django-conference is intended to be a complete conference and symposia
management system. It provides the functionality needed to organize conferences
and allow attendees to register for the conference online.

# Features

* Integrates with Django's user authentication system.
* Allows papers and session proposals to be submitted by any registered user.
* Easy-to-use admin interface for reviewing and approving sessions and papers.
* Customizable reporting engine to view registration and session/paper submission statistics.
* Highly customizable registration system that integrates with Stripe for payment.

# Dependencies

* Python 2.7
* Django 1.8+
* [django-autocomplete-light 3.0+](https://github.com/yourlabs/django-autocomplete-light)

# Installation
Run `python setup.py install` to install django-conference and any missing dependencies.

# Using in an Existing Django Project
If you want to integrate django-conference with an existing project, follow these steps:

1. Add `"django_conference"` to the `INSTALLED_APPS` tuple in the project's `settings.py` file.
2. Add `django-autocomplete-light` to `INSTALLED_APPS` [as detailed here](https://django-autocomplete-light.readthedocs.io/en/master/install.html#install-in-your-project).
3. Add `(r'^conference/', include('django_conference.urls'))` to the project's `urls.py` file.

# Using Standalone
If you don't have an existing Django project, you'll need to create one. Use
the project in the "example_project" directory as a starting point and
customize the settings.py file for your server. See the following pages for
more information:

* [Deploying Django](http://docs.djangoproject.com/en/dev/howto/deployment/)
* [Django settings documentation](http://docs.djangoproject.com/en/dev/topics/settings/)
