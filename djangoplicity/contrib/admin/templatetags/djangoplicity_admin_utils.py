# Djangoplicity
# Copyright 2007-2009 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.conf import settings
from django.utils.safestring import mark_safe
from django import template
register = template.Library()


@register.filter(name='boolean_icon')
def display_boolean_icon(field_val):
    BOOLEAN_MAPPING = {'1': 'yes', True: 'yes', 'on': 'yes', 'off': 'no', '0': 'no', False: 'no', '': 'unknown', None: 'unknown'}

    return mark_safe(u'<img src="%sadmin/img/icon-%s.svg" alt="%s" />' % (settings.STATIC_URL, BOOLEAN_MAPPING[field_val], field_val))
