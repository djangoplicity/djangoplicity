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

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from djangoplicity.eventcalendar.forms import EventForm
from djangoplicity.eventcalendar.models import Event, EventType, EventCountry, EventTypeProxy


class EventCountryAdmin( admin.ModelAdmin ):
    list_display = ['name', 'isocode']
    search_fields = ['name', 'isocode']


class EventTypeAdmin( admin.ModelAdmin ):
    list_display = ['name', 'slug']
    search_fields = ['name', 'slug', 'description']
    fieldsets = (
        ( None, {'fields': ( 'slug', 'name', 'description', 'published', 'opengraph_image', ) } ),
    )


class EventTypeProxyAdmin( admin.ModelAdmin ):
    list_display = ('name', 'lang', 'slug')
    search_fields = ('name', 'slug', 'description')
    fieldsets = (
        ( 'Language', {'fields': ( 'source', 'lang', ) } ),
        ( None, {'fields': ( 'name', 'description', ) } ),
    )


class EventAdmin( admin.ModelAdmin ):
    list_display = ['title', 'published', 'city', 'country', 'start_date', 'end_date', 'ongoing', 'type', 'last_modified']
    list_editable = [ 'city', 'country', 'ongoing', 'type']
    list_filter = ['published', 'type', 'ongoing', 'country', 'last_modified', 'created', ]
    readonly_fields = [ 'last_modified', 'created', ]
    search_fields = ['title', 'link', 'description', 'city', 'country__name', ]
    fieldsets = [
        ( None, { 'fields': [ ( 'last_modified', 'created', )] } ),
        ( _( "Publishing" ), { 'fields': [ 'published', ] } ),
        ( _( "Date and time" ), { 'fields': [ 'ongoing', 'start_date', 'end_date', 'timezone' ] } ),
        ( _( "Content" ), { 'fields': [ 'title', 'link', 'description', 'type' ] } ),
        ( _( "Location" ), { 'fields': [ 'city', 'country', ] } ),
    ]
    form = EventForm

    def get_queryset(self, request):
        return super(EventAdmin, self).get_queryset(request).select_related(
            'country', 'type')


def register_with_admin( admin_site ):
    admin_site.register( Event, EventAdmin )
    admin_site.register( EventType, EventTypeAdmin )
    admin_site.register( EventCountry, EventCountryAdmin )
    admin_site.register( EventTypeProxy, EventTypeProxyAdmin )

# Register with default admin site
register_with_admin( admin.site )
