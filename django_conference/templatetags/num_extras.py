from django import template

from django_conference.models import ExtraType, RegistrationExtra

register = template.Library()


@register.simple_tag
def num_extras(registration, extra_type_name):
    """
    Helper tag that returns the number of extras that the given registration
    contains. First argument must be the registration, second must be the
    name of the extra type.
    """
    try:
        extra_type = models.ExtraType.get(name = extra_type_name)
    except ExtraType.DoesNotExist:
        err = 'num_extras received invalid extra type'
        raise template.TemplateSyntaxError(err)
    try:
        regextra = registration.regextras.get(extra__extra_type = extra_type)
        return regextra.quantity
    except RegistrationExtra.DoesNotExist:
        return 0
