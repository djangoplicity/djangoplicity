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

import json
from unittest import mock

from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings

from djangoplicity.media import views
from djangoplicity.media.models import Image, MultiwavelengthImage, \
    MultiwavelengthImageBand


@override_settings( USE_I18N=True )
class WavelengthSelectorTestCase( TestCase ):
    """ The use_wavelength_selector flag of MultiwavelengthImage. """

    def setUp( self ):
        self.source = MultiwavelengthImage.objects.create(
            id='mwltest', title='Test object' )

    def _translation( self ):
        return MultiwavelengthImage.objects.create(
            id='mwltest-es', title='Objeto de prueba', lang='es', source=self.source )

    def _band( self, image_id, wavelength, is_main=False ):
        image = Image.objects.create( id=image_id, title=image_id, priority=0 )
        return MultiwavelengthImageBand.objects.create(
            multiwavelength_image=self.source, image=image,
            wavelength=wavelength, is_main=is_main )

    def test_on_by_default( self ):
        self.assertTrue( self.source.use_wavelength_selector )

    def test_new_translation_inherits_it( self ):
        self.source.use_wavelength_selector = False
        self.source.save()

        self.assertFalse( self._translation().use_wavelength_selector )

    def test_change_on_source_reaches_translations( self ):
        translation = self._translation()

        self.source.use_wavelength_selector = False
        self.source.save()

        translation.refresh_from_db()
        self.assertFalse( translation.use_wavelength_selector )

    def test_bands_do_not_depend_on_it( self ):
        # The wavelength stays required in both modes and still orders the
        # images, so switching the selector off changes nothing here.
        radio = self._band( 'mwltest-radio', 1e8 )
        visible = self._band( 'mwltest-visible', 550.0, is_main=True )
        xray = self._band( 'mwltest-xray', 1.0 )

        for selector in ( True, False ):
            self.source.use_wavelength_selector = selector
            self.source.save()
            source = MultiwavelengthImage.objects.get( pk=self.source.pk )

            self.assertEqual( [ b.pk for b in source.ordered_bands() ],
                              [ xray.pk, visible.pk, radio.pk ] )
            self.assertEqual( source.main_band_object().pk, visible.pk )


# Images whose id ends in '-notiles' have no zoomable tiles.
def _zoomable_resource( instance, *args, **kwargs ):
    if instance.id.endswith( '-notiles' ):
        return None
    return mock.Mock( url='https://cdn.test/zoomable/%s' % instance.id )


# The site may use a manifest storage, which only knows the collected files.
@override_settings( USE_I18N=True,
                    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage' )
@mock.patch.object( Image.Archive.zoomable, 'get_resource_for_instance',
                    side_effect=_zoomable_resource )
class ZoomableCompareTestCase( TestCase ):
    """ The images of the fullscreen zoomable viewer with crossfade. """

    def setUp( self ):
        self.source = MultiwavelengthImage.objects.create(
            id='mwltest', title='Test object' )

    def _band( self, image_id, wavelength, is_main=False, title='' ):
        image = Image.objects.create( id=image_id, title=image_id, priority=0,
                                      width=2000, height=1000 )
        return MultiwavelengthImageBand.objects.create(
            multiwavelength_image=self.source, image=image,
            wavelength=wavelength, is_main=is_main, title=title )

    def _ids( self, obj ):
        return [ i['image'].id for i in obj.get_zoomable_images() ]

    def _render( self, obj ):
        request = RequestFactory().get( '/multiwavelength/%s/fullscreen-comparison/' % obj.pk )
        return views.ZoomableCompareDetailView().render(
            request, MultiwavelengthImage, obj, None, False )

    def test_ordered_by_wavelength_with_main_marked( self, _resource ):
        self._band( 'mwltest-radio', 1e8 )
        self._band( 'mwltest-visible', 550.0, is_main=True, title='Visible light' )
        self._band( 'mwltest-xray', 1.0 )

        images = self.source.get_zoomable_images()

        self.assertEqual( self._ids( self.source ),
                          [ 'mwltest-xray', 'mwltest-visible', 'mwltest-radio' ] )
        self.assertEqual( [ i['is_main'] for i in images ], [ False, True, False ] )
        self.assertEqual( images[1]['title'], 'Visible light' )
        self.assertEqual( images[1]['label'], 'Visible light' )

    def test_only_images_with_tiles( self, _resource ):
        self._band( 'mwltest-visible', 550.0, is_main=True )
        self._band( 'mwltest-xray-notiles', 1.0 )
        self._band( 'mwltest-radio', 1e8 )

        self.assertEqual( self._ids( self.source ), [ 'mwltest-visible', 'mwltest-radio' ] )

    def test_main_without_tiles_is_replaced( self, _resource ):
        self._band( 'mwltest-visible-notiles', 550.0, is_main=True )
        self._band( 'mwltest-xray', 1.0 )
        self._band( 'mwltest-radio', 1e8 )

        images = self.source.get_zoomable_images()

        self.assertEqual( self._ids( self.source ), [ 'mwltest-xray', 'mwltest-radio' ] )
        self.assertEqual( [ i['is_main'] for i in images ], [ True, False ] )

    def test_image_in_several_bands_shown_once( self, _resource ):
        band = self._band( 'mwltest-visible', 550.0, is_main=True )
        MultiwavelengthImageBand.objects.create(
            multiwavelength_image=self.source, image=band.image, wavelength=700.0 )

        self.assertEqual( self._ids( self.source ), [ 'mwltest-visible' ] )

    def test_translation_uses_source_bands( self, _resource ):
        self._band( 'mwltest-visible', 550.0, is_main=True )
        translation = MultiwavelengthImage.objects.create(
            id='mwltest-es', title='Objeto de prueba', lang='es', source=self.source )

        self.assertEqual( self._ids( translation ), [ 'mwltest-visible' ] )

    @mock.patch.object( views, '_zoomable_proxy', return_value=( False, None ) )
    def test_view_renders_layers( self, _proxy, _resource ):
        self._band( 'mwltest-visible', 550.0, is_main=True )
        self._band( 'mwltest-xray', 1.0 )

        html = self._render( self.source )

        data = html.split( 'id="zoomable-layers"', 1 )[1].split( '>', 1 )[1].split( '</script>', 1 )[0]
        layers = json.loads( data )
        self.assertEqual( [ l['id'] for l in layers ], [ 'mwltest-xray', 'mwltest-visible' ] )
        self.assertEqual( [ l['is_main'] for l in layers ], [ False, True ] )
        self.assertEqual( layers[1]['tiles_url'], 'https://cdn.test/zoomable/mwltest-visible/' )
        self.assertEqual( ( layers[1]['width'], layers[1]['height'] ), ( 2000, 1000 ) )

    @mock.patch.object( views, '_zoomable_proxy', return_value=( True, '/proxy/tiles/' ) )
    def test_private_tiles_go_through_the_proxy( self, _proxy, _resource ):
        self._band( 'mwltest-visible', 550.0, is_main=True )

        self.assertIn( '/proxy/tiles/', self._render( self.source ) )

    def test_view_404_without_tiles( self, _resource ):
        self._band( 'mwltest-visible-notiles', 550.0, is_main=True )

        with self.assertRaises( Http404 ):
            self._render( self.source )
