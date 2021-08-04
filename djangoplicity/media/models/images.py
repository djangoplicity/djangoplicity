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

from __future__ import division
from builtins import str
from past.utils import old_div
import colorsys
import datetime
import os
import re
import sys
from decimal import Decimal

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.db.models import signals, Q
from django.utils.translation import ugettext_lazy as _, ugettext_noop
from django.utils.encoding import python_2_unicode_compatible

from djangoplicity.archives import fields as archive_fields
from djangoplicity.archives.base import ArchiveModel, post_rename
from djangoplicity.archives.contrib import types
from djangoplicity.archives.resources import ResourceManager, ImageResourceManager
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.archives.utils import FormatTokenGenerator, \
    release_date_change_check
from djangoplicity.contentserver.models import ContentDeliveryModel
from djangoplicity.cutter.models import CropModel
from djangoplicity.media.consts import DEFAULT_CREDIT, IMAGE_AVM_FORMATS
from djangoplicity.media.consts import DEFAULT_CREATOR_FUNC, DEFAULT_CREATOR_URL_FUNC, \
    DEFAULT_CREDIT_FUNC, DEFAULT_CONTACT_ADDRESS_FUNC, DEFAULT_CONTACT_CITY_FUNC, \
    DEFAULT_CONTACT_COUNTRY_FUNC, DEFAULT_CONTACT_POSTAL_CODE_FUNC, \
    DEFAULT_CONTACT_STATE_PROVINCE_FUNC, DEFAULT_PUBLISHER_FUNC, DEFAULT_PUBLISHER_ID_FUNC, \
    DEFAULT_RIGHTS_FUNC
from djangoplicity.media.tasks import (
    write_metadata, image_color, image_extras,
    image_observation_tagging_notification
)

from djangoplicity.media.wcs import wwt_show_image_url
from djangoplicity.metadata.archives import fields as metadatafields
from djangoplicity.metadata.translation import fields as metadatafields_trans
from djangoplicity.metadata.models import Contact, TaggingStatus, Category
from djangoplicity.translation.models import TranslationModel, \
    translation_reverse
from djangoplicity.translation.fields import TranslationForeignKey, \
    TranslationManyToManyField

import django
if django.VERSION >= (2, 0):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse
from djangoplicity.archives.importer.utils import rerun_import_actions
from djangoplicity.archives.loading import get_archive_modeloptions

