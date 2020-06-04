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

from djangoplicity.archives.contrib.serialization import SimpleSerializer, \
    Serializer, Serialization
from djangoplicity.archives.utils import get_instance_archives_urls, \
    get_instance_resources
from djangoplicity.media.models import Image, ImageContact, ImageExposure
from djangoplicity.media.wcs import prepare_str


class AVMImageSerializer( Serializer ):
    def serialize_list( self, objects ):
        """
        Serialise list of image objects, but making some
        query optimisations.
        """
        datalist = []
        pks = [obj.pk for obj in objects]

        #objects = objects.select_related()

        related_cache = {}
        related_cache['imagecontact_set'] = [(obj.image_id, obj) for obj in ImageContact.objects.filter( image__in=pks )]
        related_cache['imageexposure_set'] = [(obj.image_id, obj) for obj in ImageExposure.objects.filter( image__in=pks ).select_related('instrument', 'facility')]
        related_cache['subject_name'] = [(obj.image_id, obj.subjectname) for obj in Image.subject_name.through.objects.filter( image__in=pks ).select_related('subjectname')]
        related_cache['subject_category'] = [(obj.image_id, obj.taxonomyhierarchy) for obj in Image.subject_category.through.objects.exclude( taxonomyhierarchy__top_level='X' ).filter( image__in=pks ).select_related('taxonomyhierarchy')]

        for obj in objects:
            datalist.append( self.serialize( obj, related_cache=related_cache ).data )
        return Serialization( datalist )

    def serialize( self, image, related_cache=None ):
        """
        Serialise image object
        """
        data = {}

        def cached_objects( qs, key ):
            if related_cache and key in related_cache:
                return [obj for (pk, obj) in related_cache[key] if pk == image.id]
            else:
                return qs

        def field_to_python( obj, attr ):
            return obj.__class__._meta.get_field(attr).from_internal( getattr( obj, attr ) )

        def include_related( objs, mapping ):
            d = {}
            for obj in objs:
                for field, tag in mapping.items():
                    try:
                        val = d[tag]
                    except KeyError:
                        val = []

                    attrval = getattr( obj, field )
                    if callable( attrval ):
                        attrval = attrval()

                    val.append( attrval )
                    d[tag] = val

            return d

        #
        # Creator Metadata
        #
        data.update( { 'Creator': image.creator } )
        data.update( { 'CreatorURL': image.creator_url } )
        data.update(
                    include_related( cached_objects( image.imagecontact_set.all(), 'imagecontact_set' ),
                    {
                        'contact_name': 'Contact.Name',
                        'contact_email': 'Contact.Email',
                        'contact_telephone': 'Contact.Telephone'
                    } ) )
        data.update( { 'Contact.Address': prepare_str( image.contact_address ) } )
        data.update( { 'Contact.City': prepare_str( image.contact_city ) } )
        data.update( { 'Contact.StateProvince': prepare_str( image.contact_state_province ) } )
        data.update( { 'Contact.PostalCode': prepare_str( image.contact_postal_code ) } )
        data.update( { 'Contact.Country': prepare_str( image.contact_country) } )
        data.update( { 'Rights': prepare_str(image.rights) } )

        #
        # Content Metadata
        #
        data.update( { 'Title': prepare_str( image.title ) } )
        data.update( { 'Headline': prepare_str( image.headline ) } )
        data.update( { 'Description': prepare_str( image.description, html=True ) } )
        data.update( include_related( cached_objects( image.subject_category.exclude( top_level='X' ), 'subject_category' ), { 'avm_code': 'Subject.Category' } ) )
        data.update( include_related( cached_objects( image.subject_name.all(), 'subject_name'), { 'name': 'Subject.Name' } ) )
        data.update( { 'Distance': [image.distance_ly, image.distance_z] } )
        data.update( { 'Distance.Notes': prepare_str( image.distance_notes ) } )
        data.update( { 'ReferenceURL': image.reference_url } )
        data.update( { 'Credit': prepare_str( image.credit, html=True ) } )
        data.update( { 'Date': image.release_date } )
        data.update( { 'ID': image.id } )
        data.update( { 'Type': image.type } )
        #serializer.add( { 'Image.ProductQuality': image.image_productquality } )

        #
        # Observation Metadata
        #
        data.update( include_related(
                cached_objects( image.imageexposure_set.all(), 'imageexposure_set' ),
                {
                    'facility': 'Facility',
                    'instrument': 'Instrument',
                    'spectral_color_assignment': 'Spectral.ColorAssignment',
                    'spectral_band': 'Spectral.Band',
                    'spectral_bandpass': 'Spectral.Bandpass',
                    'spectral_central_wavelength': 'Spectral.CentralWavelength',
                    'temporal_start_time': 'Temporal.StartTime',
                    'temporal_integration_time': 'Temporal.IntegrationTime',
                    'dataset_id': 'DatasetID',
                }
            ) )

        data.update( { 'Spectral.Notes': prepare_str( image.spectral_notes ) } )

        #
        # Coordinate Metadata
        #
        data.update( { 'Spatial.CoordinateFrame': image.spatial_coordinate_frame } )
        data.update( { 'Spatial.Equinox': image.spatial_equinox } )
        data.update( { 'Spatial.ReferenceValue': field_to_python( image, 'spatial_reference_value' ) } )
        data.update( { 'Spatial.ReferenceDimension': field_to_python( image, 'spatial_reference_dimension' ) } )
        data.update( { 'Spatial.ReferencePixel': field_to_python( image, 'spatial_reference_pixel' ) } )
        data.update( { 'Spatial.Scale': field_to_python( image, 'spatial_scale' ) } )
        data.update( { 'Spatial.Rotation': image.spatial_rotation } )
        data.update( { 'Spatial.CoordsystemProjection': image.spatial_coordsystem_projection } )
        data.update( { 'Spatial.Quality': image.spatial_quality } )
        data.update( { 'Spatial.Notes': prepare_str( image.spatial_notes ) } )

        #
        # Publisher Metadata
        #
        data.update( { 'Publisher': image.publisher } )
        data.update( { 'PublisherID': image.publisher_id } )
        data.update( { 'ResourceID': image.resource_id() } )
        data.update( { 'ResourceURL': image.resource_url() } )
        data.update( { 'MetadataDate': image.metadata_date } )
        data.update( { 'MetadataVersion': image.metadata_version } )

        # Formats:
        data.update({'formats_url': get_instance_archives_urls(image)})
        data.update({'Resources': get_instance_resources(image)})

        return Serialization( data )


