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

from future import standard_library
standard_library.install_aliases()
from builtins import str
import datetime
import logging
import html.parser

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import models, transaction
from django.db.models import signals, Q
from django.template.loader import get_template, render_to_string
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from djangoplicity.archives import fields as archive_fields
from djangoplicity.archives.base import ArchiveModel, post_rename
from djangoplicity.archives.contrib import types
from djangoplicity.archives.resources import ResourceManager, ImageResourceManager
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.archives.utils import release_date_change_check, \
    wait_for_resource
from djangoplicity.contentserver.models import ContentDeliveryModel
from djangoplicity.media.consts import SUBTITLE_LANGUAGES, DEFAULT_CREDIT
from djangoplicity.media.consts import DEFAULT_CREATOR_FUNC, DEFAULT_CREATOR_URL_FUNC, \
    DEFAULT_CREDIT_FUNC, DEFAULT_CONTACT_ADDRESS_FUNC, DEFAULT_CONTACT_CITY_FUNC, \
    DEFAULT_CONTACT_COUNTRY_FUNC, DEFAULT_CONTACT_POSTAL_CODE_FUNC, \
    DEFAULT_CONTACT_STATE_PROVINCE_FUNC, DEFAULT_PUBLISHER_FUNC, DEFAULT_PUBLISHER_ID_FUNC, \
    DEFAULT_RIGHTS_FUNC, SPLIT_AUDIO_TYPES
from djangoplicity.media.tasks import video_extras, update_youtube_caption, \
    update_youtube_snippet
from djangoplicity.media.youtube import youtube_configured, \
    youtube_captions_insert, youtube_captions_list, youtube_captions_update, \
    youtube_playlistitems_insert, youtube_playlistitems_list, \
    youtube_playlists_list, youtube_videos_list, youtube_videos_update, \
    YouTubeInvalidPrivacyStatus, YouTubeUnknownID
from djangoplicity.metadata.archives import fields as metadatafields
from djangoplicity.metadata.models import Contact, TaggingStatus, Category
from djangoplicity.metadata.translation import fields as metadatafields_trans
from djangoplicity.translation.models import TranslationModel, \
    translation_reverse
from djangoplicity.translation.fields import TranslationForeignKey, \
    TranslationManyToManyField
from djangoplicity.utils.history import add_admin_history


