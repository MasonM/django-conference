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
        extra_type = ExtraType.objects.get(name = extra_type_name)
    except ExtraType.DoesNotExist:
        err = 'num_extras received invalid extra type'
        raise template.TemplateSyntaxError(err)
    try:
        regextra = registration.regextras.get(extra__extra_type = extra_type)
        return regextra.quantity
    except RegistrationExtra.DoesNotExist:
        return 0


@register.tag
def has_extra(parser, token):
    """
    Same as num_extras, except it returns "Yes" if given registration includes
    one or more of one of the given extra_type, else returns "No"
    """
    args = token.split_contents()[1:]
    if len(args) < 2:
        raise template.TemplateSyntaxError, "has_extra takes at least 2 args"
    return HasExtraNode(args[0], [arg[1:-1] for arg in args[1:]])


class HasExtraNode(template.Node):
    def __init__(self, registration, extras):
        self.registration = template.Variable(registration)
        self.extras = extras

    def render(self, context):
        try:
            registration = self.registration.resolve(context)
        except template.VariableDoesNotExist:
            return 'No'

        for extra_type_name in self.extras:
            num = num_extras(registration, extra_type_name)
            if num > 0:
                return "Yes"
        return "No" 
