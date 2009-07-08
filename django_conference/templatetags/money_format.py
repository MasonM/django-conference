import locale
from decimal import Decimal

from django import template

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
register = template.Library()

@register.filter
def money_format(value):
    """
    Display float in money-style format with specified decimal places and
    comma-grouped thousands.
    """
    return locale.currency(Decimal(str(value)), grouping=True)
