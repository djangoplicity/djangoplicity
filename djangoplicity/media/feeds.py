# -*- coding: utf-8 -*-
#
# djangoplicity-media
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#   * Neither the name of the European Southern Observatory nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
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

from django.contrib.sites.models import Site
from django.db.models import Q
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils.html import strip_tags
from djangoplicity.archives.feeds import DjangoplicityArchiveFeed
from djangoplicity.feeds import conf as feedsconf
from djangoplicity.feeds.feeds import DjangoplicityFeedGen
from djangoplicity.media.models import Image, Video, PictureOfTheWeek
from djangoplicity.media.options import ImageOptions, VideoOptions, \
    PictureOfTheWeekOptions
from djangoplicity.utils.datetimes import timestring_to_seconds


class VideoFeed( DjangoplicityArchiveFeed ):
    """
    Implementation for Video Feeds. See Meta class definition for settings.


    # extract_items
    >> videoFeed = VideoFeed()
    >> VideoFeed.items()

    """
    title = feedsconf.get('VideoPodcastFeedSettings', 'title')
    link = feedsconf.get('VideoPodcastFeedSettings', 'link')
    description = feedsconf.get('VideoPodcastFeedSettings', 'description')
    title_template = 'feeds/video_title.html'

    class Meta(DjangoplicityArchiveFeed.Meta):
        model = Video
        options = VideoOptions
        latest_fieldname = Video.Archive.Meta.release_date_fieldname
        enclosure_resources = feedsconf.get('VideoPodcastFeedSettings', 'enclosure_resources')

        enclosure_mimetype = 'video/x-m4v'
        default_query = VideoOptions.Queries.default
        category_query = VideoOptions.Queries.category
        items_to_display = 25

        external_feed_url = None


class ImageFeed (DjangoplicityArchiveFeed):
    title = feedsconf.get('ImageFeedSettings', 'title', 'Images')
    link = feedsconf.get('ImageFeedSettings', 'link', '/')
    description = feedsconf.get('ImageFeedSettings', 'description', 'Images Feed')

    class Meta(DjangoplicityArchiveFeed.Meta):
        model = Image
        options = ImageOptions
        latest_fieldname = Image.Archive.Meta.release_date_fieldname
        enclosure_resources = {
            '': 'resource_screen',
            'screen': 'resource_screen',
        }
        default_query = ImageOptions.Queries.default
        category_query = ImageOptions.Queries.category
        extra_query = ImageOptions.Queries.top100
        external_feed_url = None


class VAMPFeed (DjangoplicityArchiveFeed):
    feed_type = Rss201rev2Feed
    title = "AstroPix Synchronization Feed"
    link = "/"
    title_template = None
    description_template = None

    class Meta(DjangoplicityArchiveFeed.Meta):
        model = Image
        options = ImageOptions
        latest_fieldname = 'metadata_date'
        default_query = ImageOptions.Queries.default
        category_query = None
        items_to_display = None  # will show all.
        external_feed_url = None

        cache = 5 * 60  # 5 minutes

    def item_description(self, item):
        '''
        By default item_decription returns force_text(item), and we don't
        want to use an empty description template as it will call the context
        processors for each item, so instead we just return None here
        '''
        return ''

    def item_title(self, item):
        '''
        As for item_description we bypass the template to make it more efficient
        '''
        return item.title

    def item_link(self, item):
        if item.resource_original:
            return item.resource_original.url
        else:
            return super(VAMPFeed, self).item_link(item)

    def items( self, obj ):
        """
        Returns the feed's items based on the obj returned by get_object
        """
        qs, dummy = self.Meta.default_query.queryset( self.Meta.model, self.Meta.options, None )
        qs = qs.filter( published=True, type='Observation' )
        qs = qs.filter( Q( tagging_status__slug='obs' ) | Q( tagging_status__slug='coords' ) )
        qs = qs.order_by( '-last_modified' ).distinct()
        return list( qs )

    def item_guid( self, obj ):
        """
        Override the default guid generation. Astropix (by Spitzer) does not
        handle guids like::

            <guid>https://www.eso.org/public/images/eso1152a/</guid>

        They must look like this::

            <guid isPermaLink="false">eso1152a</guid>
        """
        return obj.id


