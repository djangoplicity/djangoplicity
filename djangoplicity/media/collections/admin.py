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

from django.contrib import admin
from djangoplicity.media.collections.models import ImageCollection, ImageType


class BaseAdmin( admin.ModelAdmin ):
    list_display = ('id', 'name', 'slug')
    list_editable = ('name', 'slug')
    search_fields = ( 'name', 'slug', )
    fieldsets = (
        ( None, { 'fields': ( 'name', 'slug', ) }),
    )
    ordering = ('name',)
    prepopulated_fields = { 'slug': ('name',) }


class ImageTypeInlineAdmin( admin.TabularAdmin ):
    model = ImageType


class ImageCollectionAdmin( admin.ModelAdmin ):
    list_display = ( 'slug', 'title', )
    list_filter = ( 'last_modified', 'published', 'type', 'location', 'location__site' )
    list_editable = ( 'series', 'type', 'location', )
    search_fields = ( 'title', 'speaker', 'location__name', 'series__name', 'type', 'affiliation', 'abstract', )
    fieldsets = (
        ( 'Event or meeting', { 'fields': ( 'type', 'series', 'title', 'speaker', 'affiliation', 'abstract', 'image', 'video_url', 'additional_information' ) } ),
        ( 'Locaiton and date', { 'fields': ( 'start_date', 'end_date', 'location', ) } ),
        ( 'Publishing', {'fields': ( 'published', 'last_modified', 'created' ), } ),
    )
    readonly_fields = ( 'last_modified', 'created', )
    raw_id_fields = ( 'image', )
    ordering = ( '-start_date', )


def register_with_admin( admin_site ):
    admin_site.register( ImageCollection, ImageCollectionAdmin )

# Register with default admin site
register_with_admin( admin.site )