# #########################################################################
# Colour
# #########################################################################
@python_2_unicode_compatible
class Color( models.Model ):
    """
    Definition of colours and algorithms for computing the dominant colours
    of an image.

    The current most effective algorithm for computing dominant colours
    generates a colour histogram and uses that to select the most
    dominant colours.
    """

    #
    # Cache variables
    #
    _band_cache = None
    _black_cache = None
    _white_cache = None

    id = models.SlugField( primary_key=True, max_length=10 )
    name = models.CharField( max_length=50, help_text=_( "Name of this color" ) )
    upper_limit = models.FloatField( null=True, help_text=_( "Hue value (range 0-1) for the HSV model for the upper boundary of this colour." ) )

    class Meta:
        ordering = ( 'upper_limit', )
        app_label = 'media'

    def save( self, **kwargs ):
        self.__class__._band_cache = None
        self.__class__._bw_cache = None
        super( Color, self ).save( **kwargs )

    def __str__( self ):
        return self.name

    @classmethod
    def bands( cls ):
        """
        Get bands for the defined colours ( e.g blue may be defined for hue values 0.5417 - 0.6667 ).
        """
        if not cls._band_cache:
            cls._band_cache = [x for x in cls.objects.filter( upper_limit__isnull=False ).order_by( 'upper_limit' )]
            if not cls._band_cache:
                defaultbands = [
                    ( 0.0417, 'red', 'Red' ),
                    ( 0.1230, 'orange', 'Orange' ),
                    ( 0.1760, 'yellow', 'Yellow' ),
                    ( 0.4167, 'green', 'Green' ),
                    ( 0.5417, 'cyan', 'Cyan' ),
                    ( 0.6667, 'blue', 'Blue' ),
                    ( 0.7917, 'purple', 'Purple' ),
                    ( 0.9778, 'magenta', 'Magenta' ),
                ]

                for val, pk, name in defaultbands:
                    obj = cls( id=pk, name=name, upper_limit=val )
                    obj.save()
                cls._band_cache = [x for x in cls.objects.filter( upper_limit__isnull=False ).order_by( 'upper_limit' )]

        return cls._band_cache

    @classmethod
    def black( cls ):
        """
        Black and white are not treated as normal colors
        """
        if not cls._black_cache:
            cls._black_cache = cls.objects.get_or_create( id='black', defaults={ 'name': 'Black', 'upper_limit': None} )[0]
        return cls._black_cache

    @classmethod
    def white( cls ):
        """
        Black and white are not treated as normal colors
        """
        if not cls._white_cache:
            cls._white_cache = cls.objects.get_or_create( id='white', defaults={ 'name': 'White', 'upper_limit': None} )[0]
        return cls._white_cache

    @classmethod
    def bins( cls ):
        """
        Similar to bands()
        """
        bands = [( b.upper_limit, b.id ) for b in cls.bands()]
        if bands[-1][0] < 1.0:
            bands.append( ( 1.0, bands[0][1] ) )
        return bands

    @classmethod
    def init_histogram( cls ):
        """
        Initialise a colour histogram
        """
        hist = {}
        for b in cls.bands():
            hist[b.id] = 0
        hist[cls.black().id] = 0
        hist[cls.white().id] = 0
        return hist

    @staticmethod
    def create_dominant_colors( image, resource_attr='resource_thumbs' ):
        """
        Determine the dominant colours of an image.

        The method can use different image resource to compute - e.g. it's
        more effective to compute the dominant colours of a small image
        than a large image.
        """
        resource = getattr( image, resource_attr )
        if resource:
            imfilepath = resource.path
            if imfilepath:
                try:
                    from PIL import Image as PILImage
                    im = PILImage.open( imfilepath )
                    colors = [ImageColor(color_id=c, image=image, ratio=r) for ( c, r ) in Color._dominant_colors_3( im )]
                    return colors
                except ImportError:
                    pass
                except IOError:
                    pass
        return []

    @staticmethod
    def _dominant_color_1( im ):
        """
        Algorithm for find the dominant *colour* of an image.

        Finds the average colour of an image by averaging over all values in each channel.
        Values below a cutoff level is not included, however if more than 95% of the image
        is below a black level then the image is considered black.

        Currently this algorithm doesn't work good, if there's more than one dominant colour
        in the image.
        """
        black_level = 80  # Everything below is considered black
        cutoff_level = 150  # We only count saturated

        # Get pixels and initialise data variables
        pixels = im.getdata()
        r_t, g_t, b_t = ( 0, 0, 0 )
        i = 0
        black = 0

        for r, g, b in pixels:
            if r < cutoff_level and g < cutoff_level and b < cutoff_level:
                if r < black_level and g < black_level and b < black_level:
                    black += 1
                continue

            r_t += r
            g_t += g
            b_t += b
            i += 1

        # Check black - if more than 95% of image is black then return black
        (w, h) = im.size

        if float(black) / (w * h) > 0.95:
            return ( 0, 0, 0 )

        if i > 0:
            return ( old_div(r_t, i), old_div(g_t, i), old_div(b_t, i) )
        return ( 0, 0, 0 )

    @staticmethod
    def _dominant_color_2( im ):
        """
        Like _dominant_color_1, except that no pixel is excluded.
        """
        from PIL import ImageStat
        stat = ImageStat.Stat( im )
        return stat.mean

    @staticmethod
    def _dominant_colors_3( im ):
        """
        Algorithm for find the dominant *colours* of an image.

        Works by:
         * Generate a colour histogram (using the hue and v value of the HSV-model).
           Note, black and white are special cases.
         * Use histogram to determine dominant colours
        """
        # Prepare data
        imrgb = im.convert('RGB')
        pixels = imrgb.getdata()
        bins = Color.bins()
        histogram = Color.init_histogram()

        # Histogram
        for ( r, g, b ) in pixels:
            ( h, s, v ) = colorsys.rgb_to_hsv( r / 256.0, g / 256.0, b / 256.0 )

            if v < 0.25:
                histogram['black'] += 1
            elif s < 0.2 and v > 0.6:
                histogram['white'] += 1
            else:
                for border, name in bins:
                    if h <= border:
                        histogram[name] += 1
                        break

        # Normalise histogram to sum to 1
        total = im.size[0] * im.size[1]
        for col, count in list(histogram.items()):
            histogram[ col ] = float( count ) / total

        #
        # Classify image
        #
        classes = []

        # Astro images have lots of black normally, so ensure that the
        # black images are really very black.
        if histogram['black'] >= 0.9:
            classes.append( ( 'black', histogram['black'] ) )
        if histogram['black'] >= 1.0:
            return classes

        # Determine cut-off ratio.
        cutoff_ratio = old_div(( 1.0 - histogram['black'] ), ( len( histogram ) - 1 ))
        cutoff_ratio = max( cutoff_ratio, 0.02 )  # Ensure ratio is at least 2%
        del histogram['black']

        # Select classes
        for col, ratio in list(histogram.items()):
            if ratio > cutoff_ratio:
                classes.append( ( col, ratio ) )

        return classes


