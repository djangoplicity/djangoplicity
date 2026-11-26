# -*- coding: utf-8 -*-
#
# QA tests for the annotations overlay (Zoomify pyramid) of the
# multiwavelength Fullscreen & Compare viewer: the annotations_zoomable
# resource of MultiwavelengthImage, its import, its content server sync
# (always public) and the toggle of the compare page.
#
# Notes:
# - MultiwavelengthImage.save() is not used: with DEBUG=False the post_save
#   static_files_protection_handler sends a Celery task to the broker. Rows
#   are written with bulk_create.
# - MEDIA_ROOT and ARCHIVE_IMPORT_ROOT point to temporary directories.
# - The content server is an S3ContentServer whose boto3 client is a mock,
#   so nothing is uploaded.

import json
import os
import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import resolve, reverse

from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.importer.utils import find_importables
from djangoplicity.contentserver.base import S3ContentServer
from djangoplicity.contentserver.constants import AccessTagControl
from djangoplicity.contentserver.models import ContentServerResource
from djangoplicity.media import consts, views
from djangoplicity.media.models import Image, MultiwavelengthImage
from djangoplicity.media.options import MultiwavelengthImageOptions

# Same content as resources/zoomable-constellations/allsky-overlay-2026-11-24/
# pyramid-stars/ImageProperties.xml (Davide's pyramid).
DAVIDE_XML = '<IMAGE_PROPERTIES WIDTH="60000" HEIGHT="30000" NUMTILES="37075" NUMIMAGES="1" VERSION="1.8" TILESIZE="256" />\n'

QA_SERVER = 'QA_S3'
QA_BASE_URL = 'https://storage.test/media'
MWL_ID = 'mwlqa'
FORMAT = 'annotations_zoomable'


def _qa_server():
    server = S3ContentServer( bucket='qa-bucket', base_url=QA_BASE_URL )
    server.s3_client = mock.Mock()
    return server


class _TempMediaMixin( object ):
    """ MEDIA_ROOT in a temporary directory for every test. """

    def setUp( self ):
        super( _TempMediaMixin, self ).setUp()
        self.media_root = tempfile.mkdtemp( prefix='qa-media-' )
        self.addCleanup( shutil.rmtree, self.media_root, True )
        settings_override = override_settings( MEDIA_ROOT=self.media_root )
        settings_override.enable()
        self.addCleanup( settings_override.disable )

    def _pyramid_dir( self, obj_id=MWL_ID ):
        return os.path.join( self.media_root, 'archives', 'multiwavelength', FORMAT, obj_id )

    def _make_pyramid( self, obj_id=MWL_ID, xml=DAVIDE_XML, tiles=( '0-0-0.png', ) ):
        path = self._pyramid_dir( obj_id )
        os.makedirs( os.path.join( path, 'TileGroup0' ) )
        if xml is not None:
            with open( os.path.join( path, 'ImageProperties.xml' ), 'w' ) as f:
                f.write( xml )
        for tile in tiles:
            with open( os.path.join( path, 'TileGroup0', tile ), 'wb' ) as f:
                f.write( b'png' )
        return path

    def _mwl( self, **kwargs ):
        kwargs.setdefault( 'id', MWL_ID )
        kwargs.setdefault( 'title', 'QA object' )
        return MultiwavelengthImage( **kwargs )

    def _create_mwl( self, **kwargs ):
        MultiwavelengthImage.objects.bulk_create( [ self._mwl( **kwargs ) ] )
        return MultiwavelengthImage.objects.get( pk=kwargs.get( 'id', MWL_ID ) )