class Video( ArchiveModel, TranslationModel, ContentDeliveryModel ):
    """
    Video archive model

    Though no AVM standard is defined for vidoes, this model tries to
    stay as close to the Image AVM standard as possible.
    """
    def __init__( self, *args, **kwargs ):
        super( Video, self ).__init__( *args, **kwargs )
        if not self.credit:
            self.credit = DEFAULT_CREDIT

    UPLOAD_FORMATS = (
        'vr_8k', 'vr_4k', 'cylindrical_preview', 'ultra_hd',
        'hd_1080p25_screen', 'hd_1080_screen', 'dome_preview', 'hd_broadcast_720p25',
        'hd_and_apple', 'medium_podcast', 'ext_highres', 'ext_playback',
        'old_video'
    )

    priority = archive_fields.PriorityField( help_text=_( u'Assessment of the quality of the image (100 highest, 0 lowest). Higher priority images are ranked higher in search results than lower priority images.' ) )

    featured = models.BooleanField(default=False)

    # ========================================================================
    # Creator Metadata
    # ========================================================================
    creator = metadatafields.AVMCreatorField( default=DEFAULT_CREATOR_FUNC )
    creator_url = metadatafields.AVMCreatorURLField( default=DEFAULT_CREATOR_URL_FUNC )
    contact_address = metadatafields.AVMContactAddressField( default=DEFAULT_CONTACT_ADDRESS_FUNC )
    contact_city = metadatafields.AVMContactCityField( default=DEFAULT_CONTACT_CITY_FUNC )
    contact_state_province = metadatafields.AVMContactStateProvinceField( default=DEFAULT_CONTACT_STATE_PROVINCE_FUNC )
    contact_postal_code = metadatafields.AVMContactPostalCodeField( default=DEFAULT_CONTACT_POSTAL_CODE_FUNC )
    contact_country = metadatafields.AVMContactCountryField( default=DEFAULT_CONTACT_COUNTRY_FUNC )
    rights = metadatafields.AVMRightsField( default=DEFAULT_RIGHTS_FUNC )

    # ========================================================================
    # Content Metadata
    # ========================================================================
    def _get_reference_url( self ):
        return 'https://%s%s' % (get_current_site(None).domain, self.get_absolute_url())

    title = metadatafields.AVMTitleField()
    headline = metadatafields.AVMHeadlineField()
    description = metadatafields.AVMDescriptionField()
    web_category = models.ManyToManyField(Category, limit_choices_to=Q(type__name='Videos'), blank=True)
    subject_category = metadatafields_trans.TranslationAVMSubjectCategoryField( )
    subject_name = metadatafields_trans.TranslationAVMSubjectNameField()
    reference_url = property( _get_reference_url )
    credit = metadatafields.AVMCreditField( default=DEFAULT_CREDIT_FUNC )
    date = None  # TODO: Date = created or date/time press release was published.
    id = metadatafields.AVMIdField( help_text=_( u'Id of video - used in the URL for the image as well as the filename for the different formats.' ) )
    type = metadatafields.AVMTypeField()

    # ========================================================================
    # Observation Metadata
    # ========================================================================
    facility = metadatafields_trans.TranslationFacilityManyToManyField()

    # ========================================================================
    # Publisher Metadata
    # ========================================================================
    def _get_metadata_date(self):
        return self.last_modified

    def resource_id( self, resource='original' ):
        """ Example: sig05-010_jpg_sm """
        if resource == 'original':
            return self.id
        else:
            return "%s_%s" % ( self.id, resource )

    def resource_url(self, resource='original' ):
        if resource == 'original':
            return self.resource_original.url
        else:
            attr = "resource_" % resource
            if hasattr(self, attr):
                return getattr(self, attr).url
            else:
                return None

    publisher = metadatafields.AVMPublisherField( default=DEFAULT_PUBLISHER_FUNC )
    publisher_id = metadatafields.AVMPublisherIdField( default=DEFAULT_PUBLISHER_ID_FUNC )
    related_resources = None  # TODO: Implement Publisheer.RelatedResources
    metadata_date = property( _get_metadata_date )
    metadata_version = "dev"  # TODO: This is no offical standard yet.

    # ========================================================================
    # File Metadata
    # ========================================================================
    def _get_file_dimension(self):
        return [self.width, self.height]

    width = metadatafields.AVMFileDimensionWidth()
    height = metadatafields.AVMFileDimensionHeight()

    file_dimension = property( _get_file_dimension )
    file_duration = metadatafields.AVMFileDuration()
    file_aspect_ratio = metadatafields.AVMFileAspectRatio()
    file_size = metadatafields.AVMFileSize()
    file_bit_depth = None  # TODO: Implement File.BitDepth

    frame_rate = models.PositiveIntegerField(default=25)

    # ========================================================================
    # Resource Display Related Fields
    # ========================================================================
    audio_surround_format = metadatafields.AVMAudioSurroundFormat()

    # ========================================================================
    # Additional Fields
    # ========================================================================
    old_ids = models.CharField( max_length=255 )
    # Field to store the legacy id.

    magnet_uri = models.CharField( max_length=255, blank=True )
    # Magnet link for the bittorrent version of the original format

    youtube_video_id = models.CharField(max_length=11, blank=True, null=True, verbose_name=_('YouTube VideoID'))
    use_youtube = models.BooleanField(default=False, verbose_name=_('Use YouTube player'))

    # ========================================================================
    # Internal status field
    # ========================================================================
    tagging_status = TranslationManyToManyField( TaggingStatus, blank=True, only_sources=True )
    # Status field to indicate the status of the tagged image.

    def get_absolute_url( self ):
        return translation_reverse( 'videos_detail', args=[str( self.id if self.is_source() else self.source.id )], lang=self.lang )

    def rename(self, new_pk):
        """
        Used primarily for sending a notification email about renamed videos.
        """
        try:
            if self.is_source():
                # Try to see if we have a workflow that we need to run.
                (name, func) = settings.ARCHIVE_WORKFLOWS['media.video.rename']
                # Try to import the module and run the function
                module = __import__(name, globals(), locals(), [func, ], -1)
                getattr(module, func)(pk=self.pk, new_pk=new_pk)
        except (AttributeError, KeyError):
            pass

        result = super(Video, self).rename(new_pk)

        transaction.on_commit(
            lambda: update_youtube_snippet.delay(new_pk)
        )

        return result

    def __unicode__( self ):
        return self.title

    class Meta:
        ordering = ['-priority', '-release_date']
        app_label = 'media'
        permissions = [
            ( "view_only_non_default", "Can view only non default language" ),
            ( "view_released_videos_only", "Can view only released videos" ),
        ]

    class Translation:
        fields = ['title', 'headline', 'description', ]
        excludes = ['published', 'last_modified', 'created', ]

    class Archive:
        # Image formats
        original = ImageResourceManager( type=types.OriginalImageType )
        thumb = ImageResourceManager( derived='original', type=types.ThumbnailJpegType )
        news = ImageResourceManager( derived='original', type=types.NewsJpegType )
        newsmini = ImageResourceManager( derived='original', type=types.NewsMiniJpegType )
        videoframe = ImageResourceManager( derived='original', type=types.VideoFrameType )
        newsfeature = ImageResourceManager( derived='original', type=types.NewsFeatureType )
        potwmedium = ImageResourceManager( derived='original', type=types.POTWMediumThumbnailJpegType )
        thumb300y = ImageResourceManager( derived='original', type=types.Thumb300yType )
        thumb350x = ImageResourceManager( derived='original', type=types.Thumb350xType )

        script = ResourceManager( type=types.PDFType, verbose_name=_(u'Script') )

        # Small formats
        small_flash = ResourceManager( type=types.FlvType, verbose_name=_(u"Small Flash") )
        small_qt = ResourceManager( type=types.MovType, verbose_name=_(u"Small QT") )

        # Medium formats
        medium_podcast = ResourceManager( type=types.MediumPodcastType, verbose_name=_(u"Video Podcast") )  # video_podcast
        medium_mpeg1 = ResourceManager( type=types.MpegType, verbose_name=_(u"Medium MPEG-1") )  # medium_mpeg-1
        medium_flash = ResourceManager( type=types.FlvType, verbose_name=_(u"Medium Flash") )  # medium_flash

        # Large formats
        large_qt = ResourceManager( type=types.MovType, verbose_name=_(u"Large QT"), )  # large_qt
        broadcast_sd = ResourceManager( type=types.BroadcastSDType, verbose_name=_(u"Broadcast SD") )  # broadcast_sd

        # HD formats
        hd_and_apple = ResourceManager( type=types.HDAndAppleType, verbose_name=_(u"HD & Apple TV Preview") )  # hd_apple_tv
        hd_broadcast_720p50 = ResourceManager( type=types.BroadcastType, verbose_name=_(u"HD Broadcast 720p/50") )  # hd720p50_brodcast
        hd_1080p25_screen = ResourceManager( type=types.FullHDPreview1080p, verbose_name=_(u"Full HD Preview 1080p") )  # hd1080p25_screen
        hd_1080p25_broadcast = ResourceManager( type=types.BroadcastType, verbose_name=_(u"Full HD Broadcast 1080p") )  # hd1080p25_brodcast
        # FULL HD 29,97 FPS
        hd_1080_screen = ResourceManager( type=types.FullHDPreview1080p, verbose_name=_(u"Full HD Preview 1080p") )  # hd1080_screen
        hd_1080_broadcast = ResourceManager( type=types.BroadcastType, verbose_name=_(u"Full HD Broadcast 1080p") )  # hd1080_brodcast

        # Ultra HD (4k/2160p)
        ultra_hd = ResourceManager( type=types.UltraHDType, verbose_name=_(u"4K Ultra HD Preview H.264") )
        ultra_hd_h265 = ResourceManager( type=types.UltraHDH265Type, verbose_name=_(u"4K Ultra HD Preview H.265") )
        ultra_hd_broadcast = ResourceManager( type=types.UltraHDBroadcastType, verbose_name=_(u"4K Ultra HD Broadcast") )

        # Dome
        dome_8kmaster = ResourceManager( type=types.Dome8kMasterType, verbose_name=_(u"Fulldome 8k Master") )
        dome_4kmaster = ResourceManager( type=types.Dome4kMasterType, verbose_name=_(u"Fulldome 4k Master") )
        dome_2kmaster = ResourceManager( type=types.Dome2kMasterType, verbose_name=_(u"Fulldome 2k Master") )
        dome_mov = ResourceManager( type=types.DomeMovType, verbose_name=_(u"Fulldome 1.5k mov") )
        dome_preview = ResourceManager( type=types.DomePreviewType, verbose_name=_(u"Fulldome Preview") )

        # Cylindrical
        cylindrical_preview = ResourceManager(type=types.CylindricalPreviewType, verbose_name=_(u'Cylindrical VR Preview'))
        cylindrical_4kmaster = ResourceManager(type=types.Cylindrical4kMasterType, verbose_name=_(u'4k Cylindrical VR Master'))
        cylindrical_8kmaster = ResourceManager(type=types.Cylindrical8kMasterType, verbose_name=_(u'8k Cylindrical VR Master'))
        cylindrical_16kmaster = ResourceManager(type=types.Cylindrical16kMasterType, verbose_name=_(u'16k Cylindrical VR Master'))

        # VR
        vr_8k = ResourceManager(type=types.VR8kType, verbose_name=_(u'8k VR'))
        vr_4k = ResourceManager(type=types.VR4kType, verbose_name=_(u'4k VR'))

        # Broadcast formats
        hd_broadcast_720p25 = ResourceManager( type=types.BroadcastType, verbose_name=_(u"HD Broadcast 720p/25") )  # hd720p25_brodcast

        # External formats (used to import misc video types in a single format
        ext_highres = ResourceManager(type=types.LegacyVideo, verbose_name=_(u'Highres'))
        ext_playback = ResourceManager(type=types.LegacyVideo, verbose_name=_(u'Playback'))

        # Quictime VR
        qtvr = ResourceManager( type=types.MovType, verbose_name=_(u"QuickTime VR") )

        # For legacy formats (gif anis etc)
        old_video = ResourceManager( type=types.LegacyVideo, verbose_name=_(u"Legacy Video") )

        class Meta:
            root = settings.VIDEOS_ARCHIVE_ROOT
            release_date = True
            embargo_date = True
            release_date_owner = True
            last_modified = True
            created = True
            published = True
            rename_pk = ( 'media_video', 'id' )
            rename_fks = (
                ( 'announcements_announcementvideo', 'archive_item_id' ),
                ( 'media_pictureoftheweek', 'video_id' ),
                ( 'media_videoaudiotrack', 'video_id' ),
                ( 'media_videobroadcastaudiotrack', 'video_id' ),
                ( 'media_videocontact', 'video_id' ),
                ( 'media_video_facility', 'video_id' ),
                ( 'media_video', 'source_id'),
                ( 'media_video_subject_category', 'video_id' ),
                ( 'media_video_subject_name', 'video_id' ),
                ( 'media_videosubtitle', 'video_id' ),
                ( 'media_video_tagging_status', 'video_id' ),
                ( 'media_video_web_category', 'video_id' ),
                ( 'media_videoscript', 'video_id' ),
                ( 'releases_releasevideo', 'archive_item_id' ),
            )
            sort_fields = ['last_modified', 'release_date', 'priority', 'file_size']
            clean_html_fields = ['description', 'credit']

    def save(self, *args, **kwargs ):
        """
        Overrides default save method to determine video resolution and duration
        """

        # Send an email notification when the video is published
        send_notification = False
        if self.published:
            try:
                orig = Video.objects.get(pk=self.pk)
                if not orig.published:
                    # The video already existed, and was not published so far
                    send_notification = True
            except Video.DoesNotExist:
                # The video is new, and was created published
                send_notification = True

        # If translations are activated we only send notifications when
        # the source if published
        if settings.USE_I18N and not self.is_source():
            send_notification = False

        # In some cases where 'created' was not set upon creation the save
        # will fail so we manually set it
        if not self.created:  # pylint: disable=E0203
            self.created = datetime.datetime.today()

        # Consume argument
        if 'run_tasks' in kwargs:
            run_tasks = kwargs['run_tasks']
            del kwargs['run_tasks']
        else:
            run_tasks = True

        super( Video, self ).save( *args, **kwargs )

        # Send the actual email notification
        if send_notification and hasattr(settings, 'VIDEO_RENAME_NOTIFY'):
            try:
                from django.contrib.sites.models import Site
                domain = Site.objects.get_current().domain
            except ImportError:
                domain = ''
            from_email = settings.DEFAULT_FROM_EMAIL
            subject = 'Video "%s" is now published' % self.pk
            html_body = render_to_string('archives/video_published_email.html', {'video': self, 'site_url': domain })
            text_body = strip_tags( html_body )

            # Send
            if subject and html_body and from_email:
                try:
                    msg = EmailMultiAlternatives( subject, text_body, from_email, settings.VIDEO_RENAME_NOTIFY )
                    msg.attach_alternative( html_body, 'text/html' )
                    msg.send()
                except Exception:
                    # Just ignore error if SMTP server is down.
                    pass

        # Run background tasks on video
        if run_tasks and self.is_source():
            video_extras.delay('media', 'Video', self.pk)

    def embargo_date_action(self):
        '''
        Called at the time defined by embargo_date
        '''
        super(Video, self).embargo_date_action()

        # If the video is featured and has the same embargo and release date
        # then we leave it for release_date_action
        if self.featured and self.release_date == self.embargo_date:
            return

        self.update_youtube_privacy('unlisted')
        add_admin_history(self, 'Setting YouTube video privacy to "unlisted" at embargo time')

    def release_date_action(self):
        '''
        Called at the time defined by release_date
        '''
        super(Video, self).release_date_action()

        if self.published and self.featured:
            if self.release_date > datetime.datetime.now():
                # The release date is in the future, which shouldn't happen
                # We mark the video as unlisted and send a notification
                send_mail('WARNING: Video ' + self.pk + ' should be marked as public by '
                    'release_date_action but release date is in the future!',
                    '', 'no-reply@eso.org', ['Gurvan.Bazin@eso.org'])
                self.update_youtube_privacy('unlisted')
                return

            self.update_youtube_privacy('public')
            self.update_youtube_playlists()
            add_admin_history(self, 'Setting YouTube video privacy to "public" at release time')

    def get_youtube_description(self):
        '''
        Returns a plain text version of headline, description and headline
        for use in e.g. YouTube
        '''
        template = get_template('videos/youtube_description.html')
        description = template.render({
            'video': self,
            'domain': get_current_site(None).domain,
        })

        description = html.parser.HTMLParser().unescape(description)

        # YouTube description are limited to 5000 characters, so we truncate
        # it a bit shorter
        if len(description) > 4900:
            description = description[:4900] + '...'

        return description

    def get_youtube_playlists(self):
        '''
        Returns a list of Youtube playlists which name match the video's
        web categories
        '''
        playlists = []
        web_categories = self.web_category.values_list('name', flat=True)

        for playlist in youtube_playlists_list()['items']:
            if playlist['snippet']['title'] in web_categories:
                playlists.append(playlist)

        return playlists

    def get_youtube_tags(self):
        '''
        Returns a list of text tags to be used in YouTube, based on web
        categories, subject categories and subject name
        '''
        try:
            # Make a copy of the default list
            tags = list(settings.YOUTUBE_DEFAULT_TAGS)
        except AttributeError:
            tags = []
        tags += self.web_category.values_list('name', flat=True)
        tags += self.subject_category.values_list('name', flat=True)
        tags += self.subject_name.values_list('name', flat=True)

        return list(set(tags))

    def get_youtube_title(self):
        '''
        Returns the title truncated to 100 characters
        '''
        if len(self.title) <= 100:
            return self.title
        else:
            return self.title[:97] + u'...'

    def update_youtube_privacy(self, privacy):
        '''
        Set the Youtube privacy: private, public or unlisted
        '''
        if not youtube_configured or not self.youtube_video_id:
            return

        if privacy not in ('private', 'public', 'unlisted'):
            raise YouTubeInvalidPrivacyStatus('Unkown privacy status "%s"' %
                    privacy)

        response = youtube_videos_list(
            id=self.youtube_video_id,
            part='snippet, status'
        )

        if not response['items']:
            raise YouTubeUnknownID('Unkown YouTube ID: "%s"' %
                    self.youtube_video_id)

        status = response['items'][0]['status']

        if status['privacyStatus'] == privacy:
            # Nothing to do
            return

        status['privacyStatus'] = privacy

        youtube_videos_update(
            part='status',
            body=dict(
                status=status,
                id=self.youtube_video_id
            )
        )

    def update_youtube_playlists(self):
        '''
        Set YouTube playlists based on the video's web category
        '''
        logger = logging.getLogger(__name__)

        for playlist in self.get_youtube_playlists():
            # Check if video is already in the playlist
            for video in youtube_playlistitems_list(playlist['id'])['items']:
                if video['snippet']['resourceId']['videoId'] ==  \
                        self.youtube_video_id:
                    # Video already exists
                    logger.info('Video "%s" (%s) already belong to playlist "%s"',
                        self.pk, self.youtube_video_id,
                            playlist['snippet']['title'])
                    break
            else:
                # Video is not in playlist
                youtube_playlistitems_insert(playlist['id'],
                    self.youtube_video_id)
                logger.info('Video "%s" (%s) added to playlist "%s"',
                    self.pk, self.youtube_video_id,
                        playlist['snippet']['title'])

    def update_youtube_snippet(self):
        '''
        Update the related Youtube video snippet
        '''
        if not youtube_configured or not self.youtube_video_id:
            return

        response = youtube_videos_list(
            id=self.youtube_video_id,
            part='snippet'
        )

        if not response['items']:
            raise YouTubeUnknownID('Unkown YouTube ID: "%s"' %
                    self.youtube_video_id)

        snippet = response['items'][0]['snippet']
        snippet['title'] = self.get_youtube_title()
        snippet['description'] = self.get_youtube_description()
        snippet['tags'] = self.get_youtube_tags()

        youtube_videos_update(
            part='snippet',
            body={
                'snippet': snippet,
                'id': self.youtube_video_id
            }
        )

    @classmethod
    def fields_changed_check_pre(cls, instance, raw, *args, **kwargs):
        '''
        Check if fields have changed and save them as instance attribute
        to be used in fields_changed_check_post (that way the instance will
        have been saved to the DB)
        '''
        if raw:
            return

        try:
            obj = cls.objects.get(pk=instance.pk)
        except cls.DoesNotExist:
            return

        fields = ('title', 'headline', 'description', 'credit')
        changed_fields = []

        for field in fields:
            if getattr(instance, field) != getattr(obj, field):
                changed_fields.append(field)

        if changed_fields:
            setattr(instance, '_changed_fields', changed_fields)

    @classmethod
    def fields_changed_check_post(cls, instance, raw, *args, **kwargs):
        if raw:
            return

        if hasattr(instance, '_changed_fields'):
            # At least one field has changed, update the Youtube snippet
            if instance.youtube_video_id:
                transaction.on_commit(
                    lambda: update_youtube_snippet.delay(instance.pk)
                )

            delattr(instance, '_changed_fields')

    def get_ordered_subtitles(self):
        '''
        Returns a list of subtitles ordered by the the language name instead
        of language code
        '''
        qs = self.videosubtitle_set.all()
        return sorted(qs, key=lambda s: s.get_lang_display())


