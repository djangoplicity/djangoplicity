# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
from django import template
import urllib
register = template.Library()


@register.simple_tag
def url_encode_dict(param_dict):
    return urllib.urlencode(param_dict)
