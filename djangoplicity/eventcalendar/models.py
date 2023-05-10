# -*- coding: utf-8 -*-
#
# djangoplicity-eventcalendar
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
#

"""
Models for the event calendar.

Worth noting is the support for timezones on start/end dates.
"""

from builtins import str
from django.conf import settings
from django.db import models
from django.utils import dateformat, formats
from django.utils.translation import ugettext_lazy as _
from djangoplicity.translation.models import TranslationModel
from djangoplicity.utils.datetimes import timezone
from pytz import all_timezones
from six import python_2_unicode_compatible

EVENT_TZS = [( tz, tz ) for tz in all_timezones]

#
# Models
#


@python_2_unicode_compatible
class EventType( TranslationModel ):
    slug = models.SlugField()
    name = models.CharField( max_length=255 )
    published = models.BooleanField( default=True )
    description = models.TextField( blank=True )
    opengraph_image = models.CharField(_(u'OpenGraph Image'), blank=True, max_length=250,
            help_text=_(u"Example: 'https://www.eso.org/public/archives/imagecomparisons/newsfeature/potw1413a.jpg'. If given: full path to an image that will be used when sharing the page on social media. Must be larger than 200x200px and smaller than 5MB."))

    class Translation:
        fields = ['name', 'description']
        excludes = []

    class Meta:
        ordering = ['name']

    def __str__( self ):
        return self.name


class EventTypeProxy(EventType):
    '''
    EventType proxy model for creating admin only to edit
    translated objects.
    '''
    objects = EventType.translation_objects

    class Meta:
        proxy = True
        verbose_name = _('Event types translation')
        ordering = ['lang', 'name']


@python_2_unicode_compatible
class EventCountry( models.Model ):
    isocode = models.SlugField( max_length=2, verbose_name="ISO code" )
    name = models.CharField( max_length=255 )

    class Meta:
        ordering = ['name']
        verbose_name_plural = _( 'event countries' )

    def __str__( self ):
        return self.name



@python_2_unicode_compatible
class Event( models.Model ):
    title = models.CharField( max_length=255 )
    link = models.URLField( blank=True )
    description = models.TextField( blank=True )
    city = models.CharField( max_length=255, blank=True )
    country = models.ForeignKey( EventCountry, null=True, blank=True, on_delete=models.SET_NULL )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField( blank=True, null=True )
    timezone = models.CharField( max_length=40, default=settings.TIME_ZONE, choices=EVENT_TZS )
    ongoing = models.BooleanField( default=False )
    type = models.ForeignKey( EventType, null=True, blank=True, on_delete=models.SET_NULL )

    published = models.BooleanField( default=True )
    last_modified = models.DateTimeField( auto_now=True )
    created = models.DateTimeField( auto_now_add=True )

    def save(self, *args, **kwargs ):
        if self.end_date is None:
            self.end_date = self.start_date
        return super( Event, self ).save(*args, **kwargs )

    def get_dates( self ):
        if self.end_date and self.start_date:
            if self.end_date.year != self.start_date.year:
                return "%s - %s" % ( formats.date_format( self.start_date ), formats.date_format( self.end_date ) )
            elif self.end_date.month != self.start_date.month:
                return "%s - %s %s" % ( dateformat.format( self.start_date, "j F" ), dateformat.format( self.end_date, "j F" ), self.start_date.year )
            elif self.end_date.day != self.start_date.day:
                return "%s - %s %s" % ( dateformat.format( self.start_date, "j" ), dateformat.format( self.end_date, "j" ), dateformat.format( self.start_date, "F Y" ) )
            else:
                return formats.date_format( self.start_date )
        else:
            return formats.date_format( self.start_date )

    def get_location( self ):
        location = ""

        if self.city:
            location = self.city

        if self.country:
            c = str( self.country )
            location += ", %s" % c if location else c

        return location

    def _get_date_tz( self, date ):
        if not date:
            return None
        return timezone( date, tz=self.timezone )

    def _get_start_date_tz( self ):
        return self._get_date_tz( self.start_date )

    def _get_end_date_tz( self ):
        return self._get_date_tz( self.end_date )

    start_date_tz = property( _get_start_date_tz )
    end_date_tz = property( _get_end_date_tz )

    def __str__( self ):
        return self.title

    class Meta:
        ordering = ['-start_date']
