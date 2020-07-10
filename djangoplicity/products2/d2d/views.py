# -*- coding: utf-8 -*-
#
# djangoplicity-products
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

from djangoplicity.products2.d2d.renderers import ProductJSONRenderer
from djangoplicity.products2.d2d.serializers import Model3dSerializer, \
    MusicSerializer
from djangoplicity.products2.models import Model3d, Music
from djangoplicity.products2.options import Model3dOptions, MusicOptions
from djangoplicity.utils.d2d import D2dDict


class BasePagination(PageNumberPagination):
    page_size_query_param = 'count'
    page_size = 100

    def get_paginated_response(self, data):
        '''
        Override to add "type" to feed
        '''
        return Response(D2dDict([
            ('Type', self.feed_type),
            ('Count', self.page.paginator.count),
            ('Next', self.get_next_link()),
            ('Previous', self.get_previous_link()),
            ('Collections', data)
        ]))


class Model3dPagination(BasePagination):
    feed_type = '3D models'


class MusicPagination(BasePagination):
    feed_type = 'Music'


class D2dModel3dList(ListAPIView):
    serializer_class = Model3dSerializer
    pagination_class = Model3dPagination
    renderer_classes = (ProductJSONRenderer, )

    def get_queryset(self):
        qs = Model3dOptions.Queries.default.queryset(Model3d, Model3dOptions, None)

        return qs[0].order_by('-last_modified')


class D2dMusicList(ListAPIView):
    serializer_class = MusicSerializer
    pagination_class = MusicPagination
    renderer_classes = (ProductJSONRenderer, )

    def get_queryset(self):
        qs = MusicOptions.Queries.default.queryset(Music, MusicOptions, None)

        return qs[0].order_by('-last_modified')
