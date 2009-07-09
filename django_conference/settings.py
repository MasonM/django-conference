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
    'infomanager@hssonline.org')


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
Must be a function that accepts the following parameters: a Registration
object, an Address object, a credit-card number, a credit-card CCV number,
and a credit-card expiration date. The return value should be "success"
if the authentication succeeded, else an error message.

Here's an example that uses the PyCC Authorize.NET API
(http://pycc.sourceforge.net/):

def authnet_auth(registration, address, cc_num, ccv_num, cc_exp_date):
    from AuthorizeNet import AuthNet
    authorize_net = AuthNet()
    registrant = registration.registrant
    authorize_net.data.update({
        'amount': str(registration.get_total()),
        'card_num': cc_num,
        'exp_date': cc_exp_date,
        'card_code': ccv_num,
        'first_name': registrant.first_name,
        'last_name': registrant.last_name,
        'address': address.address_line1+address.address_line2,
        'city': address.city,
        'state': str(address.state_province),
        'zip': address.postal_code,
        'country': str(adddress.country),
        'email': registrant.email,
    })
    authorize_net.execute()
    if authorize_net.status == '1':
        return "success"
    return authorize_net.error
"""
DJANGO_CONFERENCE_PAYMENT_AUTH_FUNC = getattr(settings,
    'DJANGO_CONFERENCE_PAYMENT_AUTH_FUNC',
    lambda *args, **kwargs: "DJANGO_CONFERENCE_PAYMENT_AUTH_FUNC not set!")
