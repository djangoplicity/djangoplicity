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

from django.test import TestCase
from djangoplicity.media.options import ImageOptions, VideoOptions, \
    PictureOfTheWeekOptions, ImageComparisonOptions


class CommonViewsTestCase( TestCase ):
    fixtures = [
            'metadata_testdata.json',
    ]
    urls = 'djangoplicity.media.tests.urls'

    conf = {
        'images': {
            'root': '/images/',
            'options': ImageOptions,
            'list_views': [
                ( 'category', 'stars/', 200 ),
                ( 'top100', '', 200 ),
                ( 'bestof', '', 200 ),
                ( 'zoomable', '', 200 ),
                ( 'wallpapers', '', 200 ),
                ( 'print_layouts', '', 200 ),
            ],
        },
        'videos': {
            'root': '/videos/',
            'options': VideoOptions,
            'list_views': [
                ( 'category', 'esocast/', 200 ),
            ],
        },
        'comparisons': {
            'root': '/images/comparisons/',
            'options': ImageComparisonOptions,
            'list_views': [
                ( 'embargo', '', 302 ),
                ( 'staging', '', 302 ),
                ( 'year', '2012/', 200 ),
            ],
        },
        'potws': {
            'root': '/images/potw/',
            'options': PictureOfTheWeekOptions,
            'list_views': [
                ( 'embargo', '', 302 ),
                ( 'staging', '', 302 ),
                ( 'year', '2012/', 200 ),
            ],
        },
    }

    def setUp( self ):
        pass

    def _assert_response(self, response, code):
        status_code = response.status_code
        request_method = response.request['REQUEST_METHOD']
        path_info = response.request['PATH_INFO']

        keyed_message = "%s request to %s failed,.. Expected code %s, got %s instead."
        error_message = keyed_message % (request_method, path_info, code, status_code)

        self.assertEqual(status_code, code, error_message)

    def test_index_root(self):
        """
        Test if main index archive pages is reachable
        """
        for conf in self.conf.values():
            response = self.client.get(conf['root'])
            self._assert_response(response, 200)

    def test_queries( self ):
        """
        Test if all queries with all their browsers
        """
        for conf in self.conf.values():
            opt = conf['options']
            root = conf['root']
            views = conf['list_views']

            for q, subpart, code in views:
                view_url_root = "%sarchive/%s/%s" % ( root, q, subpart )
                response = self.client.get( view_url_root )
                self._assert_response( response, code )

                for browser in getattr( opt.Queries, q ).browsers:
                    view_url = "%s%s/" % ( view_url_root, browser )
                    response = self.client.get( view_url )
                    self._assert_response( response, code )
