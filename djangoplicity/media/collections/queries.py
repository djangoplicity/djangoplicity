# -*- coding: utf-8 -*-
#
# djangoplicity-media
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

from djangoplicity.archives.contrib.queries import AllPublicQuery, param_extra_templates
from djangoplicity.media.collections.models import ImageCollection
from django.http import Http404
from django.core import validators
from django.core.exceptions import ValidationError

collection_extra_templates = param_extra_templates( param='collection', selector=lambda obj, query: obj.slug )


class CollectionQuery( AllPublicQuery ):
    """
    """
    def __init__( self, collection_cls=ImageCollection, *args, **kwargs ):
        defaults = {
            'include_in_urlpatterns': True,
            'url_template': 'djangoplicity.archives.contrib.queries.urls.param',
            'extra_templates': collection_extra_templates,
        }
        self.collection_cls = collection_cls
        defaults.update( kwargs )
        super( CollectionQuery, self, *args, **defaults ).__init__(*args, **kwargs)

    def queryset( self, model, options, request, stringparam=None, **kwargs ):
        if not stringparam:
            raise Http404

        # Validate input param before passing it on to the database.
        try:
            validators.validate_slug( stringparam )
        except ValidationError:
            raise Http404

        # Find collection
        try:
            collection = self.collection_cls.objects.get( slug=stringparam )
        except self.collection_cls.DoesNotExist:
            raise Http404

        # Make query
        ( qs, query_data ) = super( CollectionQuery, self ).queryset( model, options, request, **kwargs )
        qs = collection.filter( qs )

        # Add some extra data to the query.
        query_data.update( { 'collection': collection } )

        return ( qs, query_data )

    def url_args( self, model, options, request, stringparam=None, **kwargs ):
        """
        Hook for query to specify extra reverse URL lookup arguments.
        """
        return [ stringparam ]

    def verbose_name( self, collection=None, **kwargs ):
        """
        Method that can be overwritten to customize the archive title.
        """
        try:
            if collection:
                return self._verbose_name % { 'title': collection.title }
        except TypeError:
            pass
        return self._verbose_name


# Helper function for specifying extra templates for CategoryQuery