class VideoSubtitle( ArchiveModel, models.Model ):
    """
    Model for storing subtitles for videos.
    """
    id = archive_fields.IdField()
    video = TranslationForeignKey( Video )
    lang = models.CharField( verbose_name=_( 'Language' ), max_length=7, choices=SUBTITLE_LANGUAGES, default=settings.LANGUAGE_CODE, db_index=True )

    def save( self, **kwargs ):
        """
        Override save() to always set id as video_id + lang

        # TODO: check video renaming
        """
        old_id = self.id
        self.id = self.video.id + self.lang

        if old_id != self.id:  # delete old
            try:
                old = VideoSubtitle.objects.get( id=old_id )
                old.delete()
            except VideoSubtitle.DoesNotExist:
                pass

        # In some cases where 'created' was not set upon creation the save
        # will fail so we manually set it
        if not self.created:  # pylint: disable=E0203
            self.created = datetime.datetime.today()

        super( VideoSubtitle, self ).save( **kwargs )

        transaction.on_commit(
            lambda: update_youtube_caption.delay(self.pk)
        )

    def __unicode__( self ):
        return dict( SUBTITLE_LANGUAGES ).get( self.lang, self.lang )

    def update_youtube_caption(self, logger=None):
        '''
        Upload the given subtitle to YouTube
        '''
        if logger is None:
            logger = logging.getLogger(__name__)

        if not youtube_configured or not self.video or not self.video.youtube_video_id:
            logger.warning('No video or YouTube ID for subtitle "%s"', self.pk)
            return

        response = youtube_videos_list(
            id=self.video.youtube_video_id,
            part='snippet'
        )

        if not response['items']:
            raise YouTubeUnknownID('Unkown YouTube ID: "%s"' %
                    self.youtube_video_id)

        snippet = dict(
            videoId=self.video.youtube_video_id,
            language=self.lang,
            name='',
            isDraft=False
        )

        # Check if caption already exists
        response = youtube_captions_list(
            part='snippet',
            video_id=self.video.youtube_video_id
        )

        # We use wait_for_resource in case the NFS is slow to synchronise
        # between the different servers
        srt = wait_for_resource(self, 'srt')

        for item in response['items']:
            if item['snippet']['language'] == self.lang:
                # Subtitle already exist, we update it
                youtube_captions_update(
                    part='snippet',
                    body=dict(
                        id=item['id'],
                        snippet=snippet
                    ),
                    media_body=srt.file.name
                )
                break
        else:
            # New subtitle, we insert it
            youtube_captions_insert(
                part='snippet',
                body=dict(
                    snippet=snippet
                ),
                media_body=srt.file.name
            )

    class Meta:
        verbose_name = _(u'Video Subtitle')
        app_label = 'media'

    class Archive:
        srt = ResourceManager( type=types.SubtitleType, verbose_name=_( u"Subtitle (srt)" ) )

        class Meta:
            root = settings.VIDEOS_ARCHIVE_ROOT
            release_date = False
            embargo_date = False
            last_modified = True
            created = True
            published = True


