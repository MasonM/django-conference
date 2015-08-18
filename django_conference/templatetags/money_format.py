from decimal import Decimal

from django import template

register = template.Library()

@register.filter
def money_format(value):
    """
    Display float in money-style format with specified decimal places and
    comma-grouped thousands.
    Adapted from https://docs.python.org/2/library/decimal.html#recipes
    """
    q = Decimal(10) ** -2      # 2 places --> '0.01'
    _, digits, exp = Decimal(str(value)).quantize(q).as_tuple()
    result = []
    digits = map(str, digits)
    build, next = result.append, digits.pop
    for i in range(2):
        build(next() if digits else '0')
    build('.')
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(',')
    build('$')
    return ''.join(reversed(result))
