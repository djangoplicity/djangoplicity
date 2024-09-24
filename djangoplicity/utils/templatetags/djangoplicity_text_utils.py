# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from builtins import str
from django import template
from django.contrib.sites.models import Site
from django.template.defaultfilters import stringfilter
from bs4 import BeautifulSoup
from djangoplicity.utils.html_cleanup import convert_html_entities
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter( name='truncateparagraph_html' )
def truncateparagraph_html(value):
    soup = BeautifulSoup(value, 'lxml')
    result = soup.find('p')
    return str( result ).strip()


@register.filter( name='remove_html' )
def remove_html_tags(value):
    """
    Remove all HTML tags, convert HTML entities into
    unicode characters and strip leading/trailing whitespace.
    """
    return convert_html_entities(strip_tags(value)).strip()


def _remove_bold_italic( text ):
    TAGS_OUT = ['em', 'i', 'u', 'b', 'strong']

    soup = BeautifulSoup(text, 'lxml')

    for tag in soup.findAll(True):
        if tag.name in TAGS_OUT:
            tag.hidden = True

    return soup.renderContents().decode('utf-8')


@register.filter( name='html2text' )
def html2text( value ):
    """
    Convert HTML into text (valid Markdown)
    """
    try:
        from djangoplicity.utils.html_to_text import DjangoplicityHTML2Text

        value = _remove_bold_italic(value)

        h2t = DjangoplicityHTML2Text(baseurl="http://%s" % Site.objects.get_current().domain)
        return h2t.handle( value ).replace('&nbsp_place_holder;', ' ').strip()
    except ImportError:
        return value


@register.filter( name='html2textnolinks' )
def html2textnolinks( value ):
    """
    Convert HTML into text (valid Markdown), ignore links
    """
    try:
        from djangoplicity.utils.html_to_text import DjangoplicityHTML2Text

        value = _remove_bold_italic(value)

        h2t = DjangoplicityHTML2Text(baseurl="http://%s" % Site.objects.get_current().domain)
        h2t.ignore_links = True
        return h2t.handle( value ).replace('&nbsp_place_holder;', ' ').strip()
    except ImportError:
        return value


@register.filter( name='unescape' )
def unescape( value ):
    """
    Convert HTML entities
    """
    try:
        import html2text as h2t

        return h2t.unescape( value, unicode_snob=True ).replace( "--", "-" ).replace('&nbsp_place_holder;', ' ')
    except ImportError:
        return value


@register.filter( name='underscore_to_space' )
@stringfilter
def underscore_to_space( value ):
    """
    Simple template filter to replace underscores in a string
    with spaces. This can eg. be used to convert a Python module name
    into a nice string.

    Example::

        {{ app_label|underscore_to_space }}
    """
    return value.replace( '_', ' ' )


@register.filter
def sp2nbsp( value ):
    try:
        value = str( value )
        value = value.replace( " ", "&nbsp;" )
        return mark_safe(value)
    except:
        return value


@register.filter
def truncatechars( value, arg ):
    """
    Truncate a string to a certain amount of characters,
    and appends ... if string is truncated.

    Example::

    {{ alongtext|truncatechars:20 }}
    """
    try:
        value = str(value)
        arg = int(arg)
    except:
        return value

    if arg < 3:
        return value

    if len(value) > arg - 3:
        return "%s..." % value[:arg - 3]
    else:
        return value


@register.filter
def remove_html_except(value, arg):
    '''
    Remove HTML tags from string except for those in 'arg'
    '''
    if arg:
        valid_tags = arg.split(',') if ',' in arg else [arg, ]
    else:
        valid_tags = None
    valid_attrs = 'href src'.split()

    soup = BeautifulSoup(value, 'lxml')
    for tag in soup.findAll(True):
        if tag.name not in valid_tags:
            tag.hidden = True
        tag.attrs = {attr: val for attr, val in tag.attrs.items() if attr in valid_attrs}
    return soup.renderContents().decode('utf8').replace('javascript:', '')