class VideoAudioTrack( ArchiveModel, models.Model ):
    """
    Model for storing Audio tracks for videos.
    """
    id = archive_fields.IdField()
    video = TranslationForeignKey( Video )
    lang = models.CharField( verbose_name=_( 'Language' ), max_length=7, choices=SUBTITLE_LANGUAGES, default=settings.LANGUAGE_CODE, db_index=True )

    def save( self, **kwargs ):
        """
        Override save() to always set id as video_id + '_' + lang

        # TODO: check video renaming
        """
        old_id = self.id
        self.id = self.video.id + '_' + self.lang

        if old_id != self.id:  # delete old
            try:
                old = VideoAudioTrack.objects.get( id=old_id )
                old.delete()
            except VideoAudioTrack.DoesNotExist:
                pass

        super( VideoAudioTrack, self ).save( **kwargs )

    def __unicode__( self ):
        return dict( SUBTITLE_LANGUAGES ).get( self.lang, self.lang )

    class Meta:
        verbose_name = _(u'Video Audio Track')
        app_label = 'media'

    class Archive:
        audio = ResourceManager( type=types.AudioTrackType, verbose_name=_( u"Audio Track" ) )

        class Meta:
            root = settings.VIDEOS_ARCHIVE_ROOT
            release_date = False
            embargo_date = False
            last_modified = True
            created = True
            published = True


