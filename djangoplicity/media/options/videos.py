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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ugettext_noop

from djangoplicity.archives.contrib import security
from djangoplicity.archives.contrib.browsers import NormalBrowser, \
    ViewAllBrowser, SerializationBrowser
from djangoplicity.archives.contrib.info import release_date, \
    admin_edit_for_site, admin_add_translation, published, featured, priority
from djangoplicity.archives.contrib.queries.defaults import UnpublishedQuery, \
    StagingQuery, EmbargoQuery, AdvancedSearchQuery
from djangoplicity.archives.contrib.serialization.serializers import JSONEmitter
from djangoplicity.archives.contrib.search.fields import VideoSizeSearchField, \
    PrioritySearchField, SeparatorField, IdSearchField, RelatedIdSearchField, \
    DateSinceSearchField, DateUntilSearchField, TextSearchField, \
    AVMSubjectNameSearchField, AVMTypeSearchField, \
    AVMSubjectCategorySearchField
from djangoplicity.archives.importer.import_actions import move_resources, \
    process_image_derivatives, remove_old_resources, rename_resource_ext, \
    compute_archive_checksums
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.views import SerializationDetailView
from djangoplicity.contentserver.import_actions import sync_content_server
from djangoplicity.media.forms import VideoImportForm, SubtitleImportForm
from djangoplicity.media.import_actions import enable_faststart, \
    embed_subtitles, fragment_mp4, upload_youtube_action, video_extras, \
    generate_thumbnail_action
from djangoplicity.media.info import related_releases, related_announcements, \
    duration, shadowbox_link, object_id, object_language, video_magnet_uri_link, \
    web_categories, frame_rate
from djangoplicity.media.models.videos import VideoProxy
from djangoplicity.media.queries import VideoWebCategoryPublicQuery, \
    VideoQuery
from djangoplicity.media.serializers import VideoSerializer
from djangoplicity.metadata.archives.info import subject_name, subject_category


