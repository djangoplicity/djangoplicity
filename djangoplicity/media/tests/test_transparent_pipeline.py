# -*- coding: utf-8 -*-
#
# Tests for the "transparent pipeline" in the image import:
# transparent_zoomable (PNG tiles with alpha through vips dzsave) and
# transparent_derivatives (PNG derived formats with alpha).
#
# Run with:
#   docker exec noirlab ./manage.py test djangoplicity.media.tests.test_transparent_pipeline
#
# The integration tests (classes *IntegrationTest) need vips/ImageMagick and
# are skipped if the binaries are not available. They only write in temporary
# directories (MEDIA_ROOT is overridden).

import os
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
from unittest import mock, skipUnless

from django.test import SimpleTestCase, TestCase, override_settings

from djangoplicity.archives.contrib import types
from djangoplicity.cutter import imagemagick
from djangoplicity.cutter.imagemagick import (
    CONVERT, SRGB_PROFILE, _get_convert_args, _get_dzsave_args,
    _get_output_ext, _generate_zoomify_vips, process_image_derivatives,
)
from djangoplicity.media.admin import ImageAdmin
from djangoplicity.media.consts import IMAGES_IMPORT_HELP_TEXT
from djangoplicity.media.forms import ImageImportForm
from djangoplicity.media.models import Image
from djangoplicity.media.options import ImageOptions, VideoOptions


HAS_VIPS = bool(shutil.which('vips') and shutil.which('vipsheader'))
HAS_IM = bool(shutil.which('convert') and shutil.which('identify'))


def _archive(transparent_derivatives=None, pk='qa-transp'):
    '''Fake archive: without the attribute if transparent_derivatives is None'''
    archive = SimpleNamespace(pk=pk, _bit_depth=8, crop_offsets=None)
    if transparent_derivatives is not None:
        archive.transparent_derivatives = transparent_derivatives
    return archive


class TransparentHelpersTest(SimpleTestCase):
    '''C6/C8: _get_dzsave_args and _get_output_ext (AC3, AC9, AC11)'''

    def test_dzsave_args_default_identical_to_original_command(self):
        expected = ['vips', 'dzsave', '/src/img.tif', '/tmp/z', '--basename', 'zoomable',
                    '--suffix', '.jpg[Q=90]', '--layout', 'zoomify', '--strip']
        self.assertEqual(_get_dzsave_args('/src/img.tif', '/tmp/z', 'zoomable'), expected)
        self.assertEqual(_get_dzsave_args('/src/img.tif', '/tmp/z', 'zoomable', transparent=False), expected)

    def test_dzsave_args_transparent_uses_png_suffix(self):
        self.assertEqual(
            _get_dzsave_args('/src/img.png', '/tmp/z', 'zoomable', transparent=True),
            ['vips', 'dzsave', '/src/img.png', '/tmp/z', '--basename', 'zoomable',
             '--suffix', '.png', '--layout', 'zoomify', '--strip'])

    def test_output_ext_jpg_becomes_png_only_with_flag(self):
        screen = Image.Archive.screen
        self.assertEqual(_get_output_ext(_archive(False), screen), 'jpg')
        self.assertEqual(_get_output_ext(_archive(True), screen), 'png')
        self.assertEqual(_get_output_ext(_archive(True), Image.Archive.large), 'png')

    def test_output_ext_tiff_and_png_unchanged(self):
        for flag in (False, True):
            self.assertEqual(_get_output_ext(_archive(flag), Image.Archive.publicationtiff), 'tif')
            png_fmt = SimpleNamespace(type=types.Thumb300xPNGType)
            self.assertEqual(_get_output_ext(_archive(flag), png_fmt), 'png')

    def test_output_ext_archive_without_attribute_uses_default(self):
        # e.g. Video or other archives without the field (AC11)
        self.assertEqual(_get_output_ext(_archive(None), Image.Archive.screen), 'jpg')
        self.assertEqual(_get_output_ext(_archive(None), Image.Archive.publicationtiff), 'tif')


