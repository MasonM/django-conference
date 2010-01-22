from django.conf import settings


"""
This is the URL prefix for the media files used by django-conference.
"""
DJANGO_CONFERENCE_MEDIA_ROOT = getattr(settings,
    'DJANGO_CONFERENCE_MEDIA_ROOT',
    '/media')


"""
Django-conference stores all e-mails as HTML and uses a text-browser to
convert them to text. The default is W3M, but Elinks would also work well.
Here's the command string for ELinks: elinks -force-html -stdin -dump -no-home
"""
DJANGO_CONFERENCE_HTML2TEXT_CMD = getattr(settings,
    'DJANGO_CONFERENCE_HTML2TEXT_CMD',
    'w3m -dump -T text/html -cols 80 -O ascii')


"""
Contact e-mail address used to set the "From" address for e-mails sent by
the system and for various "contact us for help" links.
"""
DJANGO_CONFERENCE_CONTACT_EMAIL = getattr(settings,
    'DJANGO_CONFERENCE_CONTACT_EMAIL',
    'example@example.com')


"""
A tuple of the form (app_name, model) that corresponds to the model
that should be used for the Registration.registrant and Paper.presenter
foreign keys. This is mainly for sites that extend the User model
via inheritance, as detailed at
http://scottbarnham.com/blog/2008/08/21/extending-the-django-user-model-with-inheritance/
"""
DJANGO_CONFERENCE_USER_MODEL = getattr(settings,
    'DJANGO_CONFERENCE_USER_MODEL',
    ('auth', 'User'))


"""
A tuple representing the function to use for performing payment authentication.
The first element of the tuple should be the package and second should be the
function name. The function must accept a dictionary of the following form:
{
    'address_line1': <first line of address>,
    'address_line2': <second line of address>,
    'postal_code': <postal/zip code>,
    'city': <city>,
    'state_province': <state or province ISO code>,
    'country': <country ISO code>,
    'number': <credit card #>,
    'holder': <name on credit card>,
    'expiration': <expiration date as a Python Date object>,
    'ccv_number': <credit card CCV #>,
    'total': <total amount to charge as a Decimal object>,
    'registrant': <User object>,
    'description': <descriptive string describing registration>,
}
The return value should be "success" if the authentication succeeded,
else an error message.

Here's an example that uses the PyCC Authorize.NET API
(http://pycc.sourceforge.net/):

def authnet_auth(**kwargs):
    from AuthorizeNet import AuthNet
    authorize_net = AuthNet()
    registrant = kwargs['registration'].registrant
    authorize_net.data.update({
        'amount': str(kwargs['registration'].get_total()),
        'card_num': kwargs['number'],
        'exp_date': kwargs['expiration'].strftime("%m/%Y"),
        'card_code': kwargs['ccv_number'],
        'first_name': registrant.first_name,
        'last_name': registrant.last_name,
        'address': kwargs['address_line1']+kwarrgs['address_line2'],
        'city': kwargs['city'],
        'state': kwargs['state_province'],
        'zip': kwargs['postal_code'],
        'country': kwargs['country'],
        'email': registrant.email,
    })
    authorize_net.execute()
    if authorize_net.status == '1':
        return "success"
    return authorize_net.error
"""
DJANGO_CONFERENCE_PAYMENT_AUTH_FUNC = getattr(settings,
    'DJANGO_CONFERENCE_PAYMENT_AUTH_FUNC',
    None)


"""
A tuple representing the form to use for billing addresses. The first element
of the tuple should be package and the second is the class name.
This is override-able so that sites with their own address models/forms can
integrate with Django-conference.
Note that the form must have a save() method and accept a "user" parameter in
the constructor
"""
DJANGO_CONFERENCE_ADDRESS_FORM = getattr(settings,
    'DJANGO_CONFERENCE_ADDRESS_FORM',
    ("django_conference.forms", "AddressForm"))


"""
URL to redirect registrants to who are not logged in.
"""
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/account')


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
