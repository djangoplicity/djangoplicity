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

from builtins import str
from django.conf import settings
from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from djangoplicity.archives import fields as archive_fields
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.contrib import types
from djangoplicity.archives.resources import ImageResourceManager
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.archives.utils import propagate_release_date
from djangoplicity.media.consts import DEFAULT_CREDIT, DEFAULT_CREDIT_FUNC
from djangoplicity.media.models.images import Image
from djangoplicity.metadata.archives import fields as metadatafields
from djangoplicity.translation.models import TranslationModel, \
    translation_reverse
from djangoplicity.translation.fields import TranslationForeignKey


@python_2_unicode_compatible
class ImageComparison( ArchiveModel, TranslationModel ):
    """
    Image comparisons allows to compare two images with a nice
    JavaScript feature that will reveal the two images when hovering
    the mouse over the image.
    """
    id = archive_fields.IdField()
    priority = archive_fields.PriorityField( help_text=_( u'Assessment of the quality of the image comparison (100 highest, 0 lowest). Higher priority images are ranked higher in search results than lower priority images.' ) )

    featured = models.BooleanField(default=True)

    title = metadatafields.AVMTitleField()
    description = metadatafields.AVMDescriptionField()
    credit = metadatafields.AVMCreditField( default=DEFAULT_CREDIT_FUNC )

    image_before = TranslationForeignKey( Image, related_name='imagecomparison_before_set', null=True, on_delete=models.CASCADE )
    image_after = TranslationForeignKey( Image, related_name='imagecomparison_after_set', null=True, on_delete=models.CASCADE )

    def __init__( self, *args, **kwargs ):
        super( ImageComparison, self ).__init__( *args, **kwargs )
        if not self.credit:
            self.credit = DEFAULT_CREDIT

    def __str__( self ):
        return self.title

    def height_ratio( self ):
        return float( self.image_before.height ) / float( self.image_before.width )

    def height_1280( self ):
        return int( 1280 * self.height_ratio() )

    def get_absolute_url(self):
        return translation_reverse( 'imagecomparisons_detail', args=[str( self.id if self.is_source() else self.source.id )], lang=self.lang )

    class Meta:
        ordering = ( '-priority', '-release_date', )
        app_label = 'media'
        permissions = [
            ( "view_only_non_default", "Can view only non default language" ),
        ]

    class Translation:
        fields = [ 'title', 'description', 'credit', ]
        excludes = [ 'published', 'last_modified', 'created', ]

    class Archive:
        original = ImageResourceManager( type=types.OriginalImageType )
        large = ImageResourceManager( derived='original', type=types.LargeJpegType )
        screen = ImageResourceManager( derived='original', type=types.ScreensizeJpegType )
        news = ImageResourceManager( derived='original', type=types.NewsJpegType )
        newsmini = ImageResourceManager( derived='original', type=types.NewsMiniJpegType )
        newsfeature = ImageResourceManager( derived='original', type=types.NewsFeatureType )
        medium = ImageResourceManager( derived='original', type=types.MediumJpegType )
        wallpaperthumbs = ImageResourceManager( derived='original', type=types.WallpaperThumbnailType )
        potwmedium = ImageResourceManager( derived='original', type=types.POTWMediumThumbnailJpegType )
        thumbs = ImageResourceManager( derived='original', type=types.ThumbnailJpegType )
        thumb350x = ImageResourceManager( derived='original', type=types.Thumb350xType )
        screen640 = ImageResourceManager(derived='original', type=types.Screen640Type)
        thumb300y = ImageResourceManager(derived='original', type=types.Thumb300yType)
        thumb350x = ImageResourceManager(derived='original', type=types.Thumb350xType)
        thumb700x = ImageResourceManager(derived='original', type=types.Thumb700xType)

        class Meta:
            root = getattr( settings, 'IMAGECOMPARISON_ARCHIVE_ROOT', '' )
            release_date = True
            embargo_date = True
            release_date_owner = True
            last_modified = True
            created = True
            published = True
            rename_pk = ( 'media_imagecomparison', 'id' )
            rename_fks = (
                ( 'media_imagecomparison', 'source_id' ),
                ( 'media_image', 'release_date_owner' ),
                ( 'releases_releaseimagecomparison', 'archive_item_id' )
            )
            sort_fields = ['last_modified', 'release_date', ]
            clean_html_fields = ['description', 'credit']


# ========================================================================
# Translation proxy model
# ========================================================================
class ImageComparisonProxy( ImageComparison, TranslationProxyMixin ):
    """
    Image proxy model for creating admin only to edit
    translated objects.
    """
    objects = ImageComparison.translation_objects

    def clean( self ):
        # Note: For some reason it's not possible to
        # to define clean/validate_unique in TranslationProxyMixin
        # so we have to do this trick, where we add the methods and
        # call into translation proxy mixin.
        self.id_clean()

    def validate_unique( self, exclude=None ):
        self.id_validate_unique( exclude=exclude )

    class Meta:
        proxy = True
        verbose_name = _('Image comparison translation')
        app_label = 'media'

    class Archive:
        class Meta:
            rename_pk = ( 'media_imagecomparison', 'id' )
            rename_fks = []
            clean_html_fields = ['description', 'credit']


# Propagate Image comparisons release date to Image and Videos.
propagate_release_date( ImageComparison.image_before )
propagate_release_date( ImageComparison.image_after )
# Send notification email when translation_ready is changed to True
signals.pre_save.connect( ImageComparisonProxy.send_notification_mail, sender=ImageComparisonProxy )
