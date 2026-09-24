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
import math

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, signals
from django.utils.translation import ugettext_lazy as _
from six import python_2_unicode_compatible

from djangoplicity.archives import fields as archive_fields
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.media.consts import MULTIPLICATION_SIGN, \
    SPEED_OF_LIGHT_NM, SUPERSCRIPT_DIGITS, WAVELENGTH_UNITS
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


WAVELENGTH_BAND_LABELS = dict( WavelengthBand.choices )


# Closed wavelength interval (nanometres) of every band, shortest wavelength
# (highest energy) first. The bands touch, and a wavelength exactly on a bound
# belongs to the higher energy band, which is why band_for_wavelength() below
# compares against the upper bound.
WAVELENGTH_BAND_RANGES = (
    ( WavelengthBand.GAMMA_RAY, 1e-4, 0.01 ),
    ( WavelengthBand.X_RAY, 0.01, 10.0 ),
    ( WavelengthBand.ULTRAVIOLET, 10.0, 380.0 ),
    ( WavelengthBand.VISIBLE, 380.0, 780.0 ),
    ( WavelengthBand.INFRARED, 780.0, 400000.0 ),
    ( WavelengthBand.MICROWAVE, 400000.0, 1e7 ),
    ( WavelengthBand.RADIO, 1e7, 1e9 ),
)


def band_for_wavelength( wavelength ):
    """
    The band a wavelength in nanometres falls into, or None if it is not
    usable. Values off either end are pinned to it, so that every saved
    observation has a band: under 1e-4 nm is gamma-ray, over 1e9 nm is radio.
    """
    if not wavelength or wavelength <= 0:
        return None
    for band, _lower, upper in WAVELENGTH_BAND_RANGES:
        if wavelength <= upper:
            return band
    return WavelengthBand.RADIO


def frequency_for_wavelength( wavelength ):
    """ The frequency in hertz of a wavelength in nanometres, or None. """
    if not wavelength or wavelength <= 0:
        return None
    return SPEED_OF_LIGHT_NM / wavelength


def wavelength_label( wavelength ):
    """ A wavelength in nanometres as "550 nm", "400 um" or "1 cm". """
    if not wavelength or wavelength <= 0:
        return u''
    for factor, unit in WAVELENGTH_UNITS:
        value = wavelength / factor
        if value >= 1:
            return u'%g %s' % ( round( value, 1 ), unit )
    return u'%.3g pm' % ( wavelength / 1e-3 )


def superscript( number ):
    """ "13" -> "13" in superscript digits. """
    return u''.join( SUPERSCRIPT_DIGITS.get( c, c ) for c in str( number ) )