class AnnotationsZoomableModelTestCase( _TempMediaMixin, TestCase ):
    """ AC3: MultiwavelengthImage.get_zoomable_annotations(). """

    def test_none_without_resource( self ):
        self.assertIsNone( self._mwl().resource_annotations_zoomable )
        self.assertIsNone( self._mwl().get_zoomable_annotations() )

    def test_none_without_image_properties( self ):
        self._make_pyramid( xml=None )

        self.assertIsNotNone( self._mwl().resource_annotations_zoomable )
        self.assertIsNone( self._mwl().get_zoomable_annotations() )

    def test_none_with_invalid_xml( self ):
        self._make_pyramid( xml='<IMAGE_PROPERTIES WIDTH="60000"' )

        self.assertIsNone( self._mwl().get_zoomable_annotations() )

    def test_none_without_width_or_height( self ):
        for xml in ( '<IMAGE_PROPERTIES TILESIZE="256" />',
                     '<IMAGE_PROPERTIES WIDTH="60000" />',
                     '<IMAGE_PROPERTIES WIDTH="abc" HEIGHT="30000" />' ):
            path = self._make_pyramid( xml=xml )

            self.assertIsNone( self._mwl().get_zoomable_annotations(), xml )
            shutil.rmtree( path )

    def test_dict_with_davide_xml( self ):
        self._make_pyramid()

        annotations = self._mwl().get_zoomable_annotations()

        self.assertEqual( annotations['width'], 60000 )
        self.assertEqual( annotations['height'], 30000 )
        self.assertTrue( annotations['tiles_url'].endswith(
            '/archives/multiwavelength/annotations_zoomable/%s/' % MWL_ID ), annotations['tiles_url'] )
        self.assertFalse( annotations['tiles_url'].endswith( '//' ) )

    def test_storage_url_once_synced_even_unpublished( self ):
        # AC3/AC12: with content_server_ready and an active directory record,
        # tiles_url points straight to the storage, also when unpublished.
        self._make_pyramid()
        obj = self._create_mwl( published=False, content_server=QA_SERVER, content_server_ready=True )
        ContentServerResource.objects.create(
            content_type=ContentType.objects.get_for_model( MultiwavelengthImage ),
            object_id=MWL_ID, format=FORMAT, resource_size=0, is_directory=True,
            is_active=True, content_server=QA_SERVER,
            content_server_path='archives/multiwavelength/%s/%s' % ( FORMAT, MWL_ID ) )

        with mock.patch.dict( consts.MEDIA_CONTENT_SERVERS, { QA_SERVER: _qa_server() } ):
            obj = MultiwavelengthImage.objects.get( pk=MWL_ID )
            annotations = obj.get_zoomable_annotations()

        self.assertEqual( annotations, {
            'tiles_url': '%s/archives/multiwavelength/%s/%s/' % ( QA_BASE_URL, FORMAT, MWL_ID ),
            'width': 60000,
            'height': 30000,
        } )