class Top100Feed(ImageFeed):
    title = feedsconf.get('Top100FeedSettings', 'title', 'Top 100 Images')
    link = feedsconf.get('Top100FeedSettings', 'link', '/')
    description = feedsconf.get('Top100FeedSettings', 'description', 'Top 100 Feed')

    class Meta(DjangoplicityArchiveFeed.Meta):
        model = Image
        options = ImageOptions
        latest_fieldname = Image.Archive.Meta.release_date_fieldname
        enclosure_resources = {
            '': 'resource_screen',
            'screen': 'resource_screen',
        }
        default_query = ImageOptions.Queries.top100
        category_query = None
        items_to_display = 100
        external_feed_url = None

    def items( self, obj ):
        """
        Returns the feed's items based on the obj returned by get_object
        """
        qs, dummy = self.Meta.default_query.queryset(self.Meta.model, self.Meta.options, None, stringparam=self.category)
        return qs[:self.Meta.items_to_display]


class PictureOfTheWeekFeed( DjangoplicityArchiveFeed ):
    title = feedsconf.get( 'PictureOfTheWeekFeedSettings', 'title', 'Picture of The Week' )
    link = feedsconf.get( 'PictureOfTheWeekFeedSettings', 'link', '/' )
    description = feedsconf.get( 'PictureOfTheWeekFeedSettings', 'description', 'Picture of The Week Feed' )

    title_template = 'feeds/potw_title.html'
    description_template = 'feeds/potw_description.html'

    class Meta(DjangoplicityArchiveFeed.Meta):
        model = PictureOfTheWeek
        options = PictureOfTheWeekOptions
        latest_fieldname = PictureOfTheWeek.Archive.Meta.release_date_fieldname
        enclosure_resources = { '': 'resource_hd_and_apple'}
        enclosure_mimetype = 'video/x-m4v'
        default_query = PictureOfTheWeekOptions.Queries.default
        category_query = None
        items_to_display = 25
        external_feed_url = feedsconf.get( 'PictureOfTheWeekFeedSettings', 'external_feed_url', None )

    def item_title(self, item):
        if item.image:
            return item.image.title
        elif item.video:
            return item.video.title
        else:
            return None

    def item_pubdate(self, item):
        """
        Takes an news item, as returned by items(), and returns the news'
        release date.
        """
        return item.release_date

    def item_enclosure_url(self, item):
        if item.image:
            im = item.image
            if im.resource_screen:
                return im.resource_screen.absolute_url
            else:
                return None
        if item.comparison:
            im = item.comparison
            if im.resource_screen:
                return "https://%s%s" % (Site.objects.get_current().domain, im.resource_screen.url)
            else:
                return None
        elif item.video:
            vi = item.video
            #TODO: include in settings
            if vi.resource_hd_and_apple:
                return "https://%s%s" % (Site.objects.get_current().domain, vi.resource_hd_and_apple.url)
            elif vi.resource_hd720p_screen:
                return "https://%s%s" % (Site.objects.get_current().domain, vi.resource_hd720p_screen.url)

            else:
                return None

    def item_enclosure_length( self, item):
        if item.image:
            im = item.image
            if im.resource_screen:
                return int(im.resource_screen.size)
            else:
                return None
        elif item.video:
            vi = item.video
            if vi.resource_hd_and_apple:
                return int(vi.resource_hd_and_apple.size)
            else:
                return None

    def item_enclosure_mime_type( self, item ):
        if item.image:
            return 'image/jpeg'
        elif item.video:
            return 'video/x-m4v'