class VideoSerializer( SimpleSerializer ):
    fields = (
        'id',
        'lang',
        'release_date',
        'title',
        'headline',
        'description',
        'credit',
        'width',
        'height',
    )

    def serialize(self, obj):
        data = super(VideoSerializer, self).serialize(obj).data
        data.update({'ReferenceURL': obj.reference_url})
        data.update({'formats_url': get_instance_archives_urls(obj)})

        # Formats:
        data.update({'Resources': get_instance_resources(obj)})

        return Serialization( data )


class PictureOfTheWeekSerializer( SimpleSerializer ):
    fields = (
        'id',
        'release_date',
        'title',
        'description',
        'image',
        'video',
        'comparison',
        'lang',
    )

    def get_title_value( self, obj ):
        try:
            return obj.visual().title
        except Exception:
            return ""

    def get_description_value( self, obj ):
        try:
            return obj.visual().description
        except Exception:
            return ""

    def get_image_value( self, obj ):
        if obj.image:
            return obj.image.id
        else:
            return None

    def get_comparison_value( self, obj ):
        if obj.comparison:
            return obj.comparison.id
        else:
            return None

    def get_video_value( self, obj ):
        if obj.video:
            return obj.video.id
        else:
            return None

    def serialize(self, obj):
        data = super(PictureOfTheWeekSerializer, self).serialize(obj).data
        archive = obj.image or obj.video or obj.comparison or None
        if archive:
            data.update({'formats_url': get_instance_archives_urls(archive)})

        return Serialization( data )


class ICalPictureOfTheWeekSerializer( SimpleSerializer ):
    fields = (
        'summary',
        'description',
        'dtstart',
        'dtend',
        'dtstamp',
    )

    def get_summary_value( self, obj ):
        return "ESO Picture Of The Week %s - %s" % ( obj.id, obj.visual().title )

    def get_description_value( self, obj ):
        return obj.visual().description

    def get_dtstart_value( self, obj ):
        return obj.release_date

    def get_dtend_value( self, obj ):
        return obj.release_date

    def get_dtstamp_value( self, obj ):
        return obj.release_date


class ImageComparisonSerializer( SimpleSerializer ):
    fields = (
        'id',
        'release_date',
        'title',
        'description',
        'lang',
        'image_before',
        'image_after',
    )

    def get_image_before_value( self, obj ):
        return obj.image_before.id if obj.image_before else None

    def get_image_after_value( self, obj ):
        return obj.image_after.id if obj.image_after else None


class ICalImageComparisonSerializer( SimpleSerializer ):
    fields = (
        'summary',
        'description',
        'dtstart',
        'dtend',
        'dtstamp',
    )

    def get_summary_value( self, obj ):
        return "Image Comparison %s - %s" % (obj.id, obj.title)

    def get_dtstart_value( self, obj ):
        return obj.release_date

    def get_dtend_value( self, obj ):
        return obj.release_date

    def get_dtstamp_value( self, obj ):
        return obj.release_date


class MiniImageSerializer( SimpleSerializer ):
    fields = (
        'id',
        'lang',
        'title',
        'headline',
        'release_date',
    )

    related_fields = (
        'subject_category',
        'subject_name',
    )

    related_cache = (
    )

    def get_release_date_value( self, obj ):
        return self.append_timezone( obj.release_date )
