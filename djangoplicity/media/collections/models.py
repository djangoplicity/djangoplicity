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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from six import python_2_unicode_compatible
import json
from djangoplicity.metadata.models import SubjectName, TaxonomyHierarchy, Facility, Instrument
from djangoplicity.metadata import consts


@python_2_unicode_compatible
class ImageCollection( models.Model ):
    slug = models.SlugField( db_index=True, help_text=_( "Part of the URL" ) )
    title = models.CharField( max_length=255, blank=False, null=False, help_text=_( "Title of collection" ) )

    subject_category = models.ManyToManyField( TaxonomyHierarchy, blank=True )
    subject_name = models.ManyToManyField( SubjectName, blank=True )
    facility = models.ManyToManyField( Facility, blank=True )
    instrument = models.ManyToManyField( Instrument, blank=True )

    query = models.TextField( default="[]" )

    def filter( self, queryset ):
        qs_filters = json.loads( self.query )

        for ( type, params ) in qs_filters:
            if type == 'filter':
                queryset = queryset.filter( **params )
            elif type == 'exclude':
                queryset = queryset.exclude( **params )

        return queryset

    def make_query( self ):
        filters = [
            ( 'subject_category__in', self.subject_category.all(), 'pk' ),
            ( 'subject_name__in', self.subject_name.all(), 'pk' ),
            ( 'imageexposure__facility__in', self.facility.all(), 'pk' ),
            ( 'imageexposure__facility__in', self.instrument.all(), 'pk' ),
            ( 'type__in', self.imagetype_set.all(), 'type' ),
        ]

        params = {}
        for k, qs in filters:
            if qs:
                params[k] = [x.pk for x in qs]

        return json.dumps( [( 'filter', params )] )

    def __str__( self ):
        return self.title

    def save( self, *args, **kwargs ):
        self.query = self.make_query()
        super( ImageCollection, self ).save( *args, **kwargs )


@python_2_unicode_compatible
class ImageType( models.Model ):
    collection = models.ForeignKey( ImageCollection, on_delete=models.CASCADE)
    type = models.CharField( max_length=12, choices=consts.TYPE_CHOICES )

    def __str__( self ):
        return self.get_type_display()
