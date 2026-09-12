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

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from six import python_2_unicode_compatible

from djangoplicity.archives import fields as archive_fields
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.media.models.images import Image
from djangoplicity.metadata.archives import fields as metadatafields
from djangoplicity.translation.models import TranslationForeignKey


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
class MultiwavelengthImage( ArchiveModel, models.Model ):
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
            clean_html_fields = ['description', 'credit']

    class Meta:
        ordering = ['-priority', '-release_date']
        verbose_name = _('Multiwavelength Image')
        app_label = 'media'

    def __str__( self ):
        return self.id

    def get_absolute_url( self ):
        return reverse( 'multiwavelength_detail', args=[str( self.id )] )

    @property
    def main_visual( self ):
        """
        {% opengraph_image %} expects a main_visual attribute. Use the first
        band's image.
        """
        band = self.bands.first()
        return band.image if band else None


@python_2_unicode_compatible
class MultiwavelengthImageBand( models.Model ):
    """
    One wavelength view of a MultiwavelengthImage: the visual shown when the
    visitor selects this band, together with its own title and description.
    """
    multiwavelength_image = models.ForeignKey( MultiwavelengthImage,
        related_name='bands', on_delete=models.CASCADE )
    band = models.CharField( max_length=16, choices=WAVELENGTH_BAND_CHOICES,
        db_index=True )
    image = TranslationForeignKey( Image, verbose_name=_('Related Image'),
        only_sources=True, on_delete=models.CASCADE )
    title = models.CharField( max_length=255, blank=True )
    description = models.TextField( blank=True )
    order = models.PositiveSmallIntegerField( default=0,
        help_text=_('Position of the band on the spectrum bar') )

    class Meta:
        ordering = ( 'order', )
        unique_together = ( 'multiwavelength_image', 'band' )
        verbose_name = _('Wavelength band')
        app_label = 'media'

    def __str__( self ):
        return "%s: %s" % ( self.multiwavelength_image_id, self.get_band_display() )

    @property
    def credit( self ):
        """ Bands don't carry their own credit - use the image's. """
        return self.image.credit
