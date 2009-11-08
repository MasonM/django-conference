from django import template

from django_conference.models import DonationType, RegistrationDonation

register = template.Library()


@register.tag()
def num_donated(registration, donate_type_name):
    """
    Helper tag that returns the amount that the given registration donated
    to a given cause. First argument must be the registration, second must be
    the name of the donation type.
    """
    try:
        donate_type = DonationType.objects.get(name = donate_type_name)
    except DonationType.DoesNotExist:
        err = 'num_donated received invalid donation type'
        raise template.TemplateSyntaxError(err)
    try:
        regdonation = registration.regdonations.get(
            donate_type__donate_type = donate_type)
        return regdonation.quantity
    except RegistrationDonation.DoesNotExist:
        return 0


@register.simple_tag
def has_donated(registration, donate_type_name):
    """
    Same as num_donated, except it returns "Yes" if given registration donated
    more than $0 for the given donation type, else returns "No"
    """
    num = num_donated(registration, donate_type_name) 
    if num > 0:
        return "Yes"
    return "No"