class AnnotationsContentServerTestCase( _TempMediaMixin, TestCase ):
    """ C12: the annotations are always public in the content server. """

    def setUp( self ):
        super( AnnotationsContentServerTestCase, self ).setUp()
        self.server = _qa_server()
        patcher = mock.patch.dict( consts.MEDIA_CONTENT_SERVERS, { QA_SERVER: self.server } )
        patcher.start()
        self.addCleanup( patcher.stop )

    def test_access_tag_public_while_unpublished_or_embargoed( self ):
        from datetime import datetime, timedelta
        unpublished = self._mwl( published=False, content_server=QA_SERVER )
        embargoed = self._mwl( published=True, content_server=QA_SERVER,
                               release_date=datetime.now() + timedelta( days=10 ),
                               embargo_date=datetime.now() + timedelta( days=5 ) )

        for obj in ( unpublished, embargoed ):
            self.assertEqual( obj.get_access_tag_for_format( FORMAT ), AccessTagControl.PUBLIC )
            # Without the override the object would be private
            self.assertEqual( obj.get_access_tag_for_format( 'original' ), AccessTagControl.PRIVATE )

    def test_other_formats_delegate_to_super( self ):
        obj = self._mwl()
        with mock.patch.object( ArchiveModel, 'get_access_tag_for_format', return_value='super' ) as parent:
            self.assertEqual( obj.get_access_tag_for_format( 'original' ), 'super' )
            self.assertEqual( obj.get_access_tag_for_format( FORMAT ), AccessTagControl.PUBLIC )
        parent.assert_called_once_with( 'original' )

    def test_update_resource_privacy_does_not_touch_the_content_server( self ):
        # AC13: also through the date actions and the Celery task that
        # ArchiveModel.save() queues when published/dates change.
        from djangoplicity.contentserver import tasks
        self.server.update_resource_privacy = mock.Mock()
        obj = self._create_mwl( published=False, content_server=QA_SERVER, content_server_ready=True )

        self.assertIsNone( obj.update_resource_privacy() )
        with mock.patch( 'djangoplicity.archives.base.clear_archive_list_cache' ), \
                mock.patch( 'djangoplicity.archives.base.facebook_refresh' ):
            obj.embargo_date_action()
            obj.release_date_action()
        with mock.patch.object( tasks.time, 'sleep' ):
            tasks.update_resource_privacy( 'media', 'multiwavelengthimage', MWL_ID )

        self.server.update_resource_privacy.assert_not_called()
        self.server.s3_client.put_object_tagging.assert_not_called()

    def test_sync_resources_uploads_every_file_public( self ):
        # AC2/AC12 (on a small pyramid, with a mocked S3 client)
        self._make_pyramid( tiles=( '0-0-0.png', '1-0-0.png', '1-1-0.png' ) )
        obj = self._create_mwl( published=False, content_server=QA_SERVER )

        self.server.sync_resources( obj )

        calls = self.server.s3_client.upload_file.call_args_list
        keys = sorted( c[0][2] for c in calls )
        prefix = 'archives/multiwavelength/%s/%s/' % ( FORMAT, MWL_ID )
        self.assertEqual( [ k.split( prefix, 1 )[1] for k in keys ], [
            'ImageProperties.xml', 'TileGroup0/0-0-0.png', 'TileGroup0/1-0-0.png', 'TileGroup0/1-1-0.png' ] )
        for c in calls:
            self.assertEqual( c[0][1], 'qa-bucket' )
            self.assertEqual( c[1]['ExtraArgs'], { 'Tagging': 'Access=Public' } )
        self.assertTrue( MultiwavelengthImage.objects.get( pk=MWL_ID ).content_server_ready )

    def test_sync_task_records_a_directory_resource( self ):
        # AC2: the import action task ends with ContentServerResource(is_directory=True, is_active=True)
        from djangoplicity.contentserver import tasks
        self._make_pyramid()
        self._create_mwl( published=False, content_server=QA_SERVER )
        self.server.s3_client.list_objects_v2.return_value = { 'Contents': [ { 'Key': 'x' } ] }
        self.server.s3_client.get_object_tagging.return_value = { 'TagSet': [ { 'Key': 'Access', 'Value': 'Public' } ] }

        with override_settings( DEFAULT_MEDIA_CONTENT_SERVER=QA_SERVER ):
            tasks.sync_content_server( MultiwavelengthImage.__module__, 'MultiwavelengthImage', MWL_ID )

        self.assertTrue( MultiwavelengthImage.objects.get( pk=MWL_ID ).content_server_ready )
        record = ContentServerResource.objects.get( object_id=MWL_ID, format=FORMAT )
        self.assertTrue( record.is_directory )
        self.assertTrue( record.is_active )
        self.assertTrue( record.content_server_path.endswith(
            'archives/multiwavelength/%s/%s' % ( FORMAT, MWL_ID ) ) )


