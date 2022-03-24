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

from datetime import datetime

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, \
    ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.utils.translation import ugettext_lazy as _, ugettext

from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.contrib import types
from djangoplicity.archives.resources import ResourceManager
from djangoplicity.archives.utils import propagate_release_date, \
    release_date_change_check
from djangoplicity.media.models import Image, Video
from djangoplicity.metadata.translation import fields as metadatafields_trans
from djangoplicity.metadata.models import ExtendedContact, Program
from djangoplicity.translation.models import TranslationModel, \
    translation_reverse
from djangoplicity.translation.fields import TranslationForeignKey, \
    TranslationManyToManyField
from djangoplicity.media.models.comparisons import ImageComparison


# =======================================
# Defines flags and base URL for countries
# =======================================
# Deprecated: Once eso.cl is migrated this model
# and relations to it should be removed, and

class Country( models.Model ):
    isocode = models.CharField( max_length=2, primary_key=True, verbose_name=_('ISO Code') )
    url_prefix = models.CharField( max_length=255, verbose_name=_('URL Prefix') )
    name = models.CharField( max_length=255 )
    flag_url = models.CharField( max_length=255, verbose_name=_('Flag URL') )

    def __init__(self, *args, **kwargs ):
        import warnings
        warnings.warn( "Use of ReleaseTranslation and Country has been deprecated.", DeprecationWarning )
        super( Country, self ).__init__( *args, **kwargs )

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name_plural = _('countries')


# =======================================
# Press releases
# =======================================

class ReleaseType( models.Model ):
    """
    A press release can be categorized into different types of
    releases. This model is used to define centrally the possible
    types of a press release.

    Release type examples: News Release, Photo Release, Organisation Release.
    """

    name = models.CharField( max_length=100, blank=True )
    # Display name of the release type.

    def __unicode__( self ):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('Press Release Type')


