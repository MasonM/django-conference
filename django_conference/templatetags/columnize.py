from django.template.defaultfilters import stringfilter
from django import template

import textwrap

register = template.Library()

@register.filter(is_safe=True)
@stringfilter
def columnize(textblock, width):
    """
    Simple helper to take in a plain-text definition list delimited by colons
    and add formats it nicely.

    Example input:
col1: foo
a really long term: bar
l: baz
    
    Output of columnize:10
col1:       foo

a really  
long term:  bar

l:          baz
    """
    lines = unicode(textblock).split("\n")
    return columnize_helper(lines, width)

def columnize_helper(lines, width):
    out = ""
    for line in lines:
        if ":" in line:
            label, value = line.split(':', 1)
            label_lines = textwrap.wrap(label, width)
            label_lines[-1] += ':'
            out += columnize_helper(label_lines[:-1], width)
            out += "%s %s\n\n" % (label_lines[-1].ljust(width), value)
        else:
            out += line.ljust(width) + "\n"
    return out