class AnnotationsImportTestCase( _TempMediaMixin, TestCase ):
    """ AC1: import of the pyramid folder through the archive importer. """

    def setUp( self ):
        super( AnnotationsImportTestCase, self ).setUp()
        self.import_root = tempfile.mkdtemp( prefix='qa-import-' )
        self.addCleanup( shutil.rmtree, self.import_root, True )
        settings_override = override_settings( ARCHIVE_IMPORT_ROOT=self.import_root )
        settings_override.enable()
        self.addCleanup( settings_override.disable )

    def _drop_folder( self, obj_id=MWL_ID ):
        path = os.path.join( self.import_root, 'multiwavelength', FORMAT, obj_id )
        os.makedirs( os.path.join( path, 'TileGroup0' ) )
        with open( os.path.join( path, 'ImageProperties.xml' ), 'w' ) as f:
            f.write( DAVIDE_XML )
        with open( os.path.join( path, 'TileGroup0', '0-0-0.png' ), 'wb' ) as f:
            f.write( b'png' )
        return path

    def test_import_options( self ):
        options = MultiwavelengthImageOptions.Import
        self.assertFalse( options.uploadable )
        self.assertEqual( options.scan_directories, [ ( FORMAT, ( '', ) ) ] )

        taskset = mock.Mock()
        for action in options.actions:
            taskset, _conf = action( taskset, MultiwavelengthImage, MultiwavelengthImageOptions,
                                     self._mwl(), {}, { 'formats': FORMAT },
                                     conf={ 'import_root': 'src', 'archive_root': 'dst' } )
        names = [ c[0][0] for c in taskset.add.call_args_list ]
        self.assertEqual( names, [ 'archives.move_resources',
                                   'djangoplicity.contentserver.tasks.sync_content_server' ] )

    def test_find_importables_detects_the_folder( self ):
        folder = self._drop_folder()

        files, invalid = find_importables( os.path.join( self.import_root, 'multiwavelength' ),
                                           MultiwavelengthImage, MultiwavelengthImageOptions )

        self.assertEqual( list( files ), [ MWL_ID ] )
        self.assertEqual( files[MWL_ID]['formats'], FORMAT )
        self.assertEqual( files[MWL_ID]['files'], [ folder ] )
        self.assertEqual( invalid, [] )

    def test_move_resources_puts_it_in_the_archive( self ):
        from djangoplicity.archives.tasks import move_resources
        folder = self._drop_folder()

        move_resources( os.path.join( self.import_root, 'multiwavelength' ),
                        os.path.join( self.media_root, 'archives/multiwavelength/' ),
                        archive_id=MWL_ID )

        self.assertFalse( os.path.exists( folder ) )
        self.assertTrue( os.path.isfile( os.path.join( self._pyramid_dir(), 'TileGroup0', '0-0-0.png' ) ) )
        self.assertEqual( self._mwl().get_zoomable_annotations()['width'], 60000 )

    def test_import_url( self ):
        url = reverse( 'media_multiwavelengthimage_import' )

        self.assertTrue( url.endswith( '/admin/import/multiwavelength/' ), url )
        self.assertEqual( resolve( url ).kwargs['archive_model'], MultiwavelengthImage )

    def test_import_page_lists_the_folder( self ):
        self._drop_folder()
        client = _staff_client()

        response = client.get( reverse( 'media_multiwavelengthimage_import' ) )

        self.assertEqual( response.status_code, 200 )
        self.assertIn( MWL_ID, response.content.decode() )
        self.assertIsNone( response.context['upload_form'] )


def _staff_client():
    from django_otp.plugins.otp_totp.models import TOTPDevice
    user = User.objects.create_superuser( 'qa-admin', 'qa@example.test', 'qa-password' )
    TOTPDevice.objects.create( user=user, name='qa', confirmed=True )
    client = Client()
    client.force_login( user )
    session = client.session
    session['otp_verified'] = True
    session.save()
    return client


