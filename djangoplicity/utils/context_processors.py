# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.conf import settings


def site_environment(request):
    """
    Set site environment template variable.

    Will be the value of whatever is in the settings.ini file.
    """
    if hasattr( settings, 'SITE_ENVIRONMENT' ):
        return { 'site_environment': settings.SITE_ENVIRONMENT }

    return {}


def project_environment(request):
    """
    Set site environment template variable.

    Will be the value of whatever is in the settings.ini file.
    """
    if hasattr( settings, 'PRJNAME' ):
        return { 'project_environment': settings.PRJNAME }

    return {}


def google_analytics_id( request ):
    if hasattr( settings, 'GA_ID' ):
        return { 'GA_ID': settings.GA_ID }

    return {}


def djangoplicity_environment( request ):
    """
    Replacement for above context processors.
    """
    return {
        'DJANGOPLICITY': {
            'HAS_SHOP': hasattr( settings, 'SATCHMO_SETTINGS' ),
            'URL_PREFIX': '/{}'.format(settings.URLS_BASEPATH) if hasattr(settings, 'URLS_BASEPATH') else '',
            'SHOP_LIVE': settings.LIVE if hasattr( settings, 'LIVE' ) else False,
            'PROJECT_ENVIRONMENT': settings.PRJNAME if hasattr( settings, 'PRJNAME' ) else None,
            'SITE_ENVIRONMENT': settings.SITE_ENVIRONMENT if hasattr( settings, 'SITE_ENVIRONMENT' ) else None,
            'SITE_DOMAIN': settings.SITE_DOMAIN if hasattr( settings, 'SITE_DOMAIN' ) else None,
            'GA_ID': settings.GA_ID if hasattr( settings, 'GA_ID' ) else None,
            'FACEBOOK_APP_ID': settings.FACEBOOK_APP_ID if hasattr( settings, 'FACEBOOK_APP_ID' ) else None,
            'USE_I18N': settings.USE_I18N,
        },
    }