class VideoBroadcastAudioTrack( ArchiveModel, models.Model ):
    """
    Model for storing Broadcast Audio tracks for videos.
    """
    id = archive_fields.IdField()
    video = TranslationForeignKey(Video)
    lang = models.CharField(verbose_name=_('Language'), max_length=7, choices=SUBTITLE_LANGUAGES, default=settings.LANGUAGE_CODE, db_index=True)
    type = models.CharField(verbose_name=_('Audio track type'), max_length=25, choices=SPLIT_AUDIO_TYPES)

    def save( self, **kwargs ):
        """
        Override save() to always set id as video_id + '_' + type + '_' + lang

        # TODO: check video renaming
        """
        old_id = self.id
        self.id = '%s_%s_%s' % (self.video.id, self.type, self.lang)

        if old_id != self.id:  # delete old
            try:
                old = VideoBroadcastAudioTrack.objects.get( id=old_id )
                old.delete()
            except VideoBroadcastAudioTrack.DoesNotExist:
                pass

        super( VideoBroadcastAudioTrack, self ).save( **kwargs )

    def __unicode__( self ):
        return '%s %s' % (self.get_type_display(), dict(SUBTITLE_LANGUAGES).get(self.lang, self.lang))

    class Meta:
        verbose_name = _(u'Video Broadcast Audio Track')
        app_label = 'media'

    class Archive:
        broadcastaudio = ResourceManager( type=types.AudioTrackType, verbose_name=_( u"Broadcast Audio Track" ) )

        class Meta:
            root = settings.VIDEOS_ARCHIVE_ROOT
            release_date = False
            embargo_date = False
            last_modified = True
            created = True
            published = True