class Release( ArchiveModel, TranslationModel ):
    #
    # Field definitions
    #
    id = models.SlugField( primary_key=True, help_text=_(u'Id of release - e.g. heic0801. The id must be unique.') )

    old_ids = models.CharField(verbose_name=_("Old Ids"), max_length=50, blank=True, help_text=_(u'For backwards compatibility: Historic ids of this press release.') )

    # Type of the release - see ReleaseType model for more information.
    release_type = TranslationForeignKey( ReleaseType, blank=False, null=False, default=1 )

    # Title of of the press release
    title = models.CharField( max_length=255, db_index=True, help_text=_(u"Title is shown in browser window. Use a good informative title, since search engines normally display the title on their result pages.") )

    # Subtitle of of the press release
    subtitle = models.CharField( max_length=255, blank=True, help_text=_(u"Optional subtitle to be shown just above the headline.") )

    programs = models.ManyToManyField(Program, limit_choices_to=Q(type__name='Releases'), blank=True)

    # Name of the Principal Investigator
    principal_investigator = models.CharField( max_length=255, blank= True, null=True, help_text=_(u'Name of the principal investigator') )

    release_city = models.CharField( max_length=100, blank=True, help_text=_(u"The city of the release - e.g. Paris. Can be left blank.") )

    headline = models.TextField( blank=True, help_text=_(u'HTML code in lead is not allowed. The lead is further more normally shown in search engine results, making the description an effective way of capturing users attention.') )

    description = models.TextField( blank=True )

    notes = models.TextField( blank=True )

    more_information = models.TextField( blank=True )

    links = models.TextField( blank=True, help_text=_(u'Help text') )

    subject_category = metadatafields_trans.TranslationAVMSubjectCategoryField()

    subject_name = metadatafields_trans.TranslationAVMSubjectNameField()

    facility = metadatafields_trans.TranslationFacilityManyToManyField()

    instruments = metadatafields_trans.TranslationInstrumentManyToManyField()

    publications = metadatafields_trans.TranslationAVMPublicationField()

    # Field for posting disclaimers on a press release - e.g. if it's retracted.
    disclaimer = models.TextField( blank=True, help_text=_(u'Disclaimer for press release - usually e.g. retractions of previously issued press releases.') )

    related_images = TranslationManyToManyField( Image, through='ReleaseImage', only_sources=True )

    related_videos = TranslationManyToManyField( Video, through='ReleaseVideo', only_sources=True )

    related_comparisons = TranslationManyToManyField( ImageComparison, through='ReleaseImageComparison', only_sources=True )

    stock_images = TranslationManyToManyField( Image, only_sources=True, through='ReleaseStockImage', related_name='stock' )

    meltwater_keywords = models.TextField( blank=True, help_text=_(u'Used to store Meltwater Keywords.'), verbose_name=_(u'Keywords') )

    #
    # Kids press releases
    #
    kids_title = models.CharField( max_length=255, blank=True )

    kids_description = models.TextField( blank=True )

    kids_image = models.ForeignKey( Image, blank=True, null=True, related_name='kids_image_release_set', help_text=_(u'Use this to override the default Release image.') )

    def get_embargo_login( self ):
        return settings.ARCHIVE_EMBARGO_LOGIN

    def _set_main_image(self, im ):
        self._main_image_cache = im

    def _get_main_image(self):
        try:
            return self._main_image_cache
        except AttributeError:
            for visual in self.releaseimage_set.all():
                if visual.main_visual:
                    self._main_visual_cache = visual.archive_item
                    return visual.archive_item

    main_image = property( _get_main_image )

    def _get_main_imagen_comparison(self):
        try:
            return self._main_imagen_comparison_cache
        except AttributeError:
            for visual in self.releaseimagecomparison_set.all():
                if visual.main_visual:
                    self._main_imagen_comparison_cache = visual.archive_item
                    return visual.archive_item

    main_image_comparison = property(_get_main_imagen_comparison)

    def _set_main_video(self, vid ):
        self._main_video_cache = vid

    def _get_main_video(self):
        try:
            return self._main_video_cache
        except AttributeError:
            try:
                vid = ReleaseVideo.objects.filter( main_visual=True, release=self if self.is_source() else self.source ).get()
                self._main_video_cache = vid.archive_item
                return vid.archive_item
            except (IndexError, ObjectDoesNotExist, MultipleObjectsReturned):
                return None

    main_video = property( _get_main_video )

    @staticmethod
    def store_main_visuals( object_list ):
        """
        Fetches the main image and videos for all releases in object list using one query, instead
        of one query per release.
        """
        relids = [ x.id if x.is_source() else x.source_id for x in object_list ]

        ims = ReleaseImage.objects.filter( main_visual=True, release__in=relids ).select_related( 'archive_item' )
        vids = ReleaseVideo.objects.filter( main_visual=True, release__in=relids ).select_related( 'archive_item' )

        release_mapping = {}
        for im in ims:
            release_mapping[im.release_id] = im.archive_item

        for obj in object_list:
            try:
                im = release_mapping[obj.id if obj.is_source() else obj.source_id]
                obj._set_main_image( im )
            except KeyError:
                obj._set_main_image( None )

        release_mapping = {}
        for vid in vids:
            release_mapping[vid.release] = vid.archive_item

        for obj in object_list:
            try:
                vid = release_mapping[obj.id if obj.is_source() else obj.source_id]
                obj._set_main_video( vid )
            except KeyError:
                obj._set_main_video( None )

    def rename( self, new_pk ):
        '''
        Extend Archive's rename() to send email notification if original is renamed
        '''
        if self.published and self.is_source() and hasattr(settings, 'RELEASE_RENAME_NOTIFY'):
            msg_subject = 'Press Release renamed: %s -> %s' % ( self.pk, new_pk )
            msg_body = """https://www.eso.org/public/news/%s/""" % new_pk
            msg_from = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
            msg_to = getattr(settings, 'RELEASE_RENAME_NOTIFY', '')
            if msg_from and msg_to:
                send_mail( msg_subject, msg_body, msg_from, msg_to, fail_silently=False )

        return super( Release, self ).rename(new_pk)

    def is_published(self):
        return datetime.now() >= self.release_date

    @staticmethod
    def get_latest_release( count=1 ):
        qs = Release.objects.filter( release_date__lte=datetime.now(), published=True ).order_by( '-release_date' )[:count]
        return qs

    class Meta:
        ordering = ['-release_date', '-id']
        get_latest_by = "release_date"
        verbose_name = _('Press Release')
        verbose_name_plural = _('Press Releases')
        permissions = [
            ( "view_only_non_default", "Can view only non default language" ),
        ]

    def get_absolute_url(self):
        return translation_reverse( 'releases_detail', args=[str( self.id if self.is_source() else self.source.id )], lang=self.lang )

    def __unicode__( self ):
        return self.id

    class Translation:
        fields = ['description', 'disclaimer', 'headline', 'links', 'more_information', 'notes', 'release_city', 'subtitle', 'title', 'kids_title', 'kids_description']
        excludes = ['published', 'last_modified', 'created', 'meltwater_keywords']
        set_deep_copy = ['releasetranslationcontact_set']

    class Archive:
        doc = ResourceManager( type=types.DocType )
        pdf = ResourceManager( type=types.PDFType )
        text = ResourceManager( type=types.TxtType )
        sciencepapers = ResourceManager( type=types.DirType, verbose_name=_('Science Papers') )

        class Meta:
            root = settings.RELEASE_ARCHIVE_ROOT
            release_date = True
            embargo_date = True
            last_modified = True
            created = True
            published = True
            rename_pk = ('releases_release', 'id')
            rename_fks = (
                ('releases_release', 'source_id'),
                ('releases_release_facility', 'release_id'),
                ('releases_release_instruments', 'release_id'),
                ('releases_release_subject_category', 'release_id'),
                ('releases_release_subject_name', 'release_id'),
                ('releases_releasecontact', 'release_id'),
                ('releases_releaseimage', 'release_id'),
                ('releases_releasevideo', 'release_id'),
                ('releases_releasetranslation', 'release_id'),
                ('media_imagecomparison', 'release_date_owner'),
                ('media_image', 'release_date_owner'),
                ('media_video', 'release_date_owner'),
            )
            sort_fields = ['last_modified', 'release_date']
            clean_html_fields = ['description', 'notes', 'more_information',
                'links', 'disclaimer']


