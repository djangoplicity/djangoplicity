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

from builtins import str
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.utils.translation import ugettext_lazy as _, ugettext
from djangoplicity.metadata.models import Program
from djangoplicity.announcements import archive_settings
from djangoplicity.archives import fields as archive_fields
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.contrib import types
from djangoplicity.archives.resources import ResourceManager
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.archives.utils import propagate_release_date, \
    release_date_change_check
from djangoplicity.media.models import Image, Video, ImageComparison
from djangoplicity.translation.models import TranslationModel, \
    translation_reverse
from djangoplicity.translation.fields import TranslationForeignKey, \
    TranslationManyToManyField
from six import python_2_unicode_compatible


if hasattr(settings, 'ANNOUNCEMENTS_ARCHIVE_ROOT'):
    ANNOUNCEMENTS_ROOT = settings.ANNOUNCEMENTS_ARCHIVE_ROOT
else:
    ANNOUNCEMENTS_ROOT = archive_settings.ANNOUNCEMENT_ROOT

WEBUPDATE_ROOT = archive_settings.WEBUPDATE_ROOT


# ========================================
# Web updates
# ========================================
@python_2_unicode_compatible
class WebUpdateType( models.Model ):
    """
    Type of web update (similar to release types for press releases)
    """
    name = models.CharField( max_length=255 )

    class Meta:
        ordering = ['name']

    def __str__( self ):
        return self.name


@python_2_unicode_compatible
class WebUpdate( ArchiveModel, models.Model ):
    """
    Minor updates.
    """
    id = archive_fields.IdField()
    title = archive_fields.TitleField()
    link = archive_fields.URLField( blank=True )
    description = archive_fields.DescriptionField( blank=True )
    type = models.ForeignKey( WebUpdateType , on_delete=models.CASCADE)

    class Archive:
        class Meta:
            root = archive_settings.WEBUPDATE_ROOT
            release_date = True
            embargo_date = False
            last_modified = True
            created = True
            published = True
            sort_fields = ['release_date', ]
            rename_pk = ('announcements_webupdate', 'id')

    class Meta:
        ordering = ['-release_date']

    def get_absolute_url( self ):
        return self.link

    def __str__( self ):
        return "%s: %s" % ( self.id, self.title)


# ========================================
# Announcements
# ========================================
@python_2_unicode_compatible
class AnnouncementType( models.Model ):
    """
    An announcement press release can be categorized into different types
    This model is used to define centrally the possible types
    """

    # Display name of the release type
    name = models.CharField( max_length=100, blank=True )

    def __str__( self ):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('Announcement Type')


