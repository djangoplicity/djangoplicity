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

from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from djangoplicity.media.d2d.renderers import AVMJSONRenderer
from djangoplicity.media.d2d.serializers import ImageSerializer, VideoSerializer
from djangoplicity.media.models import Image, Video
from djangoplicity.media.options import ImageOptions, VideoOptions
from djangoplicity.utils.d2d import D2dDict, string_to_date


class BasePagination(PageNumberPagination):
    page_size_query_param = 'count'
    page_size = 100

    def get_paginated_response(self, data):
        '''
        Override to add custom feed values
        '''
        return Response(D2dDict([
            ('Count', self.page.paginator.count),
            ('Next', self.get_next_link()),
            ('Previous', self.get_previous_link()),
            ('Collections', data)
        ]))


class ImagePagination(BasePagination):
    feed_type = 'Images'


class VideoPagination(BasePagination):
    feed_type = 'Videos'


class D2dImageList(ListAPIView):
    serializer_class = ImageSerializer
    pagination_class = ImagePagination
    renderer_classes = (AVMJSONRenderer, )

    def get_queryset(self):
        qs = ImageOptions.Queries.default.queryset(Image, ImageOptions, None)[0]

        qs = (
            qs.order_by('-release_date')
            .prefetch_related(
                'imagecontact_set', 'imageexposure_set', 'subject_category',
                'subject_name', 'web_category', 'imageexposure_set__facility',
                'imageexposure_set__instrument'
            )
        )

        # Filter for after/before parameters
        before = string_to_date(self.request.query_params.get('before', None))
        after = string_to_date(self.request.query_params.get('after', None))

        if before:
            qs = qs.filter(release_date__lte=before)

        if after:
            qs = qs.filter(release_date__gte=after)

        return qs


class D2dVideoList(ListAPIView):
    serializer_class = VideoSerializer
    pagination_class = VideoPagination
    renderer_classes = (AVMJSONRenderer, )

    def get_queryset(self):
        qs = VideoOptions.Queries.default.queryset(Video, VideoOptions, None)

        return qs[0].order_by('-release_date').prefetch_related(
            'subject_category', 'subject_name', 'web_category', 'facility')