# =======================================
# Kids proxy (needed for specialised admin)
# =======================================
class KidsRelease( Release ):
    def get_absolute_url(self):
        return translation_reverse( 'releases_detail_kids', args=[str( self.id if self.is_source() else self.source.id )], lang=self.lang )

    class Meta:
        proxy = True
        verbose_name = _('Kids Press Release')

    class Archive:
        class Meta:
            pass


KidsRelease.objects = Release.objects


# =======================================
# Translation proxy (needed for specialised admin)
# =======================================

class ReleaseProxy( Release ):
    objects = Release.translation_objects

    def clean(self):
        """ Determine id of release translation """
        self._is_existing_translation = True

        # Determine if source exists.
        if self.source is None:
            raise ValidationError("You must provide a translation source.")

        # Determine PK if translation is new.
        if not self.id:
            self._is_existing_translation = False
            self.id = "%s%s" % ( self.source.id, self.lang )
        else:
            # Check if id matches source and lang
            if self.id != "%s%s" % ( self.source.id, self.lang ):
                pass
                # TODO: It doesn't so change it yourself.
                #old_obj = ReleaseProxy.objects.get( id=self.id )

        super( ReleaseProxy, self ).clean()

    def validate_unique( self, exclude=None ):
        """ Validate that translation language is *not* identical to source language. """
        try:
            if not hasattr( self, '_is_existing_translation' ):
                self._is_existing_translation = True
            if not self._is_existing_translation:
                ReleaseProxy.objects.filter( source=self.source.id, lang=self.lang ).get()
                raise ValidationError( { 'lang': ["Translation already exists for selected language."] })
        except ReleaseProxy.DoesNotExist:
            pass

        super(ReleaseProxy, self).validate_unique( exclude=exclude )

    def generate_duplicate_id( self, lang ):
        """
        Returns a new id including the given language code
        """
        if self.source:
            return self.source.id + lang
        else:
            return self.id + lang

    class Meta:
        proxy = True
        verbose_name = _('Press Release Translation')

    class Archive:
        class Meta:
            rename_pk = ('releases_release', 'id')
            rename_fks = (
                ('releases_releasetranslationcontact', 'release_id'),
            )
            clean_html_fields = ['description', 'notes', 'more_information',
                'links', 'disclaimer']


# =======================================
# Contacts for a press release
# =======================================