# #########################################################################
# Images
# #########################################################################

class Exposure( models.Model ):
    """
    One exposure (instance) represents data about a single exposure/layer in an
    image.

    The model ensures that each AVM field has the exposures listed in the
    right order, instead of creating semicolon separated fields.
    """
    facility = metadatafields.AVMFacilityField( on_delete=models.CASCADE )
    instrument = metadatafields.AVMInstrumentField( on_delete=models.CASCADE )
    spectral_color_assignment = metadatafields.AVMSpectralColorAssignmentField()
    spectral_band = metadatafields.AVMSpectralBandField()
    spectral_bandpass = metadatafields.AVMSpectralBandpassField()
    spectral_central_wavelength = metadatafields.AVMSpectralCentralWavelengthField()
    temporal_start_time = metadatafields.AVMTemporalStartTimeField()
    temporal_integration_time = metadatafields.AVMTemporalIntegrationTimeField()
    dataset_id = metadatafields.AVMDatasetIDField()

    class Meta:
        abstract = True
        verbose_name = _(u'Exposure')
        app_label = 'media'


@python_2_unicode_compatible
class Image( ArchiveModel, TranslationModel, ContentDeliveryModel, CropModel ):
    """
    Image Archive

    Compliant with AVM Standard v1.1 (http://www.virtualastronomy.org)
    """
    def __init__( self, *args, **kwargs ):
        super( Image, self ).__init__( *args, **kwargs )
        if not self.credit and self.is_source():
            self.credit = DEFAULT_CREDIT

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

    def _get_distance( self ):
        res = ["-", "-"]
        if self.distance_ly:
            res[0] = self.distance_ly
        if self.distance_z:
            res[1] = self.distance_z

        if res != ["-", "-"]:
            return "%s;%s" % ( res[0], res[1] )
        else:
            return None

    def _set_distance( self, value ):
        if value:
            data_list = value.split(';')
            if len( data_list ) > 0:
                try:
                    self.distance_ly = Decimal( data_list[0] )
                except ValueError:
                    self.distance_ly = None
            if len( data_list ) > 1:
                self.distance_z = None if data_list[1] == "-" else str( data_list[1] )

    def get_image_product_quality( self ):
        if self.priority > 60:
            return 'Good'
        elif self.priority > 30:
            return 'Moderate'
        else:
            return 'Poor'

    title = metadatafields.AVMTitleField()
    headline = metadatafields.AVMHeadlineField()
    description = metadatafields.AVMDescriptionField()
    web_category = models.ManyToManyField(Category, limit_choices_to=Q(type__name='Images'), blank=True)
    subject_category = metadatafields_trans.TranslationAVMSubjectCategoryField()
    subject_name = metadatafields_trans.TranslationAVMSubjectNameField()

    distance_ly = metadatafields.AVMDistanceLyField()
    distance_ly_is_accurate = models.BooleanField(default=False, verbose_name=_('Distance in ly is accurate'))
    distance_z = metadatafields.AVMDistanceZField()
    distance = property( _get_distance, _set_distance )
    distance_notes = metadatafields.AVMDistanceNotesField()
    reference_url = property( _get_reference_url )
    credit = metadatafields.AVMCreditField( default=DEFAULT_CREDIT_FUNC )

    # date is release_date
    id = metadatafields.AVMIdField( help_text=_(u'Id of image - used in the URL for the image as well as the filename for the different formats.') )
    type = metadatafields.AVMTypeField()

    image_product_quality = property( get_image_product_quality )

    # Add AVM 1.2 fields
    # - PublicationID (list)
    # - ProposalID (list)

    # ========================================================================
    # Observation Metadata
    # ========================================================================
    # See also "ImageExposure" model which contains the rest of the fields.
    spectral_notes = metadatafields.AVMSpectralNotesField()

    # ========================================================================
    # Coordinate Metadata
    # ========================================================================
    spatial_coordinate_frame = metadatafields.AVMSpatialCoordinateFrameField()
    spatial_equinox = metadatafields.AVMSpatialEquinoxField()
    spatial_reference_value = metadatafields.AVMSpatialReferenceValueField()
    spatial_reference_dimension = metadatafields.AVMSpatialReferenceDimensionField()
    spatial_reference_pixel = metadatafields.AVMSpatialReferencePixelField()
    spatial_scale = metadatafields.AVMSpatialScaleField()
    spatial_rotation = metadatafields.AVMSpatialRotationField()
    spatial_coordsystem_projection = metadatafields.AVMSpatialCoordsystemProjectionField()
    spatial_quality = metadatafields.AVMSpatialQualityField()
    spatial_notes = metadatafields.AVMSpatialNotesField()
    spatial_fits_header = metadatafields.AVMSpatialNotesField()

    def _field_to_python( self, attr ):
        return self.__class__._meta.get_field(attr).from_internal( getattr( self, attr ) )

    def get_spatial_reference_value( self ):
        return self._field_to_python( 'spatial_reference_value' )

    def get_spatial_reference_pixel( self ):
        return self._field_to_python( 'spatial_reference_pixel' )

    def get_spatial_reference_dimension( self ):
        return self._field_to_python( 'spatial_reference_dimension' )

    def get_spatial_scale( self ):
        return self._field_to_python( 'spatial_scale' )

    def get_spatial_scale_float( self, om=True ):
        return [float(x) for x in self._field_to_python( 'spatial_scale' )]

    def get_dec_verbose( self, om=True):
        sr = self.get_spatial_reference_value()
        if not sr:
            return ''
        deg = float(sr[1])
        if deg > 90 or deg < -90:
            return ''
        d = int(deg)
        m = abs(deg - d) * 60
        s = m - int(m)
        m = int(m)
        s = s * 60
        return '%d&deg %d\' %.2f"' % (d, m, s) if om else '%d %d %.2f' % (d, m, s)

    def get_fov_verbose( self ):
        scale = self.get_spatial_scale_float()
        dimension = self.get_spatial_reference_dimension()
        if not scale or len(dimension) != 2 or not dimension[0] or not dimension[1]:
            return ''
        return '%.2f x %.2f arcminutes' % (abs(scale[0]) * float(dimension[0]) * 60,
                abs(scale[1]) * float(dimension[1]) * 60)

    def get_ra_verbose( self, om=False):
        sr = self.get_spatial_reference_value()
        if not sr:
            return ''
        deg = float(sr[0])
        #  Degrees should be in 0..360
        if deg < 0:
            deg += 360
        deg = old_div(deg, 15)
        h = int(deg)
        m = (deg - h) * 60
        s = m - int(m)
        m = int(m)
        s = s * 60
        return '%dh %dm %.2fs' % (h, m, s) if om else '%d %d %.2f' % (h, m, s)

    def get_spatial_rotation_verbose( self ):
        r = float(self.spatial_rotation)
        x = self.get_spatial_scale_float()[0]
        if x < 0 and r < 0:
            direction = _('right')
            r = -r
        elif x < 0 and r >= 0:
            direction = _('left')
        elif x >= 0 and r < 0:
            direction = _('right')
            r = -r
        elif x >= 0 and r >= 0:
            direction = _('left')
        return _('North is %(degree).1f&deg; %(direction)s of vertical') % {'degree': r, 'direction': direction}

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
        try:
            if resource == 'original':
                return "http://%s%s" % (get_current_site(None).domain, self.resource_original.url)
            else:
                attr = "resource_" % resource
                if hasattr(self, attr):
                    return "http://%s%s" % (get_current_site(None).domain, getattr(self, attr).url)
                else:
                    return None
        except AttributeError:
            return None

    publisher = metadatafields.AVMPublisherField( default=DEFAULT_PUBLISHER_FUNC )
    publisher_id = metadatafields.AVMPublisherIdField( default=DEFAULT_PUBLISHER_ID_FUNC )
    metadata_date = property( _get_metadata_date )
    metadata_version = "1.1"

    # ========================================================================
    # File Metadata
    # ========================================================================
    def _get_file_dimension(self):
        return [self.width, self.height]

    width = metadatafields.AVMFileDimensionWidth()
    height = metadatafields.AVMFileDimensionHeight()

    def _fov_x(self):
        if self.fov_x_l and self.fov_x_r:
            return abs(self.fov_x_l) + self.fov_x_r
        else:
            return None

    def _fov_y(self):
        if self.fov_y_u and self.fov_y_d:
            return self.fov_y_u + abs(self.fov_y_d)
        else:
            return None

    fov_x = property(_fov_x)
    fov_y = property(_fov_y)

    fov_x_l = models.DecimalField('FOV x West', max_digits=10, decimal_places=5,
        blank=True, null=True, help_text='Horizontal Field of View (west), in degrees')
    fov_x_r = models.DecimalField('FOV x East', max_digits=10, decimal_places=5,
        blank=True, null=True, help_text='Horizontal Field of View (east), in degrees')
    fov_y_d = models.DecimalField('FOV y Bottom', max_digits=10, decimal_places=5,
        blank=True, null=True, help_text='Vertical Field of View (bottom), in degrees')
    fov_y_u = models.DecimalField('FOV y Top', max_digits=10, decimal_places=5,
        blank=True, null=True, help_text='Vertical Field of View (top), in degrees')

    # We store width * height separately to make it easier to filter
    # on the number of pixels
    n_pixels = models.BigIntegerField(blank=True, null=True)

    file_type = metadatafields.AVMFileType()
    file_dimension = property( _get_file_dimension )
    file_size = metadatafields.AVMFileSize()
    file_bit_depth = None  # TODO: Implement File.BitDepth

    # ========================================================================
    # Resource Display Related Fields
    # ========================================================================
    zoomify = models.BooleanField( verbose_name=ugettext_noop( 'Zoomable' ), default=False )
    wallpapers = models.BooleanField( verbose_name=ugettext_noop( 'Wallpapers' ), default=True )
    print_layout = models.BooleanField( verbose_name=ugettext_noop( 'Print Layout' ), default=False )
    zoomable = models.BooleanField( default=False, verbose_name=_('Use zoomable as main') )

    # TODO: Should be extended to allow locking (i.e not overwriting when generating derivatives)
    # of any format. This should ideally work for all archives (not only image archive). This is
    # tightly connect with the locked_resources function and djangoplicity.archives.importer
    keep_newsfeature = models.BooleanField( verbose_name=ugettext_noop( 'Disable News Feature Auto-Overwite' ), default=False )

    # ========================================================================
    # Additional Fields
    # ========================================================================
    # Field to store the legacy id in - useful during migration
    old_ids = models.CharField( max_length=255 )

    # Some images are imported from sister organisations and needs to reference their press release.
    press_release_link = models.CharField( max_length=255, blank=True, help_text=_( 'External link to non-local press releases.' ) )

    # Some images are imported from sister organisations and needs to reference their corresponding long caption
    # in another image archibe.
    long_caption_link = models.CharField( max_length=255, blank=True, help_text=_( 'External link to a longer image caption located elsewhere.' ) )

    # Magnet link for the bittorrent version of the original format
    magnet_uri = models.CharField( max_length=255, blank=True )

    # ========================================================================
    # Internal status field
    # ========================================================================
    # Status field to indicate the status of the tagged image
    tagging_status = TranslationManyToManyField( TaggingStatus, blank=True, only_sources=True )

    # The dominant colours in the image
    colors = TranslationManyToManyField( Color, through='ImageColor', verbose_name=_( "Colours" ), only_sources=True )

    # ========================================================================
    # Python/Django specific methods
    # ========================================================================
    def save(self, *args, **kwargs ):
        """
        Overrides default save method to determine image size of original file.
        """
        # Consume argument
        if 'run_tasks' in kwargs:
            run_tasks = kwargs['run_tasks']
            del kwargs['run_tasks']
        else:
            run_tasks = True

        # In some cases where 'created' was not set upon creation the save
        # will fail so we manually set it
        if not self.created:  # pylint: disable=E0203
            self.created = datetime.datetime.today()

        super( Image, self ).save( *args, **kwargs )

        # Run background tasks on image
        if run_tasks and self.is_source() and 'loaddata' not in sys.argv:
            image_extras.delay( self.id )
            image_color.delay( self.id )
            write_metadata.delay( self.id, IMAGE_AVM_FORMATS )

    def reimport_resources(self, user=None):
        model, options = get_archive_modeloptions(self._meta.app_label, self._meta.model_name)
        if options.Import.actions and model:
            if user:
                extra_conf = {'user_id': user.pk}
            else:
                extra_conf = {}
            rerun_import_actions(model, options, self, extra_conf=extra_conf)

    def get_absolute_url(self):
        return translation_reverse( 'images_detail', args=[str( self.id if self.is_source() else self.source.id )], lang=self.lang )

    def __str__( self ):
        return self.title

    @classmethod
    def observation_tagging_notification(cls, sender, instance, raw=False, **kwargs):
        '''
        Send an email notification if the image is marked as Observation
        This is done in a background task as the tagging status are not yet
        stored to the DB when the pre_save run
        '''
        if raw:
            return

        if instance.type != 'Observation':
            return

        # Check if the type has just been set
        try:
            old = sender.objects.get(pk=instance.pk)
            if old.type == instance.type:
                return
        except sender.DoesNotExist:
            pass

        image_observation_tagging_notification.apply_async([instance.pk],
            countdown=300)

    # ========================================================================
    # Djangoplicity archives methods
    # ========================================================================
    def locked_resources(self):
        """
        List of resources that should not be overwritten (usually they have been manually generated).
        """
        if self.keep_newsfeature:
            return ['banner1920', 'newsfeature', 'potwmedium', 'thumb350x']
        else:
            return []

    # ========================================================================
    # Image specific methods
    # ========================================================================
    def get_wwt_url(self):
        """
        Get URL for showing image in Microsoft WorldWide Telescope
        """
        return wwt_show_image_url(self)

    def get_aladinlite_params(self):
        """
        Return a dictionnary of parameters for the Aladin Lite API
        So far only the target name
        """
        params = {}

        subject_name = self.subject_name.all()[:1]
        if len(subject_name) > 0:
            params['target'] = subject_name[0].name
        else:
            title = self.title
            MAX_LEN = 40
            if len(title) > MAX_LEN:
                title = "%s..." % title[:MAX_LEN - 3]
            params['target'] = title

    # ========================================================================
    # Methods for generating "passthrough URL" for static protected images.
    #
    # Needed to allow e.g. HTML newsletters to include links to embargoed images.
    # ========================================================================
    def get_PASSTHROUGH_image_url( self, fmt ):
        """
        """
        res = getattr( self, "resource_%s" % fmt )
        if res:
            token = FormatTokenGenerator.create_token( fmt, self.id )
            ( _tail, ext ) = os.path.splitext( res.path )
            if len( ext ) > 1:
                ext = ext[1:]

            return reverse( 'images_passthrough', args=[token, fmt, self.id, ext] )
        return None

    def get_PASSTHROUGH_image_token( self, fmt ):
        """
        """
        token = FormatTokenGenerator.create_token( fmt, self.id )
        return token

    def __getattr__( self, name ):
        """
        Catches access to attributes e.g. im.screen_image_url or im.large_image_token
        and directs it to the two above methods which will compute the value.
        """
        m = re.match( '([a-z0-9]+)_image_url', name )
        if m:
            return self.get_PASSTHROUGH_image_url( m.group(1) )
        else:
            m = re.match( '([a-z0-9]+)_image_token', name )
            if m:
                return self.get_PASSTHROUGH_image_token( m.group(1) )
        raise AttributeError

    # ========================================================================
    # Classes
    # ========================================================================
    class Meta:
        ordering = ['-priority', '-release_date']
        app_label = 'media'
        permissions = [
            ( "view_only_non_default", "Can view only non default language" ),
            ( "view_released_images_only", "Can view only released images" ),
        ]

    class Translation:
        fields = ['title', 'headline', 'description', ]
        excludes = ['published', 'last_modified', 'created']

    class Archive:
        original = ImageResourceManager(type=types.OriginalImageType)
        publicationtiff40k = ImageResourceManager(derived='original', type=types.PublicationTiff40KType)
        publicationtiff25k = ImageResourceManager(derived='publicationtiff40k', type=types.PublicationTiff25KType)
        publicationtiff10k = ImageResourceManager(derived='publicationtiff25k', type=types.PublicationTiff10KType)
        publicationtiff = ImageResourceManager(derived='original', type=types.PublicationTiffType)
        large = ImageResourceManager(derived='original', type=types.LargeJpegType)
        publicationjpg = ImageResourceManager(derived='publicationtiff', type=types.PublicationJpegType)
        screen = ImageResourceManager(derived='publicationtiff', type=types.ScreensizeJpegType)
        wallpaper1 = ImageResourceManager(derived='publicationtiff', type=types.Wallpaper1Type)
        wallpaper2 = ImageResourceManager(derived='publicationtiff', type=types.Wallpaper2Type)
        wallpaper3 = ImageResourceManager(derived='publicationtiff', type=types.Wallpaper3Type)
        wallpaper4 = ImageResourceManager(derived='publicationtiff', type=types.Wallpaper4Type)
        wallpaper5 = ImageResourceManager(derived='publicationtiff', type=types.Wallpaper5Type)
        news = ImageResourceManager(derived='publicationtiff', type=types.NewsJpegType)
        newsmini = ImageResourceManager(derived='publicationtiff', type=types.NewsMiniJpegType)
        newsfeature = ImageResourceManager(derived='publicationtiff', type=types.NewsFeatureType)
        medium = ImageResourceManager(derived='publicationtiff', type=types.MediumJpegType)
        wallpaperthumbs = ImageResourceManager(derived='publicationtiff', type=types.WallpaperThumbnailType)
        potwmedium = ImageResourceManager(derived='publicationtiff', type=types.POTWMediumThumbnailJpegType)
        thumb150y = ImageResourceManager(derived='publicationtiff', type=types.Thumb150yType)
        thumb300y = ImageResourceManager(derived='publicationtiff', type=types.Thumb300yType)
        thumb350x = ImageResourceManager(derived='publicationtiff', type=types.Thumb350xType)
        thumb700x = ImageResourceManager(derived='publicationtiff', type=types.Thumb700xType)
        thumbs = ImageResourceManager(derived='publicationtiff', type=types.ThumbnailJpegType)
        banner1920 = ImageResourceManager(derived='publicationtiff', type=types.Banner1920Type)
        zoomable = ImageResourceManager(derived='original', type=types.ZoomableType)
        screen640 = ImageResourceManager(derived='publicationtiff', type=types.Screen640Type)
        portrait1080 = ImageResourceManager(derived='publicationtiff', type=types.Portrait1080Type)
        poster400y = ImageResourceManager(derived='publicationtiff', type=types.Poster400yType)

        pl_original = ImageResourceManager(type=types.OriginalImageType)
        pl_screen = ImageResourceManager(derived='pl_original', type=types.ScreensizeJpegType)
        pl_thumbs = ImageResourceManager(derived='pl_original', type=types.ThumbnailJpegType)

        eps = ResourceManager(type=types.EpsType)
        pdf = ResourceManager(verbose_name=_('PDF File'), type=types.PDFType)
        illustrator = ResourceManager(type=types.IllustratorType)
        illustrator_text = ResourceManager(type=types.IllustratorType, verbose_name=_('Illustrator File (traced text)'))

        class Meta:
            root = settings.IMAGES_ARCHIVE_ROOT
            release_date = True
            embargo_date = True
            release_date_owner = True
            last_modified = True
            created = True
            published = True
            rename_pk = ('media_image', 'id')
            rename_fks = (
                ('announcements_announcementimage', 'archive_item_id'),
                ('events_event', 'image_id'),
                ('feeds_postimage', 'archive_item_id'),
                ('internal_internalannouncementpublicimage', 'archive_item_id'),
                ('media_imagecolor', 'image_id'),
                ('media_imagecomparison', 'image_after_id'),
                ('media_imagecomparison', 'image_before_id'),
                ('media_imagecontact', 'image_id'),
                ('media_imageexposure', 'image_id'),
                ('media_image', 'source_id'),
                ('media_image_subject_category', 'image_id'),
                ('media_image_subject_name', 'image_id'),
                ('media_image_tagging_status', 'image_id'),
                ('media_image_web_category', 'image_id'),
                ('media_pictureoftheweek', 'image_id'),
                ('products_mountedimage', 'image_id'),
                ('products_visit', 'image_id'),
                ('programme_activity', 'key_visual_hori_de_id'),
                ('programme_activity', 'key_visual_hori_en_id'),
                ('programme_activity', 'poster_de_id'),
                ('programme_activity', 'poster_en_id'),
                ('releases_release', 'kids_image_id'),
                ('releases_releaseimage', 'archive_item_id'),
                ('releases_releasestockimage', 'archive_item_id'),
                ('science_scienceannouncementimage', 'archive_item_id'),
                ('blog_post', 'banner_id'),
            )
            sort_fields = ['last_modified', 'release_date', 'priority', 'file_size', 'distance_ly']
            crop_display_format = 'thumb300y'
            clean_html_fields = ['description', 'credit']


