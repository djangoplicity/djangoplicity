# -*- coding: utf-8 -*-
#
# djangoplicity-releases
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

from django.contrib.sites.shortcuts import get_current_site

from djangoplicity.archives.contrib.serialization import SimpleSerializer
from djangoplicity.archives.utils import get_instance_archives, \
    get_instance_archives_urls, related_archive_items
from djangoplicity.metadata.serializers import ExtendedContactSerializer
from djangoplicity.releases.models import Release
from djangoplicity.utils.datetimes import timestring_to_seconds


class ReleaseSerializer( SimpleSerializer ):
    fields = (
        'id',
        'lang',
        'release_type',
        'title',
        'subtitle',
        'release_city',
        'headline',
        'description',
        'notes',
        'more_information',
        'links',
        'disclaimer',
        'kids_title',
        'kids_description',
        'release_date',
        'visuals',
        'url',
)

    related_fields = (
        'publications',
        'subject_category',
        'subject_name',
        'facility',
        ( 'releasecontact_set', ExtendedContactSerializer, {}, 'contacts' ),
    )

    related_cache = (

    )

    def get_visuals_value( self, obj ):
        images = related_archive_items( Release.related_images, obj )
        videos = related_archive_items( Release.related_videos, obj, has_main_visual=False )
        stock_images = related_archive_items( Release.stock_images, obj, has_main_visual=False )

        return {
            'images': [
                {
                    'id': relobj.id,
                    'source_id': relobj.source.id if relobj.source else None,
                    'is_main_visual': relobj.is_main_visual,
                    'featured': relobj.featured,
                    'width': relobj.width,
                    'height': relobj.height,
                    'formats': get_instance_archives(relobj),
                    'formats_url': get_instance_archives_urls(relobj),
                    'url': 'http://%s%s' % (get_current_site(None), relobj.get_absolute_url()),
                    'title': relobj.title,
                } for relobj in images ],
            'videos': [
                {
                    'id': relobj.id,
                    'source_id': relobj.source.id if relobj.source else None,
                    'featured': relobj.featured,
                    'formats': get_instance_archives(relobj),
                    'formats_url': get_instance_archives_urls(relobj),
                    'duration': timestring_to_seconds(relobj.file_duration) if relobj.file_duration else None,
                    'url': 'http://%s%s' % (get_current_site(None), relobj.get_absolute_url()),
                    'title': relobj.title,
                } for relobj in videos],
            'stockimages': [
                {
                    'id': relobj.id,
                } for relobj in stock_images],
        }

    def get_release_date_value( self, obj ):
        return self.append_timezone( obj.release_date )

    def get_url_value( self, obj ):
        return 'http://%s%s' % (get_current_site(None), obj.get_absolute_url())


class ICalReleaseSerializer( SimpleSerializer ):
    fields = (
        'summary',
        'description',
        'dtstart',
        'dtend',
        'dtstamp',
    )

    def get_summary_value( self, obj ):
        return "ESO %s %s - %s" % ( obj.release_type.name, obj.id, ( ( "%s - %s" % ( obj.title, obj.subtitle ) ) if obj.subtitle else obj.title ) )

    def get_description_value( self, obj ):
        return obj.headline

    def get_dtstart_value( self, obj ):
        return self.append_timezone( obj.release_date )

    def get_dtend_value( self, obj ):
        return self.append_timezone( obj.release_date )

    def get_dtstamp_value( self, obj ):
        return self.append_timezone( obj.release_date )


class MiniReleaseSerializer( SimpleSerializer ):
    fields = (
        'id',
        'lang',
        'release_type',
        'title',
        'subtitle',
        'headline',
        'release_date',
        'main_visual',
    )

    related_fields = (
        'subject_category',
        'subject_name',
        'facility',
    )

    related_cache = (
    )

    def get_main_visual_value( self, obj ):
        images = related_archive_items( Release.related_images, obj )
        # By default related_archive_items put 'main visual' images first
        # so we can simply return the first one
        if images:
            return images[0].id

    def get_release_date_value( self, obj ):
        return self.append_timezone( obj.release_date )