class ReleaseContact( ExtendedContact ):
    """
    Source release contacts (global for all translations as well)
    """
    release = TranslationForeignKey( Release, only_sources=True )

    class Meta:
        verbose_name = _(u'contact')
        ordering = ( 'id', )  # In the order they where added (and shown in admin)


class ReleaseTranslationContact( ExtendedContact ):
    """
    A contact specific for a PR translation (these contacts are shown before
    the source release's contacts.
    """
    release = TranslationForeignKey( Release, only_sources=False )

    class Meta:
        verbose_name = _(u'translation contact')
        ordering = ( 'id', )  # In the order they where added (and shown in admin)


# =======================================
# Related images, videos and stock images
# =======================================

class RelatedRelease( models.Model  ):
    """
    Abstract model to link another archive item (e.g. visuals) to a release. The Model should be
    subclassed and used as a many-to-many intermediary model::

        class RelatedReleaseImage( RelatedRelease ):
            archive_item = models.ForeignKey( Image, verbose_name=('Image') )

            class Meta:
                verbose_name = _('...')
    """

    # The release to link with another archive item.
    release = TranslationForeignKey( Release, verbose_name=_('Related release'), only_sources=True )

    order = models.PositiveSmallIntegerField( blank=True, null=True )
    # Used to define an order for the archive items, in case this should not be via the alphabetic order of the id.

    main_visual = models.BooleanField( default=False )
    # Defines the primary visual for a release - the user is responsible for only selecting one main visual.

    # In case you ingest a visual into several release, this field can be used to override the id.
    override_id = models.SlugField( blank=True, null=True, verbose_name=_('Override ID') )

    # Define if the visual should be hidden if used for e.g. the kiosk
    hide = models.BooleanField( default=False, verbose_name=_('Hide on kiosk') )

    def __unicode__(self):
        return ugettext("Archive Item for Release %s" % (unicode(self.release.id)))

    class Meta:
        abstract = True


class ReleaseImage( RelatedRelease ):
    """ Images related to a release. """
    archive_item = TranslationForeignKey( Image, verbose_name=_('Related Image') )
    zoomable = models.BooleanField( default=False, verbose_name=_('Zoomable if main') )


class ReleaseVideo( RelatedRelease ):
    """ Images related to a release. """
    archive_item = TranslationForeignKey( Video, verbose_name=_('Related Video') )


class ReleaseStockImage( RelatedRelease ):
    """ Stock Images related to a release. """
    archive_item = TranslationForeignKey( Image, verbose_name=_('Related Stock Image') )


class ReleaseImageComparison( RelatedRelease ):
    """ Stock Images related to a release. """
    archive_item = TranslationForeignKey( ImageComparison, verbose_name=_('Related Image Comparison') )


# =======================================
# Flags for press releases
# =======================================
# Deprecated: Once eso.cl has been migrated to eso.org
# then all translations are available in djangoplicity, and
# this model is no longer needed.

class ReleaseTranslation( models.Model ):
    release = models.ForeignKey( Release )
    country = models.ForeignKey( Country )
    url_suffix = models.CharField( max_length=255, verbose_name=_('URL Suffix') )

    def __init__(self, *args, **kwargs ):
        import warnings
        warnings.warn( "Use of ReleaseTranslation and Country has been deprecated.", DeprecationWarning )
        super( ReleaseTranslation, self ).__init__( *args, **kwargs )


# =======================================
# Helper methods
# =======================================

def save_related(instance, related_field):
    related_object_set = getattr( instance, related_field )
    for o in related_object_set.all():
        o.save()


def relateditems_cache_reset( sender, instance, created, raw, **kwargs ):
    if raw:
        return
    save_related(instance, 'related_images')
    save_related(instance, 'related_videos')


# =======================================
# Connect signals
# =======================================
post_save.connect( relateditems_cache_reset, sender=Release )
pre_save.connect( ReleaseProxy.send_notification_mail, sender=ReleaseProxy )  # Send notification email when translation_ready is changed to True
pre_save.connect( release_date_change_check, sender=Release)

# Propagate release dates from PRs to images and videos.
propagate_release_date( Release.related_images )
propagate_release_date( Release.related_videos )
propagate_release_date( Release.related_comparisons )
