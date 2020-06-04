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

"""
"""

from djangoplicity.archives.feeds import DjangoplicityArchiveFeed
from djangoplicity.feeds import conf as feedsconf
from djangoplicity.releases.models import Release
from djangoplicity.releases.options import ReleaseOptions


class ReleaseFeed( DjangoplicityArchiveFeed ):
    title = feedsconf.get( 'ReleaseFeedSettings', 'title', 'News' )
    link = feedsconf.get( 'ReleaseFeedSettings', 'link', '/' )
    description = feedsconf.get( 'ReleaseFeedSettings', 'description', 'News' )
    override_guids = feedsconf.get( 'ReleaseFeedSettings', 'override_guids', {} )
    title_template = feedsconf.get( 'ReleaseFeedSettings', 'title_template', 'feeds/release_title.html' )
    description_template = feedsconf.get( 'ReleaseFeedSettings', 'description_template', 'feeds/release_description.html' )

    class Meta( DjangoplicityArchiveFeed.Meta ):
        model = Release
        options = ReleaseOptions
        latest_fieldname = Release.Archive.Meta.release_date_fieldname
        enclosure_resources = { '': 'resource_screen' }
        default_query = ReleaseOptions.Queries.default
        category_query = None
        items_to_display = 10
        archive_query = "default"
        external_feed_url = feedsconf.get( 'ReleaseFeedSettings', 'external_feed_url', None )

    def item_pubdate( self, item ):
        """
        Takes an news item, as returned by items(), and returns the news'
        release date.
        """
        return item.release_date

    def item_enclosure_url( self, item ):
        """
        Use main image for press release as enclosure.
        """
        im = item.main_image
        if im and im.resource_screen:
            return im.resource_screen.absolute_url
        else:
            return None

    def item_enclosure_mime_type( self, item ):
        return 'image/jpeg'
