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

import copy

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from six import python_2_unicode_compatible

from djangoplicity.archives import fields as archive_fields
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.media.models.images import Image
from djangoplicity.metadata.archives import fields as metadatafields
from djangoplicity.translation.fields import TranslationForeignKey
from djangoplicity.translation.models import TranslationModel, \
    translation_reverse


# The bands of the electromagnetic spectrum, ordered from the shortest to the
# longest wavelength. Note that djangoplicity.metadata.consts already defines
# SPECTRAL_BAND_CHOICES (the AVM controlled vocabulary used by
# ImageExposure.spectral_band), but it has no Microwave band and calls the
# visible band "Optical". The keys below are kept close to the AVM values so
# the two can be mapped later on if needed.
class WavelengthBand( models.TextChoices ):
    GAMMA_RAY = 'gamma-ray', _('Gamma-ray')
    X_RAY = 'x-ray', _('X-ray')
    ULTRAVIOLET = 'ultraviolet', _('Ultraviolet')
    VISIBLE = 'visible', _('Visible light')
    INFRARED = 'infrared', _('Infrared')
    MICROWAVE = 'microwave', _('Microwave')
    RADIO = 'radio', _('Radio')


# Position of every band on the spectrum, shortest wavelength first. Bands are
# always presented in this order, so MultiwavelengthImageBand carries no order
# field of its own.
WAVELENGTH_BAND_ORDER = dict(
    ( value, index ) for index, value in enumerate( WavelengthBand.values ) )


class CaptionAlign( models.TextChoices ):
    LEFT = 'left', _('Left')
    RIGHT = 'right', _('Right')


@python_2_unicode_compatible
class MultiwavelengthImage( ArchiveModel, TranslationModel ):
    """
    An astronomical object presented across several bands of the
    electromagnetic spectrum. The visitor switches band and the visual is
    swapped, so the archive itself holds no file resources: every visual comes
    from the Image archive through MultiwavelengthImageBand.
    """
    id = archive_fields.IdField()
    title = archive_fields.TitleField()
    subtitle = models.CharField( max_length=255, blank=True )
    description = archive_fields.DescriptionField()
    credit = metadatafields.AVMCreditField()
    priority = archive_fields.PriorityField( default=0 )
    main_band = models.CharField( max_length=16, choices=WavelengthBand.choices,
        default=WavelengthBand.VISIBLE, verbose_name=_('Main band'),
        help_text=_('Band shown when the page opens and used as the main visual of the object') )

    class Translation:
        fields = ['title', 'subtitle', 'description', 'credit', ]
        excludes = ['published', 'last_modified', 'created', ]

    class Archive:
        # No resources of its own - the visuals live in the Image archive.

        class Meta:
            release_date = True
            embargo_date = True
            last_modified = True
            created = True
            published = True
            sort_fields = ['last_modified', 'release_date', 'priority', ]
            rename_pk = ( 'media_multiwavelengthimage', 'id' )
            rename_fks = (
                ( 'media_multiwavelengthimage', 'source_id' ),
                ( 'media_multiwavelengthimageband', 'multiwavelength_image_id' ),
                ( 'media_multiwavelengthimagebandtranslation', 'translation_id' ),
            )
            clean_html_fields = ['description', 'credit']

    class Meta:
        ordering = ['-priority', '-release_date']
        verbose_name = _('Multiwavelength Image')
        app_label = 'media'
        permissions = [
            ( "view_only_non_default", "Can view only non default language" ),
        ]

    def __str__( self ):
        return self.id

    def get_absolute_url( self ):
        return translation_reverse( 'multiwavelength_detail', args=[str( self.id if self.is_source() else self.source.id )], lang=self.lang )

    def ordered_bands( self ):
        """
        The bands of this object sorted along the spectrum, from gamma-ray to
        radio. Sorting is done in Python so a prefetch of `bands__image` (or
        `source__bands__image` for translations) is reused instead of
        triggering another query.

        On a translation the bands come from the source, with the title and
        description replaced by the translated ones where they have been
        filled in. The source bands are copied, not modified, so the source
        instances stay untouched.
        """
        bands = [b for b in self.get_source().bands.all() if b.band in WAVELENGTH_BAND_ORDER]

        if self.is_translation():
            translated = dict( ( t.band, t ) for t in self.band_translations.all() )
            for i, band in enumerate( bands ):
                t = translated.get( band.band )
                if t is None:
                    continue
                band = copy.copy( band )
                if t.title:
                    band.title = t.title
                if t.description:
                    band.description = t.description
                bands[i] = band

        return sorted( bands, key=lambda b: b.spectrum_index )

    def main_band_object( self ):
        """
        The band selected as main in the admin, or the shortest-wavelength
        band the object has if that one is missing.
        """
        bands = self.ordered_bands()
        for band in bands:
            if band.band == self.main_band:
                return band
        return bands[0] if bands else None

    @property
    def main_visual( self ):
        """
        {% opengraph_image %} expects a main_visual attribute. Use the image
        of the main band.
        """
        band = self.main_band_object()
        return band.image if band else None


