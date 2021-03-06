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

from rest_framework import serializers

from djangoplicity.archives.utils import get_instance_resources
from djangoplicity.products.models import Model3d, Music
from djangoplicity.utils.datetimes import timezone
from djangoplicity.utils.d2d import D2dDict
from djangoplicity.utils.templatetags.djangoplicity_text_utils import \
    remove_html_tags


class ProductSerializer(serializers.ModelSerializer):
    assets = serializers.SerializerMethodField()
    credit = serializers.SerializerMethodField()
    release_date = serializers.SerializerMethodField()

    def get_credit(self, obj):
        '''
        Strip HTML from credit
        '''
        return remove_html_tags(obj.credit)

    def get_release_date(self, obj):
        return timezone(obj.release_date, 'UTC')


class Model3dSerializer(ProductSerializer):
    class Meta:
        model = Model3d
        fields = (
            'id', 'title', 'description', 'credit', 'priority',
            'release_date', 'assets'
        )

    def get_assets(self, obj):
        asset = D2dDict([
            ('MediaType', 'Model'),
            ('Resources', get_instance_resources(obj)),
        ])

        return [asset]


class MusicSerializer(ProductSerializer):
    class Meta:
        model = Music
        fields = (
            'id', 'title', 'description', 'credit', 'priority',
            'release_date', 'assets'
        )

    def get_assets(self, obj):
        asset = D2dDict([
            ('MediaType', 'Audio'),
            ('Resources', get_instance_resources(obj)),
        ])

        return [asset]