class TransparentConvertArgsTest(SimpleTestCase):
    '''C8: _get_convert_args with flags False/True (AC7, AC9)'''

    def _args(self, archive, fmt, width, height):
        return _get_convert_args(archive, width, height, fmt, '/tmp/in.mpc', '/tmp/out')

    def test_screen_flag_false_identical_to_original(self):
        expected = CONVERT.split() + [
            '-resize', '1280x', '-unsharp', '1x1+0.25+0', '-quality', '85',
            '-profile', SRGB_PROFILE, '/tmp/in.mpc', '-depth', '8',
            '/tmp/out/qa-transp.jpg']
        self.assertEqual(self._args(_archive(False), Image.Archive.screen, 2000, 1000), expected)
        # Archive without the attribute behaves the same (AC11)
        self.assertEqual(self._args(_archive(None), Image.Archive.screen, 2000, 1000), expected)

    def test_screen_flag_true_png_without_quality(self):
        args = self._args(_archive(True), Image.Archive.screen, 2000, 1000)
        self.assertEqual(args[-1], '/tmp/out/qa-transp.png')
        self.assertNotIn('-quality', args)
        self.assertIn('-unsharp', args)
        self.assertEqual(args[args.index('-resize') + 1], '1280x')

    def test_large_jpg_limit_65500_only_without_flag(self):
        # LargeJpegType has no width/height/size so the resize option is -thumbnail
        large = Image.Archive.large
        args = self._args(_archive(False), large, 70000, 35000)
        self.assertIn('65500x', args)
        self.assertIn('-quality', args)
        self.assertTrue(args[-1].endswith('qa-transp.jpg'))

        args = self._args(_archive(False), large, 35000, 70000)
        self.assertIn('x65500', args)

        args = self._args(_archive(True), large, 70000, 35000)
        self.assertNotIn('65500x', args)
        self.assertNotIn('-thumbnail', args)
        self.assertNotIn('-resize', args)
        self.assertNotIn('-quality', args)
        self.assertTrue(args[-1].endswith('qa-transp.png'))

    def test_tiff_identical_with_and_without_flag(self):
        for fmt, w, h in ((Image.Archive.publicationtiff, 6000, 3000),
                          (Image.Archive.publicationtiff40k, 60000, 30000)):
            args_false = self._args(_archive(False), fmt, w, h)
            args_true = self._args(_archive(True), fmt, w, h)
            self.assertEqual(args_false, args_true)
            self.assertTrue(args_true[-1].endswith('qa-transp.tif'))
            self.assertIn('-compress', args_true)
        # BigTIFF still forced for the 40k format
        args_40k = self._args(_archive(True), Image.Archive.publicationtiff40k, 60000, 30000)
        self.assertTrue(args_40k[-1].startswith('tiff64:'))

    def test_png_type_keeps_quality(self):
        fmt = SimpleNamespace(type=types.Thumb300xPNGType)
        for flag in (False, True):
            args = self._args(_archive(flag), fmt, 2000, 1000)
            self.assertIn('-quality', args)
            self.assertTrue(args[-1].endswith('qa-transp.png'))


