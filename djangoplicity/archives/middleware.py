# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from djangoplicity.archives.utils import is_internal


class InternalRequestMiddleware( object ):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        response = self.get_response(request)

        return response

    def process_request( self, request ):
        """
        Checks if a request is an internal request and set a META variable with the state.

        Normally this middleware should be installed together with the context processor:
        djangoplicity.archives.context_processors.internal_request
        """
        request.META['INTERNAL_REQUEST'] = is_internal( request )
