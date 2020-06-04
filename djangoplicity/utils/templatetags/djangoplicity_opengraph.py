# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

import locale

from django import template
from django.conf import settings

register = template.Library()


@register.filter(name='opengraph_locale')
def opengraph_locale(value):
    '''
    Convert the LANGUAGE_CODE to an opengraph locale value
    '''
    if not settings.USE_I18N:
        value = settings.LANGUAGE_CODE

    if value == 'en':
        value = 'en-gb'

    if len(value) == 2:
        return locale.normalize(value.lower()).split('.')[0]
    elif len(value) == 5:
        lang, ter = value.split('-')
        return '%s_%s' % (lang.lower(), ter.upper())
    else:
        return ''


@register.filter(name='opengraph_image_url')
def opengraph_image_url(obj):
    '''
    Return the https url for og:image and og:image:secure_url
    '''
    resources = ('screen', 'videoframe', 'medium', 'thumb', 'thumbs')
    url = ''

    # First check if the object itself has resources
    for resource in resources:
        attr = 'resource_%s' % resource
        if hasattr(obj, attr) and getattr(obj, attr):
            url = getattr(obj, attr).absolute_url
            break

    # If we don't have a url we check if the obj has a main visual or
    # main image
    if not url and hasattr(obj, 'main_image'):
        main_image = getattr(obj, 'main_image')
        if main_image:
            for resource in resources:
                attr = 'resource_%s' % resource
                if hasattr(main_image, attr) and getattr(main_image, attr):
                    url = getattr(main_image, attr).absolute_url
                    break

    if not url and hasattr(obj, 'main_visual'):
        main_visual = getattr(obj, 'main_visual')
        if main_visual:
            for resource in resources:
                attr = 'resource_%s' % resource
                if hasattr(main_visual, attr) and getattr(main_visual, attr):
                    url = getattr(main_visual, attr).absolute_url
                    break

    if url.startswith('http:'):
        url.replace('http:', 'https:')
    return url


@register.filter(name='opengraph_image')
def opengraph_image(obj):
    '''
    Return the full opengraph properties for og:image and og:image:secure_url
    '''
    url = opengraph_image_url(obj)
    if not url:
        return ''

    secure_url = url
    url = url.replace('https:', 'http:')

    return '<meta property="og:image" content="%s" />' \
        '<meta property="og:image:secure_url" content="%s" />' % (url, secure_url)
