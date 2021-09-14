# Djangoplicity
# -*- coding: utf-8 -*-
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django import template
from django.conf import settings
from datetime import datetime
import math
import pycountry
import re

register = template.Library()
numeric_test = re.compile("^\d+$")

@register.filter( name='sort_list' )
def sort_list( value ):
    """
    Expects a dictionary and returns a sorted list
    """
    return sorted(value.items())


@register.filter( name='split_list' )
def split_list( value, arg ):
    """
    Simple template filter split a list into a list of lists of
    certain size.

    Example::
        {% for list in object_list|split_list:"4" %}
    """
    try:
        split_count = int(arg)
    except ValueError:
        return value

    if value:
        list_count = int(math.ceil(float(len(value)) / split_count))

        result = []
        for i in range(list_count):
            result.append( value[i * split_count:(i + 1) * split_count] )

        return result
    else:
        return value


@register.inclusion_tag('paginator_tag.html')
def paginator( paginator, page_obj, paginator_url, paginator_prefix, paginator_params=None ):
    """
    {% load djangoplicity_utils %}
    {% paginator paginator page_obj %}
    """
    return {
        'paginator': paginator,
        'adj_range': paginator.adj_range(page_obj),
        'page_obj': page_obj,
        'paginator_prefix': paginator_prefix,
        'paginator_url': paginator_url,
        'paginator_params': paginator_params,
    }


@register.inclusion_tag('statusbar.html')
def statusbar( paginator, page_obj, browsers=None, searchable=False, search_url='', search_str='', ):
    """
    {% load djangoplicity_utils %}
    {% statusbar paginator page_obj browsers searchable %}
    """
    return {
        'paginator': paginator,
        'page_obj': page_obj,
        'searchable': searchable,
        'browsers': browsers,
        'search_str': search_str,
        'search_url': search_url,
    }


@register.filter( name='any' )
def any(lst):
    return any(lst)


@register.filter( name='any_arg' )
def any_arg(lst, arg):
    if not lst:
        return False
    for val in lst:
        if hasattr(val, arg) and getattr(val, arg):
            return True
    return False


# basic math operations
@register.filter
def mult(value, arg):
    "Multiplies the arg and the value"
    return int(value) * int(arg)


@register.filter
def sub(value, arg):
    "Subtracts the arg from the value"
    return int(value) - int(arg)


@register.filter
def div(value, arg):
    "Divides the value by the arg"
    return int(value) / int(arg)


@register.filter
def country_to_code(name):
    '''
    Return the country name for the given code
    E.g.: Belgium -> be
    '''
    # Deal with exceptions:
    if name == 'USA':
        name = 'United States'
    elif name == 'Russia':
        name = 'Russian Federation'

    try:
        c = pycountry.countries.get(name=name)
        return c.alpha2.lower()
    except KeyError:
        return ''


@register.filter
def code_to_country(code):
    '''
    Return the country name for the given code
    E.g.: fr-be => Belgium
    '''
    for c, lang in settings.LANGUAGES:
        if c == code:
            return lang

    return code


@register.filter
def code_to_country_prefix(code):
    '''
    Return the country name for the given code
    E.g.: fr-be => /public/belgium-fr/
    '''
    for prefix, c in settings.LANGUAGE_PREFIX.iteritems():
        if c == code:
            return prefix

    return code


@register.filter
def code_to_country_code(code):
    '''
    Return the country code for the given code
    E.g.: fr-be => be
    '''
    if code == 'sr-latn':
        # special case
        return code
    elif '-' in code:
        return code.split('-')[1]
    else:
        return code


@register.filter
def code_to_local_country(code):
    '''
    Return the country name for the given code translated
    in the code's language.
    E.g.: fr-be => Belgique, nl-be => België
    '''
    try:
        return settings.LOCAL_COUNTRIES[code]
    except KeyError:
        return code


@register.filter
def code_to_local_language(code):
    '''
    Return the language name for the given code translated
    in the code's language.
    E.g.: fr-be => Français (Belgique), de => Deutsch
    '''
    try:
        return settings.LOCAL_LANGUAGES[code]
    except KeyError:
        return code


@register.filter
def get_local_languages(languages):
    '''
    Returns a list of language_name, language_code with language name in the
    code's language. The list is sorted by translated language name
    '''

    local_languages = []

    if not languages:
        return

    for code, _lang in languages:
        if code == settings.LANGUAGE_CODE:
            # We handle the default language separately
            continue
        try:
            local_lang = settings.LOCAL_LANGUAGES[code]
        except KeyError:
            local_lang = code

        local_languages.append((local_lang, code))

    local_languages.sort()
    return [(settings.LOCAL_LANGUAGES[settings.LANGUAGE_CODE], settings.LANGUAGE_CODE)] + local_languages


@register.filter(name='years_range')
def years_range(start):
    '''
    Returns a list of years up the current one (included)
    '''
    return range(int(start), datetime.now().year + 1)


@register.filter
def is_eu_country(country):
    '''
    Returns True if the given country code is part of the European Union
    '''
    EU_COUNTRIES = set(['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'GB'])
    return country.upper() in EU_COUNTRIES


@register.filter
def is_southam_country(country):
    '''
    Returns True if the given country code is part of south america
    '''
    SOUTHAM_COUNTRIES = set(['AR', 'BO', 'BR', 'CL', 'CO', 'EC', 'FK', 'GF', 'GY', 'GY', 'PY', 'PE', 'SR', 'UY', 'VE'])
    return country.upper() in SOUTHAM_COUNTRIES


@register.filter
def is_elsewhere_country(country):
    '''
    Returns True if the given country code is neither part of EU nor SA
    '''
    return not is_eu_country(country) and not is_southam_country(country)


@register.filter
def pop_querydict_key(querydict, keys):
    '''
    Makes a copy of the querydict, remove the given key(s) and returns a query string
    If multiple keys are provided (separated by a ',') they are all removed.
    '''
    if ',' in keys:
        keys = [ x.strip() for x in keys.split(',') ]
    else:
        keys = [keys]

    querydict = querydict.copy()

    for key in keys:
        while key in querydict:
            querydict.pop(key)

    return querydict.urlencode()


@register.filter
def endswith(value, arg):
    """
    Return true if value endswith arg

    Example::
        {% if variable|endswith:".mov" %}
    """
    return value.endswith(arg)


@register.filter
def startswith(value, arg):
    """
    Return true if value startswith arg

    Example::
        {% if variable|startswith:"http://" %}
    """
    return value.startswith(arg)


@register.simple_tag
def has_attribute(model, attribute):
    """
    check out if exists an attribute of an object dynamically from a string name

    Example::
        {% has_attribute original "get_report_url" as has_report %}
    """

    if hasattr(model, str(attribute)):
        return True
    elif hasattr(model, 'has_key') and model.has_key(attribute):
        return True
    elif numeric_test.match(str(attribute)) and len(model) > int(attribute):
        return True
    else:
        return False