# ========================================================================
# Related Image models
# ========================================================================
@python_2_unicode_compatible
class ImageColor( models.Model ):
    """
    Stores a dominant colour for an image (computed by Color model).
    """
    color = models.ForeignKey( Color, on_delete=models.CASCADE )
    image = TranslationForeignKey( Image, only_sources=True, on_delete=models.CASCADE )
    ratio = models.FloatField()

    def __str__( self ):
        return "%s: %s (%s)" % ( self.image.id, self.color.name, self.ratio )

    class Meta:
        app_label = 'media'


class ImageExposure( Exposure ):
    """
    Links the exposure model with images
    """
    image = TranslationForeignKey( Image, only_sources=True, on_delete=models.CASCADE )

    class Meta:
        verbose_name = _(u'Exposure')
        app_label = 'media'


class ImageContact( Contact ):
    """
    Links contacts with images
    """
    image = TranslationForeignKey( Image, only_sources=True, on_delete=models.CASCADE )

    class Meta:
        verbose_name = _(u'Contact')
        app_label = 'media'


# ========================================================================
# Translation proxy model
# ========================================================================

class ImageProxy( Image, TranslationProxyMixin ):
    """
    Image proxy model for creating admin only to edit
    translated objects.
    """
    objects = Image.translation_objects

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
        verbose_name = _('Image translation')
        app_label = 'media'

    class Archive:
        class Meta:
            rename_pk = ('media_image', 'id')
            rename_fks = (
                ( 'media_image', 'source_id'),
                ( 'media_image_subject_category', 'image_id' ),
                ( 'media_image_subject_name', 'image_id' ),
                ( 'media_image_tagging_status', 'image_id' ),
                ( 'media_imagecontact', 'image_id' ),
                ( 'media_imageexposure', 'image_id' ),
                ( 'media_pictureoftheweek', 'image_id' ),
                ( 'releases_releaseimage', 'archive_item_id' ),
                ( 'announcements_announcementimage', 'archive_item_id' ),
                ( 'media_imagecolor', 'image_id' ),
                ( 'products_mountedimage', 'image_id' ),
                ( 'releases_releasestockimage', 'archive_item_id' ),
                ( 'media_imagecomparison', 'image_before_id' ),
                ( 'media_imagecomparison', 'image_after_id' ),
            )
            clean_html_fields = ['description', 'credit']


# Send notification email when translation_ready is changed to True
signals.pre_save.connect( ImageProxy.send_notification_mail, sender=ImageProxy )

# Observation image notification
signals.pre_save.connect(Image.observation_tagging_notification, sender=Image)

# Connect signal to check for changes in Content server
signals.pre_save.connect(Image.content_server_changed, sender=Image)
signals.post_save.connect(Image.sync_archive_to_content_server, sender=Image)

signals.pre_save.connect( release_date_change_check, sender=Image )

post_rename.connect(Image.sync_archive_on_rename, sender=Image)