class VideoScript( ArchiveModel, models.Model ):
    """
    Model for storing scripts for videos.
    """
    id = archive_fields.IdField()
    video = TranslationForeignKey(Video)
    lang = models.CharField(verbose_name=_('Language'), max_length=7, choices=SUBTITLE_LANGUAGES, default=settings.LANGUAGE_CODE, db_index=True)
    # type = models.CharField(verbose_name=_('Audio track type'), max_length=25, choices=SPLIT_AUDIO_TYPES)

    def save( self, **kwargs ):
        """
        Override save() to always set id as video_id + '_' + lang

        # TODO: check video renaming
        """
        old_id = self.id
        self.id = '%s_%s' % (self.video.id, self.lang)

        if old_id != self.id:  # delete old
            try:
                old = VideoScript.objects.get( id=old_id )
                old.delete()
            except VideoScript.DoesNotExist:
                pass

        super( VideoScript, self ).save( **kwargs )

    def __unicode__( self ):
        return dict( SUBTITLE_LANGUAGES ).get( self.lang, self.lang )

    class Meta:
        verbose_name = _(u'Video Script')
        app_label = 'media'

    class Archive:
        script = ResourceManager( type=types.PDFType, verbose_name=_( u"Broadcast Audio Track" ) )

        class Meta:
            root = settings.VIDEOS_ARCHIVE_ROOT
            release_date = False
            embargo_date = False
            last_modified = True
            created = True
            published = True