class VideoPodcastFeedGen (DjangoplicityFeedGen):
    """
    Used together with VideoPodcastFeed, in order to support the rendering
    of the extra elements provided.
    """

    def rss_attributes(self):
        """
        dict with attributes needed for the RSS initial definitions such as namespaces,
        versions etc.
        """
        return {
            u"version": self._version,
            u"xmlns:itunes": u'http://www.itunes.com/dtds/podcast-1.0.dtd',
            u"xmlns:media": u'http://search.yahoo.com/mrss/',
            u"xmlns:amp": u'http://www.adobe.com/amp/1.0',
            u"xmlns:atom": u'http://www.w3.org/2005/Atom',
            u"xmlns:feedburner": u'http://rssnamespace.org/feedburner/ext/1.0',
        }

    def add_item_elements(self, handler, item):
        """
        checks the item dictionary for podcast-specific keywords and adds them to
        the feed <item /> entry. These keywords can be defined in the item_extra_kwargs
        on the Feed class
        """

        super(DjangoplicityFeedGen, self).add_item_elements(handler, item)

        if item.get('itunes:author', None):
            handler.addQuickElement(u'itunes:author', item['itunes:author'])

        if item.get('itunes:subtitle', None):
            handler.addQuickElement(u'itunes:subtitle', item['itunes:subtitle'])

        if item.get('itunes:summary', None):
            handler.addQuickElement(u'itunes:summary', item['itunes:summary'])

        if item.get('itunes:explicit', None):
            handler.addQuickElement(u'itunes:explicit', item['itunes:explicit'])

        if item.get('itunes:keywords', None):
            handler.addQuickElement(u'itunes:keywords', item['itunes:keywords'])

        if item.get('itunes:duration', None):
            handler.addQuickElement(u'itunes:duration', item['itunes:duration'])

        if item.get('media:thumbnail', None):
            handler.addQuickElement(u'media:thumbnail', '', item['media:thumbnail'] )  # Dictionary


class VideoPodcastFeed( VideoFeed ):
    """
    Extends the Feed class VideoFeed to provide for podcast-specific
    elements e.g. those used by iTunes and Adobe Media Player
    """
    title = feedsconf.get('VideoPodcastFeedSettings', 'title', 'Video Podcast Feed')
    link = feedsconf.get('VideoPodcastFeedSettings', 'link', '/')
    description = feedsconf.get('VideoPodcastFeedSettings', 'description', 'Video Podcast Feed')

    override_guids = feedsconf.get('VideoPodcastFeedSettings', 'override_guids', {})
    override_guids_format = feedsconf.get('VideoPodcastFeedSettings', 'override_guids_format', {})

    feed_type = VideoPodcastFeedGen
    header_template = None
    footer_template = None

    description_template = 'feeds/video_description.html'

    def item_extra_kwargs(self, item):
        """
        Returns a dict with extra keywords needed for each item in the RSS feed
        """
        if self.feed_type != VideoPodcastFeedGen:
            return {}

        dict = {
                'itunes:author': item.creator,
                'itunes:subtitle': strip_tags(item.headline)[:250] if item.headline else '',
                'itunes:summary': strip_tags(item.headline) if item.headline else '',
                'itunes:explicit': 'No',
                'itunes:keywords': item.keywords if hasattr(item, 'keywords') else '',
                'media:thumbnail': { u"url": "https://%s%s" % (Site.objects.get_current().domain, item.resource_thumb.url) if item.resource_thumb else '' },
                }

        # parse H:m:s:ff format to seconds
        dict['itunes:duration'] = ''
        if item.file_duration:
            try:
                dict['itunes:duration'] = str(timestring_to_seconds(item.file_duration))
            except ValueError:
                pass

        return dict

    def feed_extra_kwargs(self, obj):
        """
        Returns a dict with extra keywords needed for the root of the RSS feed
        """

        dict = {}

        if hasattr(self, 'header_template'):
            dict['header_template'] = self.header_template

        if hasattr(self, 'footer_template'):
            dict['footer_template'] = self.footer_template

        if hasattr(self, 'format'):
            dict['format'] = self.format

        return dict