class TransparentImportFormTest(SimpleTestCase):
    '''C3/C4/C14: import form, handle_import and help text (AC1, AC2, AC11)'''

    def test_form_has_new_unchecked_optional_fields(self):
        form = ImageImportForm()
        for name in ('transparent_zoomable', 'transparent_derivatives'):
            self.assertIn(name, form.fields)
            field = form.fields[name]
            self.assertFalse(field.required)
            self.assertIs(field.initial, False)
            self.assertTrue(field.help_text)
        # Existing fields untouched
        self.assertIs(form.fields['zoomify'].initial, True)
        self.assertIs(form.fields['wallpapers'].initial, True)

    def test_form_cleaned_data_defaults_to_false(self):
        form = ImageImportForm(data={
            'id': 'x', 'date_modified': 'x', 'title': 't', 'priority': '0', 'formats': 'original',
            'credit': 'c'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIs(form.cleaned_data.get('transparent_zoomable'), False)
        self.assertIs(form.cleaned_data.get('transparent_derivatives'), False)

    def _handle_import(self, zoomable, derivatives):
        obj = mock.Mock(description='d', credit='c')
        form_values = {'wallpapers': True, 'zoomify': True,
                       'transparent_zoomable': zoomable,
                       'transparent_derivatives': derivatives}
        with mock.patch('djangoplicity.archives.importer.utils.handle_import',
                        side_effect=lambda obj, **kw: obj):
            res = ImageOptions.handle_import(obj, id='x', data={'files': [], 'formats': []},
                                             form_values=form_values)
        obj.save.assert_called_once_with()
        return res

    def test_handle_import_copies_flags(self):
        res = self._handle_import(True, False)
        self.assertIs(res.transparent_zoomable, True)
        self.assertIs(res.transparent_derivatives, False)
        res = self._handle_import(False, True)
        self.assertIs(res.transparent_zoomable, False)
        self.assertIs(res.transparent_derivatives, True)

    def test_import_help_text_only_in_images(self):
        self.assertEqual(ImageOptions.Import.help_text, IMAGES_IMPORT_HELP_TEXT)
        self.assertIn('Transparent zoomable', ImageOptions.Import.help_text)
        self.assertIn('Transparent derivatives', ImageOptions.Import.help_text)
        self.assertNotIn('Transparent', getattr(VideoOptions.Import, 'help_text', '') or '')

    def test_admin_fieldset_contains_flags(self):
        fields = []
        for _name, opts in ImageAdmin.fieldsets:
            for f in opts['fields']:
                fields.extend(f if isinstance(f, (list, tuple)) else [f])
        self.assertIn('transparent_zoomable', fields)
        self.assertIn('transparent_derivatives', fields)


class TransparentResourcesTest(SimpleTestCase):
    '''C11/C12: png lookup for JPG resources and png original (AC8, AC10)'''

    def test_jpg_managers_of_image_archive_accept_png(self):
        for name in ('large', 'screen', 'medium', 'thumbs', 'news', 'publicationjpg',
                     'banner1920', 'screen640', 'pl_screen', 'pl_thumbs'):
            self.assertEqual(getattr(Image.Archive, name).exts, ['jpg', 'png'], name)
        # Global types not modified
        self.assertEqual(types.JpegType.exts, ['jpg'])
        self.assertEqual(types.LargeJpegType.exts, ['jpg'])
        # Non JPG managers unchanged
        self.assertEqual(Image.Archive.publicationtiff.exts, ['tif'])

    def test_original_scan_directories_accept_png(self):
        exts = dict(ImageOptions.Import.scan_directories)['original']
        self.assertIn('.png', exts)
        for ext in ('.tif', '.psb', '.jpg'):
            self.assertIn(ext, exts)

    def test_resource_url_follows_existing_file(self):
        tmp = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=tmp):
                screen_dir = os.path.join(tmp, Image.Archive.Meta.root, 'screen')
                os.makedirs(screen_dir)
                img = Image(id='qa-transp')
                open(os.path.join(screen_dir, 'qa-transp.png'), 'w').close()
                self.assertTrue(img.resource_screen.url.endswith('screen/qa-transp.png'))
                img = Image(id='qa-transp')
                open(os.path.join(screen_dir, 'qa-transp.jpg'), 'w').close()
                # jpg has priority when both exist
                self.assertTrue(img.resource_screen.url.endswith('screen/qa-transp.jpg'))
        finally:
            shutil.rmtree(tmp)


class TransparentModelTest(TestCase):
    '''C1/C2: model fields persisted (AC2, AC12)'''

    def test_fields_default_false(self):
        img = Image(id='qa-transp')
        self.assertIs(img.transparent_zoomable, False)
        self.assertIs(img.transparent_derivatives, False)

    def test_fields_persist_in_db(self):
        Image.objects.filter(pk='qa-transp').delete()
        img = Image(id='qa-transp', title='QA transparent', priority=0)
        img.transparent_zoomable = True
        img.transparent_derivatives = True
        # bulk_create: no post_save signals (they enqueue celery tasks with DEBUG=False)
        Image.objects.bulk_create([img])
        img = Image.objects.get(pk='qa-transp')
        self.assertIs(img.transparent_zoomable, True)
        self.assertIs(img.transparent_derivatives, True)


def _run(args):
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding='utf8', check=True).stdout.strip()