class VideoContact( Contact ):
    """
    Contact information for a video
    """
    video = TranslationForeignKey( Video )

    class Meta:
        verbose_name = _( u'Contact' )
        app_label = 'media'


# ========================================================================
# Translation proxy model
# ========================================================================

class VideoProxy( Video, TranslationProxyMixin ):
    """
    Image proxy model for creating admin only to edit
    translated objects.
    """
    objects = Video.translation_objects

    def clean( self ):
        # Note: For some reason it's not possible to
        # to define clean/validate_unique in TranslationProxyMixin
        # so we have to do this trick, where we add the methods and
        # call into translation proxy micin.
        self.id_clean()

    def validate_unique( self, exclude=None ):
        self.id_validate_unique( exclude=exclude )

    class Meta:
        proxy = True
        verbose_name = _('Video translation')
        app_label = 'media'

    class Archive:
        class Meta:
            rename_pk = ('media_video', 'id')
            rename_fks = (
                ( 'media_video', 'source_id'),
                ( 'media_video_subject_category', 'video_id' ),
                ( 'media_video_subject_name', 'video_id' ),
                ( 'media_video_facility', 'video_id' ),
                ( 'media_videocontact', 'video_id' ),
                ( 'media_pictureoftheweek', 'video_id' ),
                ( 'releases_releasevideo', 'archive_item_id' ),
                ( 'announcements_announcementvideo', 'archive_item_id' ),
                ( 'media_videosubtitle', 'video_id' ),
                ( 'media_videoaudiotrack', 'video_id' ),
                ( 'media_videobroadcastaudiotrack', 'video_id' ),
            )
            clean_html_fields = ['description']


# Connect signals to check if fields have changed
signals.pre_save.connect(Video.fields_changed_check_pre, sender=Video)
signals.post_save.connect(Video.fields_changed_check_post, sender=Video)

# Send notification email when translation_ready is changed to True
signals.pre_save.connect(VideoProxy.send_notification_mail, sender=VideoProxy)

# Connect signal to check for changes in Content server
signals.pre_save.connect(Video.content_server_changed, sender=Video)
signals.post_save.connect(Video.sync_archive_to_content_server, sender=Video)

signals.pre_save.connect(release_date_change_check, sender=Video)

post_rename.connect(Video.sync_archive_on_rename, sender=Video)