@override_settings( STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage' )
class AnnotationsAdminTestCase( TestCase ):
    """ AC4: the admin of MultiwavelengthImage. """

    def _admin( self ):
        from noirlab.admin import admin_site
        return admin_site._registry[MultiwavelengthImage]

    def test_content_delivery_admin( self ):
        from djangoplicity.contentserver.admin import ContentDeliveryAdmin
        admin = self._admin()

        self.assertIsInstance( admin, ContentDeliveryAdmin )
        fieldsets = dict( ( str( name ), opts ) for name, opts in admin.fieldsets )
        self.assertEqual( tuple( fieldsets['Content Delivery']['fields'] ),
                          ( 'content_server', 'content_server_ready' ) )
        self.assertIn( 'content_server_ready', admin.readonly_fields )
        for action in ( 'action_toggle_published', 'action_reimport', 'action_resync_resources' ):
            self.assertIn( action, admin.actions )
            self.assertTrue( callable( getattr( admin, action ) ), action )

    def test_changelist_has_import_button( self ):
        # Django only shows the actions when the list is not empty
        MultiwavelengthImage.objects.bulk_create( [ MultiwavelengthImage( id=MWL_ID, title='QA object' ) ] )
        client = _staff_client()

        response = client.get( reverse( 'admin_site:media_multiwavelengthimage_changelist' ) )

        self.assertEqual( response.status_code, 200 )
        html = response.content.decode()
        self.assertIn( 'Import files', html )
        self.assertIn( 'admin/import/multiwavelength/', html )
        for action in ( 'action_reimport', 'action_resync_resources' ):
            self.assertIn( 'value="%s"' % action, html )


def _image_resource( instance, *args, **kwargs ):
    return mock.Mock( url='https://cdn.test/zoomable/%s' % instance.id )


@override_settings( USE_I18N=True,
                    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage' )
@mock.patch.object( views, '_zoomable_proxy', return_value=( False, None ) )
@mock.patch.object( Image.Archive.zoomable, 'get_resource_for_instance', side_effect=_image_resource )
@mock.patch.object( Image.Archive.thumb350x, 'get_resource_for_instance', return_value=None )
@mock.patch.object( Image.Archive.screen, 'get_resource_for_instance', return_value=None )
class AnnotationsCompareViewTestCase( _TempMediaMixin, TestCase ):
    """ AC5, AC9, AC11 (server side) and P10: the compare page. """

    def setUp( self ):
        super( AnnotationsCompareViewTestCase, self ).setUp()
        image = Image( id='mwlqa-visible', title='Visible', width=2000, height=1000 )
        patcher = mock.patch.object( MultiwavelengthImage, 'get_zoomable_images', return_value=[ {
            'image': image, 'title': '', 'label': 'Visible light', 'wavelength': '', 'is_main': True } ] )
        patcher.start()
        self.addCleanup( patcher.stop )

    def _render( self, embed=False ):
        obj = self._mwl()
        request = RequestFactory().get( '/multiwavelength/%s/fullscreen-comparison/' % MWL_ID,
                                        { 'embed': '1' } if embed else {} )
        return views.ZoomableCompareDetailView().render( request, MultiwavelengthImage, obj, None, False )

    def _annotations_json( self, html ):
        data = html.split( 'id="zoomable-annotations"', 1 )[1].split( '>', 1 )[1].split( '</script>', 1 )[0]
        return json.loads( data )

    def test_toggle_on_with_annotations( self, *_mocks ):
        self._make_pyramid()

        for embed in ( False, True ):
            html = self._render( embed )

            header = html.split( '<header class="zc-bar zc-top">', 1 )[1].split( '</header>', 1 )[0]
            self.assertIn( 'data-zc-annotations aria-pressed="true"', header )
            self.assertIn( '>Annotations ON</button>', header )
            self.assertIn( 'data-label-off="Annotations OFF"', header )
            annotations = self._annotations_json( html )
            self.assertEqual( ( annotations['width'], annotations['height'] ), ( 60000, 30000 ) )
            self.assertTrue( annotations['tiles_url'].endswith( '/%s/%s/' % ( FORMAT, MWL_ID ) ) )
            # The script reading it is loaded after the JSON
            self.assertLess( html.index( 'id="zoomable-annotations"' ), html.index( 'media/js/zoomable_compare.js' ) )

    def test_context_has_the_annotations( self, *_mocks ):
        self._make_pyramid()
        with mock.patch( 'djangoplicity.media.views.loader.select_template' ) as select:
            self._render()
        context = select.return_value.render.call_args[0][0]
        self.assertEqual( context['annotations']['width'], 60000 )

    def test_no_toggle_without_resource( self, *_mocks ):
        for embed in ( False, True ):
            html = self._render( embed )

            self.assertNotIn( 'data-zc-annotations', html )
            self.assertNotIn( 'zoomable-annotations', html )
            self.assertIn( 'id="zoomable-layers"', html )

    def test_no_toggle_if_the_pyramid_cannot_be_read( self, *_mocks ):
        # AC11 (failures detectable on the server): folder without XML, or a broken XML
        path = self._make_pyramid( xml=None )
        self.assertNotIn( 'data-zc-annotations', self._render() )

        shutil.rmtree( path )
        self._make_pyramid( xml='not xml' )
        html = self._render()
        self.assertNotIn( 'data-zc-annotations', html )
        self.assertNotIn( 'zoomable-annotations', html )

    def test_hidden_button_rule( self, *_mocks ):
        # The [hidden] attribute set by zoomable_compare.js must win over .zc-btn's display
        self._make_pyramid()
        html = self._render()
        self.assertRegex( html, r'\.zc-btn\[hidden\]\s*\{\s*display:\s*none;' )


@override_settings( USE_I18N=True )
class AnnotationsDetailPageTestCase( _TempMediaMixin, TestCase ):
    """ AC10: the normal detail page does not get the toggle. """

    def test_detail_templates_do_not_use_the_annotations( self ):
        from django.template.loader import get_template
        names = [ MultiwavelengthImageOptions.template_name, 'archives/multiwavelength/_toolbar.html' ]
        for name in names:
            source = open( get_template( name ).origin.name ).read()
            self.assertNotIn( 'data-zc-annotations', source, name )
            self.assertNotIn( 'zoomable-annotations', source, name )
            self.assertNotIn( 'get_zoomable_annotations', source, name )
