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

from rest_framework import serializers

from djangoplicity.archives.utils import get_instance_resources
from djangoplicity.media.models import Image, Video
from djangoplicity.utils.d2d import D2dDict
from djangoplicity.utils.datetimes import timezone
from djangoplicity.utils.templatetags.djangoplicity_text_utils import \
    remove_html_tags


class AVMSerializer(serializers.ModelSerializer):
    assets = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    credit = serializers.SerializerMethodField()
    dimension = serializers.SerializerMethodField()
    release_date = serializers.SerializerMethodField()
    spatial_reference_value = serializers.SerializerMethodField()
    spatial_reference_dimension = serializers.SerializerMethodField()
    spatial_reference_pixel = serializers.SerializerMethodField()
    spatial_scale = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    web_category = serializers.StringRelatedField(many=True)

    def get_contact(self, obj):
        return D2dDict([
            ('Address', obj.contact_address),
            ('City', obj.contact_city),
            ('Country', obj.contact_country),
            ('PostalCode', obj.contact_postal_code),
            ('StateProvince', obj.contact_state_province),
        ])

    def get_subject(self, obj):
        return D2dDict([
            ('Category', [c.name for c in obj.subject_category.all()]),
            ('Name', [s.name for s in obj.subject_name.all()]),
        ])

    def get_dimension(self, obj):
        return obj.file_dimension

    def get_release_date(self, obj):
        return timezone(obj.release_date, 'UTC')

    def get_spatial_scale(self, obj):
        return obj.get_spatial_scale()

    def get_spatial_reference_pixel(self, obj):
        return obj.get_spatial_reference_pixel()

    def get_spatial_reference_value(self, obj):
        return obj.get_spatial_reference_value()

    def get_spatial_reference_dimension(self, obj):
        return obj.get_spatial_reference_dimension()

    def get_credit(self, obj):
        '''
        Strip HTML from credit
        '''
        return remove_html_tags(obj.credit)


class ImageSerializer(AVMSerializer):
    class Meta:
        model = Image
        fields = (
            'creator', 'creator_url', 'contact', 'id', 'title', 'description',
            'credit', 'release_date', 'subject', 'reference_url', 'rights',
            'priority', 'assets'
        )

    def get_assets(self, obj):
        '''
        Images return a single Image asset
        '''
        exposures = obj.imageexposure_set.all()

        def get_float(value):
            try:
                return float(value)
            except:  # pylint: disable=bare-except
                return None

        def get_int(value):
            try:
                return int(value)
            except:  # pylint: disable=bare-except
                return None

        def s_to_f(array):
            '''
            Convert an array of strings to an array of float
            Invalid values are returned as None
            '''
            return [get_float(x) for x in array]

        def s_to_i(array):
            '''
            Convert an array of strings to an array of int
            Invalid values are returned as None
            '''
            return [get_int(x) for x in array]

        observation = None
        if obj.type == 'Observation':
            observation = D2dDict([
                ('Facility', [e.facility.name for e in exposures if e.facility]),
                ('Instrument', [e.instrument.name for e in exposures if e.instrument]),
                ('Distance', [obj.distance_ly, obj.distance_z]),
                ('DistanceNotes', obj.distance_notes),
                ('Spectral', D2dDict([
                    ('ColorAssignment', [e.spectral_color_assignment for e in exposures]),
                    ('Band', [e.spectral_bandpass for e in exposures]),
                    ('Bandpass', [e.spectral_bandpass for e in exposures]),
                    ('CentralWavelength', s_to_i(
                        [e.spectral_central_wavelength for e in exposures]
                    )),
                ])),
                ('Temporal', D2dDict([
                    ('StartTime', [e.temporal_start_time for e in exposures]),
                    ('IntegrationTime', s_to_i(
                        [e.temporal_integration_time for e in exposures]
                    )),
                ])),
                ('Spatial', D2dDict([
                    ('CoordinateFrame', obj.spatial_coordinate_frame),
                    ('ReferenceValue', s_to_f(obj.get_spatial_reference_value())),
                    ('ReferenceDimension', s_to_f(obj.get_spatial_reference_dimension())),
                    ('ReferencePixel', s_to_f(obj.get_spatial_reference_pixel())),
                    ('Scale', s_to_f(obj.get_spatial_scale())),
                    ('Rotation', get_float(obj.spatial_rotation)),
                    ('CoordsystemProjection', obj.spatial_coordsystem_projection),
                    ('Equinox', obj.spatial_equinox),
                ])),
            ])

        asset = D2dDict([
            ('MediaType', 'Image'),
            ('Resources', get_instance_resources(obj)),
            ('ObservationData', observation),
        ])

        return [asset]


class VideoSerializer(AVMSerializer):
    class Meta:
        model = Video
        fields = (
            'creator', 'creator_url', 'contact', 'id', 'title', 'description',
            'credit', 'release_date', 'subject', 'reference_url', 'rights',
            'priority', 'assets',
        )

    def get_contact_name(self, obj):
        return obj.videocontact_set.order_by('id').values_list(
            'name', flat=True)

    def get_contact_email(self, obj):
        return obj.videocontact_set.order_by('id').values_list(
            'email', flat=True)

    def get_contact_phone(self, obj):
        return obj.videocontact_set.order_by('id').values_list(
            'telephone', flat=True)

    def get_assets(self, obj):
        asset = D2dDict([
            ('MediaType', 'Video'),
            ('Resources', get_instance_resources(obj)),
        ])

        return [asset]
