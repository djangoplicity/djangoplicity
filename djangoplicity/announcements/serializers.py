# -*- coding: utf-8 -*-
#
# djangoplicity-announcements
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

from djangoplicity.announcements.models import Announcement
from djangoplicity.archives.contrib.serialization import SimpleSerializer
from djangoplicity.archives.utils import get_instance_archives, \
    get_instance_archives_urls, related_archive_items


# ==========================================
# Announcements
# ==========================================
class AnnouncementSerializer( SimpleSerializer ):
    fields = (
        'id',
        'title',
        'subtitle',
        'description',
        'contacts',
        'links',
        'featured',
        'release_date',
        'visuals',
        'lang',
        'url',
    )

    def get_visuals_value( self, obj ):
        images = related_archive_items( Announcement.related_images, obj )
        videos = related_archive_items( Announcement.related_videos, obj, has_main_visual=False )

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
                } for relobj in images],
            'videos': [
                {
                    'id': relobj.id,
                    'source_id': relobj.source.id if relobj.source else None,
                    'featured': relobj.featured,
                    'formats': get_instance_archives(relobj),
                    'formats_url': get_instance_archives_urls(relobj),
                    'url': 'http://%s%s' % (get_current_site(None), relobj.get_absolute_url()),
                    'title': relobj.title,
                } for relobj in videos],
        }

    def get_url_value( self, obj ):
        return 'http://%s%s' % (get_current_site(None), obj.get_absolute_url())


class ICalAnnouncementSerializer( SimpleSerializer ):
    fields = (
        'summary',
        'description',
        'dtstart',
        'dtend',
        'dtstamp',
    )

    def get_summary_value( self, obj ):
        return "ESO Announcement %s - %s" % ( obj.id, ( ( "%s - %s" % ( obj.title, obj.subtitle ) ) if obj.subtitle else obj.title ) )

    def get_description_value( self, obj ):
        return obj.description

    def get_dtstart_value( self, obj ):
        return obj.release_date

    def get_dtend_value( self, obj ):
        return obj.release_date

    def get_dtstamp_value( self, obj ):
        return obj.release_date


# ==========================================
# Web updates
# ==========================================
class WebUpdateSerializer( SimpleSerializer ):
    fields = (
        'id',
        'title',
        'description',
        'link',
        'type',
        'release_date',
    )

    def get_release_date_value( self, obj ):
        return self.append_timezone( obj.release_date )


class ICalWebUpdateSerializer( SimpleSerializer ):
    fields = (
        'summary',
        'description',
        'dtstart',
        'dtend',
        'dtstamp',
    )

    def get_summary_value( self, obj ):
        return "New on %s %s - %s" % ( get_current_site(None), obj.id, obj.title )

    def get_description_value( self, obj ):
        return obj.description

    def get_dtstart_value( self, obj ):
        return self.append_timezone( obj.release_date )

    def get_dtend_value( self, obj ):
        return self.append_timezone( obj.release_date )

    def get_dtstamp_value( self, obj ):
        return self.append_timezone( obj.release_date )
