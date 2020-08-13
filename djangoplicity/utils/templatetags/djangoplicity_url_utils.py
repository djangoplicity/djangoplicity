# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
from future import standard_library
standard_library.install_aliases()
from django import template
import urllib.request, urllib.parse, urllib.error
register = template.Library()


@register.simple_tag
def url_encode_dict(param_dict):
    return urllib.parse.urlencode(param_dict)
