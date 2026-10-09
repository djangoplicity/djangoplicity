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
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings

from djangoplicity.media import views
from djangoplicity.media.models import Image, MultiwavelengthImage, \
    MultiwavelengthImageBand
from djangoplicity.media.options import MultiwavelengthImageOptions


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



@override_settings( USE_I18N=True )
class OverlayUrlsTestCase( TestCase ):
    """ The constellations and annotations overlays of MultiwavelengthImage. """

    URL = 'https://cdn.test/overlays/mwltest-constellations.png'

    def setUp( self ):
        self.source = MultiwavelengthImage.objects.create(
            id='mwltest', title='Test object' )

    def _translation( self ):
        return MultiwavelengthImage.objects.create(
            id='mwltest-es', title='Objeto de prueba', lang='es', source=self.source )

    def test_empty_by_default( self ):
        self.assertEqual( self.source.constellations_image_url, '' )
        self.assertEqual( self.source.annotations_image_url, '' )

    def test_new_translation_inherits_them( self ):
        self.source.constellations_image_url = self.URL
        self.source.save()

        self.assertEqual( self._translation().constellations_image_url, self.URL )

    def test_change_on_source_reaches_translations( self ):
        translation = self._translation()

        self.source.annotations_image_url = self.URL
        self.source.save()

        translation.refresh_from_db()
        self.assertEqual( translation.annotations_image_url, self.URL )


# Images whose id ends in '-nobanner' have no banner1920.
def _banner_resource( instance, *args, **kwargs ):
    if instance.id.endswith( '-nobanner' ):
        return None
    return mock.Mock( url='https://cdn.test/banner1920/%s.jpg' % instance.id )


def _screen_resource( instance, *args, **kwargs ):
    return mock.Mock( url='https://cdn.test/screen/%s.jpg' % instance.id )


@override_settings( USE_I18N=True )
@mock.patch.object( Image.Archive.zoomable, 'get_resource_for_instance', return_value=None )
@mock.patch.object( Image.Archive.screen, 'get_resource_for_instance', side_effect=_screen_resource )
@mock.patch.object( Image.Archive.banner1920, 'get_resource_for_instance', side_effect=_banner_resource )
class StageImageTestCase( TestCase ):
    """ The picture each band shows on the stage, and the overlay toggles. """

    def setUp( self ):
        self.source = MultiwavelengthImage.objects.create(
            id='mwltest', title='Test object' )

    def _band( self, image_id, width=2000, height=1000 ):
        image = Image.objects.create( id=image_id, title=image_id, priority=0,
                                      width=width, height=height )
        return MultiwavelengthImageBand.objects.create(
            multiwavelength_image=self.source, image=image, wavelength=550.0 )

    def _toolbar( self ):
        obj = MultiwavelengthImage.objects.get( pk=self.source.pk )
        return render_to_string( 'archives/multiwavelength/_toolbar.html',
                                 { 'object': obj, 'bands': obj.ordered_bands() } )

    def test_banner_first( self, *_resources ):
        band = self._band( 'mwltest-visible' )

        self.assertTrue( band.hero_is_banner )
        self.assertEqual( band.hero.url, 'https://cdn.test/banner1920/mwltest-visible.jpg' )
        self.assertEqual( band.hero_ratio, '2.1333' )

    def test_screen_without_banner( self, *_resources ):
        band = self._band( 'mwltest-visible-nobanner', width=1000, height=1000 )

        self.assertFalse( band.hero_is_banner )
        self.assertEqual( band.hero.url, 'https://cdn.test/screen/mwltest-visible-nobanner.jpg' )
        self.assertEqual( band.hero_ratio, '1.0000' )

    def test_no_ratio_without_size( self, *_resources ):
        band = self._band( 'mwltest-visible-nobanner', width=0, height=0 )

        self.assertEqual( band.hero_ratio, '' )

    def test_no_toggles_without_overlays( self, *_resources ):
        self._band( 'mwltest-visible' )

        html = self._toolbar()

        self.assertNotIn( 'mwl-layer-toggle', html )

    def test_toggle_only_for_the_overlays_it_has( self, *_resources ):
        self._band( 'mwltest-visible' )
        self.source.constellations_image_url = 'https://cdn.test/c.png'
        self.source.save()

        html = self._toolbar()

        self.assertIn( 'data-layer="constellations"', html )
        self.assertNotIn( 'data-layer="annotations"', html )

    def test_both_toggles_in_both_modes( self, *_resources ):
        self._band( 'mwltest-visible' )
        self.source.constellations_image_url = 'https://cdn.test/c.png'
        self.source.annotations_image_url = 'https://cdn.test/a.png'

        for selector in ( True, False ):
            self.source.use_wavelength_selector = selector
            self.source.save()

            html = self._toolbar()

            self.assertIn( 'data-layer="constellations"', html )
            self.assertIn( 'data-layer="annotations"', html )


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

    def _request( self, obj, embed=False ):
        return RequestFactory().get( '/multiwavelength/%s/fullscreen-comparison/' % obj.pk,
                                     { 'embed': '1' } if embed else {} )

    def _render( self, obj, embed=False ):
        return views.ZoomableCompareDetailView().render(
            self._request( obj, embed ), MultiwavelengthImage, obj, None, False )

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

    @mock.patch.object( views, '_zoomable_proxy', return_value=( False, None ) )
    def test_embedded_page_closes_instead_of_going_back( self, _proxy, _resource ):
        self._band( 'mwltest-visible', 550.0, is_main=True )

        page = self._render( self.source )
        embedded = self._render( self.source, embed=True )

        back = 'href="%s"' % self.source.get_absolute_url()
        self.assertIn( back, page )
        self.assertNotIn( 'data-zc-close', page )
        self.assertIn( 'data-zc-close', embedded )
        self.assertNotIn( back, embedded )

    def test_embedded_page_is_cached_apart( self, _resource ):
        view = views.ZoomableCompareDetailView()

        page = view.vary_on( self._request( self.source ), MultiwavelengthImage, self.source, None, False )
        embedded = view.vary_on( self._request( self.source, embed=True ), MultiwavelengthImage, self.source, None, False )

        self.assertNotEqual( page, embedded )

    def test_can_be_framed_by_the_same_origin( self, _resource ):
        view = views.ZoomableCompareDetailView()
        view.options = MultiwavelengthImageOptions

        response = view.response( '<html></html>' )

        self.assertEqual( response['X-Frame-Options'], 'SAMEORIGIN' )