@python_2_unicode_compatible
class MultiwavelengthImageBand( models.Model ):
    """
    One wavelength view of a MultiwavelengthImage: the visual shown when the
    visitor selects this band, together with its own title and description.
    Bands are shared by all translations (see MultiwavelengthImageBandTranslation
    for the translated texts).
    """
    multiwavelength_image = TranslationForeignKey( MultiwavelengthImage,
        related_name='bands', only_sources=True, on_delete=models.CASCADE )
    band = models.CharField( max_length=16, choices=WavelengthBand.choices,
        db_index=True )
    image = TranslationForeignKey( Image, verbose_name=_('Related Image'),
        only_sources=True, on_delete=models.CASCADE )
    title = models.CharField( max_length=255, blank=True )
    description = models.TextField( blank=True )
    caption_align = models.CharField( max_length=5, choices=CaptionAlign.choices,
        default=CaptionAlign.LEFT, help_text=_('Side of the image where the band text is shown') )

    class Meta:
        unique_together = ( 'multiwavelength_image', 'band' )
        verbose_name = _('Wavelength band')
        app_label = 'media'

    def __str__( self ):
        return "%s: %s" % ( self.multiwavelength_image_id, self.get_band_display() )

    @property
    def spectrum_index( self ):
        """ Position of the band on the spectrum (0 = gamma-ray). """
        return WAVELENGTH_BAND_ORDER.get( self.band, len( WAVELENGTH_BAND_ORDER ) )

    @property
    def credit( self ):
        """ Bands don't carry their own credit - use the image's. """
        return self.image.credit


@python_2_unicode_compatible
class MultiwavelengthImageBandTranslation( models.Model ):
    """
    Translated title and description of one band of the spectrum for one
    translation of a MultiwavelengthImage. The language is the one of the
    translation it belongs to, and the band is matched by its spectrum value
    against the source bands, so the rows can be filled in before the source
    is even chosen. Empty values fall back to the source band's text.
    """
    translation = TranslationForeignKey( MultiwavelengthImage,
        related_name='band_translations', only_sources=False, on_delete=models.CASCADE )
    band = models.CharField( max_length=16, choices=WavelengthBand.choices,
        db_index=True )
    title = models.CharField( max_length=255, blank=True )
    description = models.TextField( blank=True )

    class Meta:
        unique_together = ( 'translation', 'band' )
        verbose_name = _('Wavelength band translation')
        app_label = 'media'

    def __str__( self ):
        return "%s: %s" % ( self.translation_id, self.get_band_display() )

    @property
    def spectrum_index( self ):
        """ Position of the band on the spectrum (0 = gamma-ray). """
        return WAVELENGTH_BAND_ORDER.get( self.band, len( WAVELENGTH_BAND_ORDER ) )


# ========================================================================
# Translation proxy model
# ========================================================================
class MultiwavelengthImageProxy( MultiwavelengthImage, TranslationProxyMixin ):
    """
    Multiwavelength image proxy model for creating admin only to edit
    translated objects.
    """
    objects = MultiwavelengthImage.translation_objects

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
        verbose_name = _('Multiwavelength Image translation')
        app_label = 'media'

    class Archive:
        class Meta:
            rename_pk = ( 'media_multiwavelengthimage', 'id' )
            rename_fks = (
                ( 'media_multiwavelengthimagebandtranslation', 'translation_id' ),
            )
            clean_html_fields = ['description', 'credit']


# Send notification email when translation_ready is changed to True
signals.pre_save.connect( MultiwavelengthImageProxy.send_notification_mail, sender=MultiwavelengthImageProxy )