@python_2_unicode_compatible
class Announcement( ArchiveModel, TranslationModel ):
    """
    Similar to press releases but with fewer fields.
    """
    id = archive_fields.IdField()
    title = archive_fields.TitleField()
    subtitle = models.CharField( max_length=255, blank=True, help_text=_( u"Optional subtitle to be shown just above the headline." ) )
    description = archive_fields.DescriptionField()
    contacts = models.TextField( blank=True, help_text=_( u'Contacts' ) )
    links = models.TextField( blank=True, help_text=_( u'Links' ) )
    featured = models.BooleanField( default=True )
    related_images = TranslationManyToManyField( Image, through='AnnouncementImage' )
    related_videos = TranslationManyToManyField( Video, through='AnnouncementVideo' )
    related_comparisons = TranslationManyToManyField(ImageComparison,
        through='AnnouncementImageComparison', only_sources=True)
    programs = TranslationManyToManyField(Program, limit_choices_to=Q(types__name__iexact='Announcements'), blank=True,
                                          only_sources=True)

    announcement_type = TranslationForeignKey( AnnouncementType, blank=True, null=True, default=None, on_delete=models.CASCADE)

    def get_embargo_login(self):
        return settings.ARCHIVE_EMBARGO_LOGIN

    def _set_main_visual(self, vis ):
        self._main_visual_cache = vis

    def _get_main_visual(self):
        try:
            return self._main_visual_cache
        except AttributeError:
            pass

        for visual in self.announcementimage_set.all():
            if visual.main_visual:
                self._main_visual_cache = visual.archive_item
                return visual.archive_item

        for visual in self.announcementimagecomparison_set.all():
            if visual.main_visual:
                self._main_visual_cache = visual.archive_item
                return visual.archive_item

        for visual in self.announcementvideo_set.all():
            if visual.main_visual:
                self._main_visual_cache = visual.archive_item
                return visual.archive_item

        return None

    main_visual = property( _get_main_visual )

    def _get_main_imagen_comparison(self):
        try:
            return self._main_imagen_comparison_cache
        except AttributeError:
            for visual in self.announcementimagecomparison_set.all():
                if visual.main_visual:
                    self._main_imagen_comparison_cache = visual.archive_item
                    return visual.archive_item

    main_image_comparison = property(_get_main_imagen_comparison)

    def rename( self, new_pk ):
        '''
        Extend Archive's rename() to send email notification if original is renamed
        '''
        if self.published and self.is_source() and hasattr(settings, 'ANNOUNCEMENT_RENAME_NOTIFY'):
            msg_subject = 'Announcement renamed: %s -> %s' % ( self.pk, new_pk )
            msg_body = """https://www.eso.org/public/announcements/%s/""" % new_pk
            msg_from = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
            msg_to = getattr(settings, 'ANNOUNCEMENT_RENAME_NOTIFY', '')
            if msg_from and msg_to:
                send_mail( msg_subject, msg_body, msg_from, msg_to, fail_silently=False )

        return super( Announcement, self ).rename(new_pk)

    @staticmethod
    def store_main_visuals(object_list):
        '''
        Fetches the main image for all announcements in object list using one query, instead
        of one query per announcement.
        '''
        annids = [x.id if x.is_source() else x.source_id for x in object_list]

        images = (
            AnnouncementImage.objects
            .filter(main_visual=True, announcement__in=annids)
            .select_related('archive_item')
        )
        videos = (
            AnnouncementVideo.objects
            .filter(main_visual=True, announcement__in=annids)
            .select_related('archive_item')
        )
        comparisons = (
            AnnouncementImageComparison.objects
            .filter(main_visual=True, announcement__in=annids)
            .select_related('archive_item')
        )

        announcement_mapping = {}
        for video in videos:
            announcement_mapping[video.announcement_id] = video.archive_item
        for image in images:
            announcement_mapping[image.announcement_id] = image.archive_item
        for comparison in comparisons:
            announcement_mapping[comparison.announcement_id] = comparison.archive_item

        for obj in object_list:
            try:
                visual = announcement_mapping[obj.id if obj.is_source() else obj.source_id]
                obj._set_main_visual(visual)
            except KeyError:
                obj._set_main_visual(None)

    @staticmethod
    def get_latest_announcement( len=1, only_featured=False ):
        qs = Announcement.objects.filter( release_date__lte=datetime.now(), published=True )
        if only_featured:
            qs = qs.filter( featured=True )
        return qs.order_by( '-release_date' )[:len]

    class Meta:
        ordering = ['-release_date', '-id']
        get_latest_by = "release_date"
        permissions = [
            ( "view_only_non_default", "Can view only non default language" ),
        ]

    def get_absolute_url(self):
        return translation_reverse( 'announcements_detail', args=[str( self.id if self.is_source() else self.source.id )], lang=self.lang )

    def __str__( self ):
        return u"%s: %s" % ( self.id, self.title )

    class Translation:
        fields = ['title', 'subtitle', 'description', 'contacts', 'links' ]
        excludes = ['published', 'last_modified', 'created', ]
        non_default_languages_in_fallback = False  # Don't show non-en anns. if no en translation is available

    class Archive:
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType )
        sciencepaper = ResourceManager( type=types.PDFType, verbose_name=_('Science paper') )

        class Meta:
            root = ANNOUNCEMENTS_ROOT
            release_date = True
            embargo_date = True
            last_modified = True
            created = True
            published = True
            rename_pk = ('announcements_announcement', 'id')
            rename_fks = (
                ('announcements_announcement', 'source_id'),
                ('announcements_announcementimage', 'announcement_id'),
                ('announcements_announcementimagecomparison', 'announcement_id'),
                ('announcements_announcementvideo', 'announcement_id'),
                ('media_image', 'release_date_owner'),
                ('media_video', 'release_date_owner'),
                ('media_imagecomparison', 'release_date_owner'),
            )
            sort_fields = ['last_modified', 'release_date']
            clean_html_fields = ['description', 'links', 'contacts']