class VideoOptions( ArchiveOptions ):
    description_template = 'archives/video/object_description.html'

    urlname_prefix = "videos"

    info = (
        (
            ugettext_noop(u'About the Video'), {
                'fields': (object_id, object_language, release_date,
                    related_releases, related_announcements, duration,
                    frame_rate)
            }
        ),
        (
            ugettext_noop(u'About the Object'), {
                'fields': (subject_name, subject_category, web_categories)
            }
        ),
    )

    admin = (
        (
            ugettext_noop(u'Admin'), {
                'links': (
                    admin_edit_for_site('admin_site', translation_proxy=VideoProxy),
                    admin_add_translation('admin_site', translation_proxy=VideoProxy),
                ),
                'fields': ( published, featured, 'release_date_owner', 'last_modified', 'created', priority ),
            }
        ),
    )

    downloads = (
        ( ugettext_noop('Fulldome'), {
            'resources': ( 'dome_8kmaster', 'dome_4kmaster', 'dome_2kmaster', 'dome_mov' ),
            'icons': {
                'dome_8kmaster': 'dome',
                'dome_4kmaster': 'dome',
                'dome_2kmaster': 'dome',
                'dome_mov': 'dome',
                }
        } ),
        ( ugettext_noop('Cylindrical'), {
            'resources': ( 'cylindrical_16kmaster', 'cylindrical_8kmaster', 'cylindrical_4kmaster' ),
            'icons': {
                'cylindrical_16kmaster': 'dome',
                'cylindrical_8kmaster': 'dome',
                'cylindrical_4kmaster': 'dome',
                }
        } ),
        (ugettext_noop('VR'), {
            'resources': ('vr_8k', 'vr_4k'),
            'icons': {
                'vr_8k': 'vr',
                'vr_4k': 'vr',
                }
        }),
        ( ugettext_noop('Fulldome Preview'), {
            'resources': ( 'dome_preview', ),
            'icons': {
                'dome_preview': 'dome',
                }
        } ),
        ( ugettext_noop('Ultra HD'), {
            'resources': ( 'ultra_hd', 'ultra_hd_h265', ),
            'icons': {
                'ultra_hd': 'movie',
                'ultra_hd_h265': 'movie',
                }
        } ),
        ( ugettext_noop('HD'), {
            'resources': ( shadowbox_link('hd_and_apple', 1280, 720, player='qt'), 'hd_1080p25_screen', 'ext_highres', 'ext_playback'),
            'icons': {
                'shadowbox_link': 'movie',
                'hd_1080p25_screen': 'movie',
                }
        } ),
        ( ugettext_noop( u'BitTorrent Download' ), {
            'resources': ( video_magnet_uri_link, ),
            'icons': { 'video_magnet_uri_link': 'magnet', }
        } ),
        ( ugettext_noop('Large'), {
            'resources': ( shadowbox_link('large_qt', 720, 405), ),
            'icons': { 'shadowbox_link': 'movie', }
        } ),
        ( ugettext_noop('Medium'), {
            'resources': ( shadowbox_link('medium_podcast', 640, 360), shadowbox_link('medium_mpeg1', 640, 360), shadowbox_link( 'medium_flash', 640, 360 ), ),
            'icons': {
                'shadowbox_link': 'movie',
                'medium_mpeg1': 'movie',
                'medium_podcast': 'movie',
                }
        } ),
        ( ugettext_noop(u'Small'), {
            'resources': ( shadowbox_link( 'small_flash', 320, 180 ), shadowbox_link( 'small_qt', 320, 180), ),
            'icons': {
                'shadowbox_link': 'movie',
                'small_qt': 'movie',
                }
        } ),
        ( ugettext_noop('For Broadcasters'), {
            'resources': ( 'ultra_hd_broadcast', 'hd_1080p25_broadcast', 'hd_broadcast_720p50', 'hd_broadcast_720p25', 'broadcast_sd', 'broadcast_sd_old', ),
            'icons': {
                'broadcast_sd': 'movie',
                'broadcast_sd_old': 'movie',
                'hd_broadcast_720p25': 'movie',
                'hd_broadcast_720p50': 'movie',
                'hd_1080p25_broadcast': 'movie',
                'ultra_hd_broadcast': 'movie',
                }
        } ),
        ( ugettext_noop('Script'), {
            'resources': ( 'script', ),
            'icons': {'script': 'doc' }
        } ),
        ( ugettext_noop('QuickTime VR'), {
            'resources': ( shadowbox_link('qtvr', 1280, 720, player='qt'), ),
            'icons': { 'shadowbox_link': 'movie' }
        } ),
        ( ugettext_noop(u'Legacy Videos'), {
            'resources': ( 'old_video', ),
            'icons': { 'old_video': 'movie' }
        } ),
    )

    detail_views = (
        { 'url_pattern': 'api/(?P<serializer>xml|json)/', 'view': SerializationDetailView( serializer=VideoSerializer, emitters=[JSONEmitter] ), 'urlname_suffix': 'serialization', },
    )

    search_fields = ( 'id', 'title', 'headline', 'description', 'subject_name__name', 'subject_name__alias', 'facility__name', 'credit', 'type' )
    archive_list_only_fields = (
        'id', 'title', 'credit', 'lang', 'source', 'content_server',
        'content_server_ready', 'youtube_video_id', 'use_youtube'
    )

    @staticmethod
    def feeds():
        from djangoplicity.media.feeds import VideoPodcastFeed
        feed_dict = {
            '': VideoPodcastFeed,
            'category': VideoPodcastFeed,
        }
        return feed_dict

    class Queries(object):
        default = VideoQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Videos") )
        category = VideoWebCategoryPublicQuery( relation_field='web_category', browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Video Archive: %(title)s"), category_type='Videos', feed_name="category", featured=[settings.VIDEOS_FEATURED_SUBJECT] if hasattr(settings, 'VIDEOS_FEATURED_SUBJECT') else [])
        search = AdvancedSearchQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Advanced Video Search"), searchable=False )
        staging = StagingQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Videos (staging)") )
        embargo = EmbargoQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Videos (embargoed)") )

    class AdvancedSearch (object):
        minimum_size = VideoSizeSearchField( label=_( "Minimum size" ) )
        ranking = PrioritySearchField( label=_( "Ranking" ) )
        additional_search_items = SeparatorField( label=_("Additional search terms") )
        id = IdSearchField( label=_('Image ID') )
        release_id = RelatedIdSearchField( label=_('Release ID'), model_field='release__id' )
        published_since = DateSinceSearchField( label=_( "Published since" ), model_field='release_date' )
        published_until = DateUntilSearchField( label=_( "Published until" ), model_field='release_date' )
        title = TextSearchField( label=_( "Title" ), model_field='title' )
        subject_name = AVMSubjectNameSearchField( label=_( "Subject name" ) )
        description = TextSearchField( label=_( "Description" ), model_field='description' )
        credit = TextSearchField( label=_( "Credit" ), model_field='credit' )
        type = AVMTypeSearchField( label=_( "Type" ), )
        category = AVMSubjectCategorySearchField( label=_( "Category" ), )

        class Meta:
            verbose_name = ugettext_noop("Advanced Video Search")

    class Browsers(object):
        normal = NormalBrowser( paginate_by=50 )
        viewall = ViewAllBrowser( paginate_by=100 )
        json = SerializationBrowser( serializer=VideoSerializer, emitter=JSONEmitter, paginate_by=100, display=False, verbose_name=ugettext_noop( "JSON" ) )

    class ResourceProtection( object ):
        unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
        staging = ( StagingQuery, security.STAGING_PERMS )
        embargo = ( EmbargoQuery, security.EMBARGO )

    class Import( object ):
        form = VideoImportForm
        metadata = 'original'
        uploadable = True
        scan_directories = [
            # Image
            ( 'original', ( '.jpg', '.jpeg', '.tif', '.png', ) ),
            # Dome
            ( 'dome_8kmaster', ( '.avi', '.zip', ) ),
            ( 'dome_4kmaster', ( '.avi', '.zip', ) ),
            ( 'dome_2kmaster', ( '.avi', '.zip', ) ),
            ('dome_2kplayback', ('.mp4',)),
            ('dome_4kplayback', ('.mp4',)),
            ( 'dome_mov', ( '.mov', '.mp4' ) ),
            ( 'vr_8k', ( '.mp4', ) ),
            ( 'vr_8k', ( '.mp4', ) ),
            ( 'dome_preview', ( '.mp4', ) ),
            # Cylindrical
            ( 'cylindrical_preview', ( '.mp4', ) ),
            ( 'cylindrical_4kmaster', ( '.zip', ) ),
            ( 'cylindrical_8kmaster', ( '.zip', ) ),
            ( 'cylindrical_16kmaster', ( '.zip', ) ),
            # Ultra HD
            ( 'ultra_hd_broadcast', ( '.avi', ) ),
            ( 'ultra_hd_h265', ( '.mkv', '.mp4' ) ),
            ( 'ultra_hd', ( '.mp4', ) ),
            # HD
            ( 'hd_and_apple', ( '.mp4', '.m4v' ) ),
            ( 'hd_1080p25_screen', ( '.mp4' ) ),
            # Broadcast
            ( 'broadcast_sd', ( '.avi', '.mxf', '.mov', '.mp4' ) ),
            ( 'hd_broadcast_720p25', ( '.mxf', '.m2t', '.mov' ) ),
            ( 'hd_broadcast_720p50', ( '.mxf', '.m2t', '.mov' ) ),
            ( 'hd_1080p25_broadcast', ( '.avi', '.mxf' ) ),
            # Large
            ( 'large_qt', ( '.mov', ) ),
            # Medium
            ( 'medium_flash', ( '.flv', ) ),
            ( 'medium_mpeg1', ( '.mpg', ) ),
            ( 'medium_podcast', ( '.m4v', '.mp4') ),
            # Small
            ( 'small_flash', ( '.flv', ) ),
            ( 'small_qt', ( '.mov', ) ),
            # Other
            ( 'ext_highres', ('.m4v', '.flv', '.mov', '.avi', '.mpeg', '.mp4', '.mpg') ),
            ( 'ext_playback', ('.m4v', '.flv', '.mov', '.avi', '.mpeg', '.mp4', '.mpg') ),
        ]
        actions = [
            remove_old_resources( [
                'broadcast',
                'broadcast_sd_old',
                'h264',
                'hd720p_broadcast',
                'hd720p_screen',
                'hd1080p_broadcast',
                'hd1080p_screen',
                'mov_medium',
                'mov_small',
                'mpg_medium',
                'mpg_small',
                'vodcast',
                'dome',
                'broadcast_sd_part1',
                'broadcast_sd_part2',
                'broadcast_sd_part3',
                'broadcast_sd_part4',
                'broadcast_sd_part5',
                'broadcast_sd_part6',
                'broadcast_sd_part7',
                'broadcast_sd_part8',
                'broadcast_sd_part9',
                'broadcast_sd_part10',
                'hd_broadcast_720p25_part1',
                'hd_broadcast_720p25_part2',
                'hd_broadcast_720p25_part3',
                'hd_broadcast_720p25_part4',
                'hd_broadcast_720p25_part5',
                'hd_broadcast_720p25_part6',
                'hd_broadcast_720p25_part7',
                'hd_broadcast_720p25_part8',
                'hd_broadcast_720p25_part9',
                'hd_broadcast_720p25_part10',
                'hd_broadcast_720p50_part1',
                'hd_broadcast_720p50_part2',
                'hd_broadcast_720p50_part3',
                'hd_broadcast_720p50_part4',
                'hd_broadcast_720p50_part5',
                'hd_broadcast_720p50_part6',
                'hd_broadcast_720p50_part7',
                'hd_broadcast_720p50_part8',
                'hd_broadcast_720p50_part9',
                'hd_broadcast_720p50_part10',
            ] + getattr( settings, 'VIDEOS_FORMATS_REMOVE', [] ) ),
            move_resources,
            rename_resource_ext( 'hd_and_apple', 'mp4', 'm4v' ),
            enable_faststart( 'hd_and_apple', 'large_qt' ),
            fragment_mp4('hd_1080p25_screen'),
            embed_subtitles( getattr( settings, 'VIDEOS_SUBTITLES_FORMATS', [] ) ),
            video_extras(),
            generate_thumbnail_action(),
            process_image_derivatives(),
            compute_archive_checksums(),
            sync_content_server(extra_formats=['videoframe']),
            upload_youtube_action()
        ]

    @staticmethod
    def queryset( request, model ):
        """
        Query set for detail view. Make sure we select related releases right away,
        as we need the later on.
        """
        return model._default_manager.all()

    @staticmethod
    def handle_import( obj, id=None, data=None, form_values=None ):
        """
        Create a video when importing an Video file.
        """
        if data is None:
            data = {}
        if form_values is None:
            form_values = {}

        from djangoplicity.archives.importer.utils import handle_import
        obj = handle_import( obj, id=id, data=data, form_values=form_values, save=True )

        if 'credit' in form_values:
            obj.credit = form_values['credit']

        # Once all videos have been re-encoded and imported, the next two lines can be removed (eso, spacetelescope, iau).
        from djangoplicity.metadata.models import TaggingStatus
        ts, _ = TaggingStatus.objects.get_or_create( slug='video_imported', name='Video imported' )
        obj.tagging_status.add( ts )

        obj.save()
        return obj


class VideoSubtitleOptions (ArchiveOptions):
    urlname_prefix = "videosubtitles"

    @staticmethod
    def find_importables( archive_import_root, archive_model, archive_options, exclude_id=None ):
        from djangoplicity.archives.importer.utils import find_importables
        from djangoplicity.media.models import Video

        res, invalid = find_importables( archive_import_root, archive_model, archive_options, exclude_id=None )
        newdict = {}

        for k, entry in res.iteritems():

            try:
                vidid = k[:-2]
                lang = k[-2:]
                vid = Video.objects.get(id=vidid)

                entry['video'] = vid
                entry['lang'] = lang

                newdict[k] = entry

            except Video.DoesNotExist:
                pass

        return (newdict, invalid)

    class Import( object ):
        uploadable = True
        form = SubtitleImportForm
        scan_directories = [
            ( 'srt', ( '.srt', ) ),
        ]
        actions = [
            move_resources,
        ]


class VideoAudioTrackOptions (ArchiveOptions):
    urlname_prefix = "videoaudiotracks"

    @staticmethod
    def find_importables( archive_import_root, archive_model, archive_options, exclude_id=None ):
        from djangoplicity.archives.importer.utils import find_importables
        from djangoplicity.media.models import Video

        res, invalid = find_importables( archive_import_root, archive_model, archive_options, exclude_id=None )
        newdict = {}

        for k, entry in res.iteritems():

            try:
                vidid = k[:-2]
                lang = k[-2:]
                vid = Video.objects.get(id=vidid)

                entry['video'] = vid
                entry['lang'] = lang

                newdict[k] = entry

            except Video.DoesNotExist:
                pass

        return (newdict, invalid)


class VideoBroadcastAudioTrackOptions (ArchiveOptions):
    urlname_prefix = "videobroadcastaudiotracks"

    @staticmethod
    def find_importables( archive_import_root, archive_model, archive_options, exclude_id=None ):
        from djangoplicity.archives.importer.utils import find_importables
        from djangoplicity.media.models import Video

        res, invalid = find_importables( archive_import_root, archive_model, archive_options, exclude_id=None )
        newdict = {}

        for k, entry in res.iteritems():

            try:
                vidid = k[:-2]
                lang = k[-2:]
                vid = Video.objects.get(id=vidid)

                entry['video'] = vid
                entry['lang'] = lang

                newdict[k] = entry

            except Video.DoesNotExist:
                pass

        return (newdict, invalid)
