
from django import template

register = template.Library()

@register.filter
def restaurants(d, key):
    r = d[key]
    return [x for x in r.items()]
