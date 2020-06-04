# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from django.http import Http404, HttpResponse
from django.conf import settings


def alive_check( request ):
    """
    View for checking that all services are running. Can be used by a monitoring service
    to check for problems with the website.
    """
    if request.META.get('INTERNAL_REQUEST', False):
        return HttpResponse(status=204)

    raise Http404


def empty_view(request, text="" ):
    """
    Empty place holder view

    Can include text if paramter is added to URL like e.g.::

        url( '^empty/', 'djangoplicity.views.empty_view', text="Some text" )
    """
    return HttpResponse( text, content_type="text/plain" )


def get_static_media_path( request ):
    return HttpResponse(settings.MEDIA_URL)