# ========================================================================
# Translation proxy model
# ========================================================================
@python_2_unicode_compatible
class AnnouncementProxy( Announcement, TranslationProxyMixin ):
    """
    Announcement proxy model for creating admin only to edit
    translated objects.
    """
    objects = Announcement.translation_objects

    def clean( self ):
        # Note: For some reason it's not possible to
        # to define clean/validate_unique in TranslationProxyMixin
        # so we have to do this trick, where we add the methods and
        # call into translation proxy micin.
        self.id_clean()

    def validate_unique( self, exclude=None ):
        self.id_validate_unique( exclude=exclude )

    def __str__( self ):
        return "%s: %s" % ( self.id, self.title )

    class Meta:
        proxy = True
        verbose_name = _('Announcement translation')

    class Archive:
        class Meta:
            rename_pk = ('announcements_announcement', 'id')
            rename_fks = []
            clean_html_fields = ['description', 'links', 'contacts']


# =======================================
# Related images, videos and stock images
# =======================================
@python_2_unicode_compatible
class RelatedAnnouncement( models.Model  ):
    """
    Abstract model to link another archive item (e.g. visuals) to an Announcement. The Model should be
    subclassed and used as a many-to-many intermediary model::

        class RelatedAnnouncementImage( RelatedRAnnouncement ):
            archive_item = models.ForeignKey( Image, verbose_name=('Image'), on_delete=models.CASCADE )

            class Meta:
                verbose_name = _('...')
    """

    announcement = TranslationForeignKey( Announcement, verbose_name=_('Related announcement'), on_delete=models.CASCADE)
    # The announcement to link with another archive item.

    order = models.PositiveSmallIntegerField( blank=True, null=True )
    # Used to define an order for the archive items, in case this should not be via the alphabetic order of the id.

    main_visual = models.BooleanField( default=False )
    # Defines the primary visual for an announcement - the user is responsible for only selecting one main visual.

    override_id = models.SlugField( blank=True, null=True, verbose_name=_('Override ID') )
    # In case you ingest a visual into several announcements, this field can be
    # used to override the id.

    hide = models.BooleanField( default=False, verbose_name=_('Hide on kiosk') )
    # Define if the visual should be hidden if used for e.g. the kiosk

    def __str__( self ):
        return ugettext( "Archive Item for Announcement %s" % ( str( self.announcement.id ) ) )

    class Meta:
        abstract = True


class AnnouncementImage( RelatedAnnouncement ):
    """ Images related to an announcement. """
    archive_item = TranslationForeignKey( Image, verbose_name=_('Related Image'), on_delete=models.CASCADE )


class AnnouncementVideo( RelatedAnnouncement ):
    """ Videos related to an announcement. """
    archive_item = TranslationForeignKey( Video, verbose_name=_('Related Video'), on_delete=models.CASCADE )


class AnnouncementImageComparison(RelatedAnnouncement):
    '''
    Image Comparisons related to an announcement
    '''
    archive_item = TranslationForeignKey(ImageComparison,
        verbose_name=_('Related Image Comparison'), on_delete=models.CASCADE)


# =======================================
# Helper methods
# =======================================
def save_related(instance, related_field):
    related_object_set = getattr( instance, related_field )
    for o in related_object_set.all():
        o.save()


def relateditems_cache_reset( sender, instance, raw=False, **kwargs ):
    if raw:
        return
    save_related(instance, 'related_images')
    save_related(instance, 'related_videos')
    save_related(instance, 'related_comparisons')


# =======================================
# Connect signals
# =======================================
post_save.connect( relateditems_cache_reset, sender=Announcement )
pre_save.connect( AnnouncementProxy.send_notification_mail, sender=AnnouncementProxy )  # Send notification email when translation_ready is changed to True
pre_save.connect( release_date_change_check, sender=Announcement)

# Propagate release dates from PRs to images and videos.
propagate_release_date( Announcement.related_images )
propagate_release_date( Announcement.related_videos )
propagate_release_date( Announcement.related_comparisons )