def frequency_label( frequency ):
    """
    A frequency in hertz as "3x10^13 Hz" or "10^8 Hz", with Unicode superscripts instead of <sup> so it also works 
    as plain text.
    """
    if not frequency or frequency <= 0:
        return u''
    # Scientific notation: 3.2e13 -> coefficient 3.2, exponent 13.
    exponent = int( math.floor( math.log10( frequency ) ) )
    coefficient = round( frequency / ( 10.0 ** exponent ), 1 )
    # Rounding can push the coefficient up to 10 (9.97 -> 10.0): carry it over.
    if coefficient >= 10:
        coefficient /= 10.0
        exponent += 1
    if coefficient == 1:
        return u'10%s Hz' % superscript( exponent )
    return u'%g%s10%s Hz' % (
        coefficient, MULTIPLICATION_SIGN, superscript( exponent ) )


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
    # Not in Translation.fields, so translations inherit it from the source.
    use_wavelength_selector = models.BooleanField( default=True,
        verbose_name=_('Wavelength selector'),
        help_text=_('Show the spectrum selector. Untick it to show a simpler '
                    'image switcher instead.') )

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
        The images of this object along the spectrum, from the shortest
        wavelength (gamma-ray) to the longest (radio). Several images may share
        a band. The order comes from MultiwavelengthImageBand.Meta.ordering,
        which the prefetch of `bands__image` (or `source__bands__image` for
        translations) carries with it, so no sorting is needed here.

        On a translation the bands come from the source, with the title and
        description replaced by the translated ones where they have been
        filled in. The source bands are copied, not modified, so the source
        instances stay untouched.
        """
        bands = [b for b in self.get_source().bands.all() if b.wavelength]

        if self.is_translation():
            translated = dict( ( t.band_id, t ) for t in self.band_translations.all() )
            for i, band in enumerate( bands ):
                t = translated.get( band.pk )
                if t is None:
                    continue
                band = copy.copy( band )
                if t.title:
                    band.title = t.title
                if t.description:
                    band.description = t.description
                bands[i] = band

        return bands

    def main_band_object( self ):
        """
        The image ticked as main in the admin, or the shortest-wavelength one
        the object has if none is ticked.
        """
        bands = self.ordered_bands()
        for band in bands:
            if band.is_main:
                return band
        return bands[0] if bands else None

    def get_zoomable_images( self ):
        """
        Gets the images to show in the zoomable viewer, ordered by wavelength.
        Only images with zoomable tiles are used. Repeated images are not shown.
        The image of the main band is marked as main. If it has no tiles, the
        first image is the main one.
        """
        main = self.main_band_object()
        main_image_id = main.image_id if main is not None else None

        images = []
        seen = set()
        for band in self.ordered_bands():
            if band.image_id in seen or not band.image.resource_zoomable:
                continue
            seen.add( band.image_id )
            images.append( {
                'image': band.image,
                'title': band.title,
                'label': str( band.get_band_display() ),
                'is_main': band.image_id == main_image_id,
            } )

        # The main image has no tiles: use the first image instead.
        has_main = any( image['is_main'] for image in images )
        if images and not has_main:
            images[0]['is_main'] = True

        return images

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
    One observation of a MultiwavelengthImage: the visual shown when the
    visitor picks this point of the spectrum, together with its own title and
    description. The editor types the wavelength of the observation and the
    band is worked out from it, so an object can carry several images of the
    same band. Bands are shared by all translations (see
    MultiwavelengthImageBandTranslation for the translated texts).
    """
    multiwavelength_image = TranslationForeignKey( MultiwavelengthImage,
        related_name='bands', only_sources=True, on_delete=models.CASCADE )
    wavelength = models.FloatField( verbose_name=_('Wavelength (nm)'), db_index=True,
        validators=[MinValueValidator( 1e-6 )], default=550.0,
        help_text=_('Wavelength of the observation in nanometres, e.g. 550 for '
                    'visible light or 1e6 for 1 mm. The band of the spectrum is '
                    'worked out from it.') )
    is_main = models.BooleanField( default=False, verbose_name=_('Main'),
        help_text=_('Shown when the page opens and used as the main visual of the '
                    'object. At most one image per object.') )
    image = TranslationForeignKey( Image, verbose_name=_('Related Image'),
        only_sources=True, on_delete=models.CASCADE )
    title = models.CharField( max_length=255, blank=True )
    description = models.TextField( blank=True )
    caption_align = models.CharField( max_length=5, choices=CaptionAlign.choices,
        default=CaptionAlign.LEFT, help_text=_('Side of the image where the band text is shown') )

    class Meta:
        ordering = ['wavelength']
        verbose_name = _('Wavelength band')
        app_label = 'media'
        constraints = [
            # The admin formset checks this too, so that the editor gets a
            # form error instead of an IntegrityError.
            models.UniqueConstraint( fields=['multiwavelength_image'],
                condition=Q( is_main=True ),
                name='media_mwlband_one_main_per_image' ),
            models.CheckConstraint( check=Q( wavelength__gt=0 ),
                name='media_mwlband_wavelength_positive' ),
        ]

    def __str__( self ):
        return "%s: %s (%.3g nm)" % (
            self.multiwavelength_image_id, self.get_band_display(), self.wavelength or 0 )

    @property
    def band( self ):
        """ The band of the spectrum this wavelength falls into. """
        return band_for_wavelength( self.wavelength )

    def get_band_display( self ):
        """
        Human readable name of the band. `band` is no longer a field with
        choices, so Django does not generate this helper any more, but the
        templates still call it.
        """
        return WAVELENGTH_BAND_LABELS.get( self.band, '' )

    @property
    def frequency( self ):
        """
        The frequency in hertz, from the wavelength. Not a column, so it
        cannot be used in filter() or order_by(): use `wavelength` instead.
        """
        return frequency_for_wavelength( self.wavelength )

    @property
    def frequency_display( self ):
        """ The frequency as the page and the admin show it. """
        return frequency_label( self.frequency )

    @property
    def wavelength_display( self ):
        """ The wavelength as the page and the admin show it. """
        return wavelength_label( self.wavelength )

    @property
    def credit( self ):
        """ Bands don't carry their own credit - use the image's. """
        return self.image.credit


@python_2_unicode_compatible
class MultiwavelengthImageBandTranslation( models.Model ):
    """
    Translated title and description of one MultiwavelengthImageBand.

    Linked to the band row itself, since several images can share a band
    name. Empty values fall back to the source band's text.
    """
    translation = TranslationForeignKey( MultiwavelengthImage,
        related_name='band_translations', only_sources=False, on_delete=models.CASCADE )
    band = models.ForeignKey( 'media.MultiwavelengthImageBand',
        related_name='translations', on_delete=models.CASCADE,
        verbose_name=_('Wavelength band') )
    title = models.CharField( max_length=255, blank=True )
    description = models.TextField( blank=True )

    class Meta:
        unique_together = ( 'translation', 'band' )
        verbose_name = _('Wavelength band translation')
        app_label = 'media'

    def __str__( self ):
        return "%s: %s" % ( self.translation_id, self.band )


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
