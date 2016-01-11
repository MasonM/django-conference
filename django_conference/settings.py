from django.conf import settings


"""
Contact e-mail address used to set the "From" address for e-mails sent by
the system and for various "contact us for help" links.
"""
DJANGO_CONFERENCE_CONTACT_EMAIL = getattr(settings,
    'DJANGO_CONFERENCE_CONTACT_EMAIL',
    'example@example.com')


"""
A tuple of the form (app_name, model) that corresponds to the model
that should be used for the Registration.registrant, Session.submitter, and
Paper.submitter foreign keys. This is mainly for sites that extend the User
model via inheritance, as detailed at
http://scottbarnham.com/blog/2008/08/21/extending-the-django-user-model-with-inheritance/
"""
DJANGO_CONFERENCE_USER_MODEL = getattr(settings,
    'DJANGO_CONFERENCE_USER_MODEL',
    ('auth', 'User'))


"""
If set to True, automatically accept all payment details, bypassing Stripe. 
Only for use in tests.
"""
DJANGO_CONFERENCE_DISABLE_PAYMENT_PROCESSING = getattr(settings,
    'DJANGO_CONFERENCE_DISABLE_PAYMENT_PROCESSING',
    False)


"""
Publishable key for Stripe
"""
DJANGO_CONFERENCE_STRIPE_PUBLISHABLE_KEY = getattr(settings,
    'DJANGO_CONFERENCE_STRIPE_PUBLISHABLE_KEY',
    '')


"""
Secret key for Stripe
"""
DJANGO_CONFERENCE_STRIPE_SECRET_KEY = getattr(settings,
    'DJANGO_CONFERENCE_STRIPE_SECRET_KEY',
    '')


"""
List of additional admin tasks. Each item in the list can must be a tuple of
the following form: ("description", view_func)
Where "description" is what should appear in the task selection drop-down and
view_func is the view function. The view function will be passed the request
and selected meeting (in that order) and must return a response. If view_func
is a list or a tuple, the view function will be dynamically imported by using
the first element as the module and the second as the function name.
view function.
Example:
[("Checklist", lambda request, meeting: show_checklist(request, meeting)),
 ("Generate Receipts", generate_receipts),
 ("Generate Packet Labels", generate_packet_labels),
 ("Dynamically imported task", ("my_project.module", "view_function")]
"""
DJANGO_CONFERENCE_ADMIN_TASKS = getattr(settings,
    'DJANGO_CONFERENCE_ADMIN_TASKS',
    [])


"""
Limit for the number of words (determined by splitting on spaces) abstracts may
have. Default is zero, which means no limit.
"""
DJANGO_CONFERENCE_ABSTRACT_MAX_WORDS = getattr(settings,
    'DJANGO_CONFERENCE_ABSTRACT_MAX_WORDS', 0)