def _make_rgba_png(path, width, height, with_icc=False):
    '''PNG RGBA: left half opaque red, right half fully transparent'''
    args = ['convert', '-size', '%dx%d' % (width, height), 'xc:none', '-fill', 'red',
            '-draw', 'rectangle 0,0 %d,%d' % (width // 2 - 1, height - 1)]
    if with_icc:
        # preserve-iCCP: write the iCCP chunk instead of the sRGB chunk
        args += ['-profile', SRGB_PROFILE, '-define', 'png:preserve-iCCP=true']
    args += ['PNG32:%s' % path]
    _run(args)


@skipUnless(HAS_VIPS and HAS_IM, 'vips/ImageMagick not available')
class TransparentZoomableIntegrationTest(SimpleTestCase):
    '''C6/C7 real vips dzsave (AC3, AC4, AC5, AC6)'''

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def _zoomify(self, with_icc, transparent):
        src = os.path.join(self.tmp, 'src-%s.png' % with_icc)
        _make_rgba_png(src, 600, 300, with_icc=with_icc)
        if with_icc:
            self.assertIn('icc-profile-data', _run(['vipsheader', '-a', src]))
        work = tempfile.mkdtemp(dir=self.tmp)
        dest = tempfile.mkdtemp(dir=self.tmp)
        archive = SimpleNamespace(pk='qa-transp', resource_original=SimpleNamespace(path=src))
        _generate_zoomify_vips(archive, work, dest, transparent=transparent)
        target = os.path.join(dest, 'zoomable', 'qa-transp')
        self.assertTrue(os.path.exists(os.path.join(target, 'ImageProperties.xml')))
        groups = [d for d in os.listdir(target) if d.startswith('TileGroup')]
        self.assertTrue(groups)
        tiles = []
        for g in groups:
            tiles += [os.path.join(target, g, f) for f in os.listdir(os.path.join(target, g))]
        self.assertTrue(tiles)
        return tiles

    def _assert_png_tiles(self, tiles):
        for t in tiles:
            self.assertTrue(t.endswith('.png'), t)
        # Tile 0-0-0 covers the full (downscaled) image, it must have alpha
        top = [t for t in tiles if os.path.basename(t) == '0-0-0.png'][0]
        self.assertEqual(_run(['vipsheader', '-f', 'bands', top]), '4')
        self.assertEqual(_run(['identify', '-format', '%[opaque]', top]).lower(), 'false')

    def test_transparent_png_tiles_without_icc(self):
        self._assert_png_tiles(self._zoomify(with_icc=False, transparent=True))

    def test_transparent_png_tiles_with_icc(self):
        self._assert_png_tiles(self._zoomify(with_icc=True, transparent=True))

    def test_default_jpg_tiles(self):
        tiles = self._zoomify(with_icc=False, transparent=False)
        for t in tiles:
            self.assertTrue(t.endswith('.jpg'), t)


@skipUnless(HAS_VIPS and HAS_IM, 'vips/ImageMagick not available')
class TransparentDerivativesIntegrationTest(TestCase):
    '''C7-C10 real process_image_derivatives (AC4, AC5, AC7, AC8, AC9, AC10)'''

    PK = 'qa-transp'

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.media = os.path.join(self.tmp, 'media')
        self.root = os.path.join(self.media, Image.Archive.Meta.root)
        original_dir = os.path.join(self.root, 'original')
        os.makedirs(original_dir)
        _make_rgba_png(os.path.join(original_dir, '%s.png' % self.PK), 4200, 2100, with_icc=True)
        override = override_settings(MEDIA_ROOT=self.media, DP_IMAGES_ZOOMIFY_WITH_VIPS=True)
        override.enable()
        self.addCleanup(override.disable)

    def _process(self, formats, **flags):
        archive = Image(id=self.PK, title='QA', priority=0, **flags)
        work = tempfile.mkdtemp(dir=self.tmp)
        with mock.patch.object(Image.objects, 'get', return_value=archive):
            process_image_derivatives('media', 'image', self.PK, formats, None, work, None)
        return archive

    def _path(self, fmt, ext):
        return os.path.join(self.root, fmt, '%s.%s' % (self.PK, ext))

    def _opaque(self, path):
        return _run(['identify', '-format', '%[opaque]', path]).capitalize()

    def test_transparent_derivatives_png_with_alpha_and_back_to_jpg(self):
        # Stale jpg from a previous non transparent import (C10)
        os.makedirs(os.path.join(self.root, 'screen'))
        open(self._path('screen', 'jpg'), 'w').close()

        # publicationtiff is listed explicitly: if it is not, the cutter caches
        # resource_publicationtiff_only_local_files as None before generating it
        # and skips screen/thumbs (pre-existing behaviour, unrelated to this feature)
        formats = ['publicationtiff', 'screen', 'thumbs']
        self._process(formats, transparent_derivatives=True)

        # Intermediate TIFF keeps alpha (P3)
        self.assertTrue(os.path.exists(self._path('publicationtiff', 'tif')))
        self.assertEqual(self._opaque(self._path('publicationtiff', 'tif')), 'False')
        for fmt in ('screen', 'thumbs'):
            self.assertTrue(os.path.exists(self._path(fmt, 'png')), fmt)
            self.assertFalse(os.path.exists(self._path(fmt, 'jpg')), fmt)
            self.assertEqual(self._opaque(self._path(fmt, 'png')), 'False', fmt)
        self.assertTrue(Image(id=self.PK).resource_screen.url.endswith('/screen/%s.png' % self.PK))

        # Disabling the flag goes back to jpg and removes the png (AC9, C10)
        self._process(formats, transparent_derivatives=False)
        for fmt in ('screen', 'thumbs'):
            self.assertTrue(os.path.exists(self._path(fmt, 'jpg')), fmt)
            self.assertFalse(os.path.exists(self._path(fmt, 'png')), fmt)
            self.assertEqual(self._opaque(self._path(fmt, 'jpg')), 'True', fmt)
        self.assertEqual(self._opaque(self._path('publicationtiff', 'tif')), 'True')
        self.assertTrue(Image(id=self.PK).resource_screen.url.endswith('/screen/%s.jpg' % self.PK))

    def test_skipped_larger_format_removes_stale_jpg_and_png(self):
        # D1 regression: a format skipped because it is larger than the original
        # (and not upscaled) must remove <pk>.<ext> for every ext of the manager,
        # not only the ext of the current mode. screen has upscale=True (it is
        # never skipped), so publicationjpg (size 4000, upscale False) is used.
        fmt = Image.Archive.publicationjpg
        self.assertFalse(fmt.type.upscale)
        self.assertTrue(imagemagick._format_is_gte_width_height(fmt, 1000, 500))
        original = os.path.join(self.root, 'original', '%s.png' % self.PK)
        os.remove(original)
        _make_rgba_png(original, 1000, 500)
        # Stale jpg from a previous non transparent import with a bigger original
        os.makedirs(os.path.join(self.root, 'publicationjpg'))
        open(self._path('publicationjpg', 'jpg'), 'w').close()

        self._process(['publicationjpg'], transparent_derivatives=True)

        self.assertFalse(os.path.exists(self._path('publicationjpg', 'jpg')))
        self.assertFalse(os.path.exists(self._path('publicationjpg', 'png')))
        self.assertIsNone(Image(id=self.PK).resource_publicationjpg)

    def _tiles(self):
        target = os.path.join(self.root, 'zoomable', self.PK)
        self.assertTrue(os.path.exists(os.path.join(target, 'ImageProperties.xml')))
        tiles = []
        for g in os.listdir(target):
            if g.startswith('TileGroup'):
                tiles += os.listdir(os.path.join(target, g))
        self.assertTrue(tiles)
        return tiles

    def test_regenerate_zoomable_follows_flag(self):
        self._process(['zoomable'], transparent_zoomable=True)
        self.assertTrue(all(t.endswith('.png') for t in self._tiles()))
        self._process(['zoomable'], transparent_zoomable=False)
        self.assertTrue(all(t.endswith('.jpg') for t in self._tiles()))

    def test_zoomable_without_vips_warns_and_uses_imagemagick(self):
        with override_settings(DP_IMAGES_ZOOMIFY_WITH_VIPS=False), \
                mock.patch.object(imagemagick, '_generate_zoomify') as gen, \
                mock.patch.object(imagemagick, '_generate_zoomify_vips') as gen_vips, \
                self.assertLogs(imagemagick.logger, level='WARNING') as logs:
            self._process(['zoomable'], transparent_zoomable=True)
        gen.assert_called_once()
        gen_vips.assert_not_called()
        self.assertTrue(any('requires DP_IMAGES_ZOOMIFY_WITH_VIPS' in m for m in logs.output))
