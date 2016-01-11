from django import template

from django_conference import settings

register = template.Library()

@register.inclusion_tag('django_conference/notice.html')
def show_notice(notice):
    """Shows a notice given by the string 'notice'"""
    return { 'notice': notice }
