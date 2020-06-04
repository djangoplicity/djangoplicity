# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from djangoplicity.archives.utils import is_internal


def internal_request( request ):
    """
    Sets a context variable to check if a request is an internal request
    """
    return { 'INTERNAL_REQUEST': is_internal( request ) }
