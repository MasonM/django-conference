from django import template

from django_conference.models import DonationType, RegistrationDonation

register = template.Library()


@register.tag()
def num_donated(registration, donation_type_name):
    """
    Helper tag that returns the amount that the given registration donated
    to a given cause. First argument must be the registration, second must be
    the name of the donation type.
    """
    try:
        donate_type = models.DonationType.get(name = donate_type_name)
    except DonationType.DoesNotExist:
        err = 'num_donated received invalid donation type'
        raise template.TemplateSyntaxError(err)
    try:
        regdonation = registration.regdonations.get(
            donate_type__donate_type = donate_type)
        return regdonation.quantity
    except RegistrationDonation.DoesNotExist:
        return 0
