# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

#
# SETTING for specifying if model fields for storing the resource by
# default should be added to the model. By default this is set to false
# The setting can be overridden in case by case.
#
from django.conf import settings

if settings.USE_I18N:
    from django.utils import translation as django_translation

CACHE_PREFIX = {
    'detail_view': 'djangoplicity.archives_detail_',
}


def _gen_cache_key( prefix, model_name, id, *args, **kwargs ):
    """
    Generate a cache key based on some prefix,
    model name and id of object.

    Extra args can be provided to specify different
    versions of the same page.
    """
    if settings.USE_I18N:
        lang = kwargs['lang'] if 'lang' in kwargs else django_translation.get_language()
        basekey = '%s%s_%s_%s' % ( prefix, lang, hash(model_name), hash(id) )
    else:
        basekey = '%s_%s_%s' % ( prefix, hash(model_name), hash(id) )

    for a in args:
        basekey = '%s_%s' % ( basekey, a )

    return basekey


if not hasattr( settings, 'ARCHIVE_URL_QUERY_PREFIX' ):
    settings.ARCHIVE_URL_QUERY_PREFIX = 'archive'

if not hasattr( settings, 'ARCHIVE_URL_DETAIL_PREFIX' ):
    settings.ARCHIVE_URL_DETAIL_PREFIX = 'detail'

if not hasattr( settings, 'ARCHIVE_URL_FEED_PREFIX' ):
    settings.ARCHIVE_URL_FEED_PREFIX = 'feed'

if not hasattr( settings, 'ARCHIVE_PAGINATOR_PREFIX' ):
    settings.ARCHIVE_PAGINATOR_PREFIX = 'page'
