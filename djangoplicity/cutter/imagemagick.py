# -*- coding: utf-8 -*-
#
# djangoplicity-cutter
# Copyright (c) 2007-2016, European Southern Observatory (ESO)
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

from __future__ import division
import errno
import glob
import json
import logging
import math
import os
import shutil
import stat
from collections import OrderedDict
from subprocess import PIPE, Popen

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail, mail_admins
from django.template.loader import get_template

from djangoplicity.archives.base import cache_handler
from djangoplicity.archives.resources import ImageResourceManager
from djangoplicity.archives.utils import wait_for_resource


logger = logging.getLogger(__name__)


# TODO: get path from settings?
IM_PATH = '/usr/bin/'
IM_LIMITS = '-limit memory 1GiB -limit map 1GiB -limit thread 4'
IM_TMP_DIR = settings.TMP_DIR

CONVERT_DEFAULTS = '-quiet -depth 8 -colorspace sRGB'
if os.path.isdir(IM_TMP_DIR):
    CONVERT_DEFAULTS += ' -define registry:temporary-path={}'.format(IM_TMP_DIR)

CONVERT = '%s %s %s' % (os.path.join(IM_PATH, 'convert'), IM_LIMITS, CONVERT_DEFAULTS)
IDENTIFY = '%s %s' % (os.path.join(IM_PATH, 'identify'), IM_LIMITS)

SRGB_PROFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'icc', 'sRGB-IEC61966-2.1.icc')


def _format_is_lte_size(fmt, size):
    '''
    Return True if the format dimension is less than or equal to size in
    either width, height or size
    '''
    if fmt.type.width and fmt.type.width > size:
        return False

    if fmt.type.height and fmt.type.height > size:
        return False

    if fmt.type.size and fmt.type.size > size:
        return False

    return True


def _format_is_gte_width_height(fmt, width, height):
    '''
    Return True if the format is greater or equal than width and height in
    width, height or size
    '''
    if fmt.type.width and fmt.type.width > width:
        return True

    if fmt.type.height and fmt.type.height > height:
        return True

    if fmt.type.size and fmt.type.size > max(width, height):
        return True

    return False


def _get_crop_offset(archive, fmt):
    '''
    Return the crop offset for the given archive and format
    '''
    offset = '+0+0'

    if not getattr(archive, 'crop_offsets', None):
        # Crop offsets not configured for given model or unset
        # for the given archive
        return offset

    aspect = unicode(fmt.type.width / fmt.type.height)
    offsets = json.loads(archive.crop_offsets) if archive.crop_offsets else {}

    try:
        offset = offsets[unicode(aspect)]
    except KeyError:
        return offset

    if archive.width / archive.height > fmt.type.width / fmt.type.height:
        ratio = fmt.type.height / archive.height
        return '%+d+0' % int(round(offset * ratio))
    else:
        ratio = fmt.type.width / archive.width
        return '+0%+d' % int(round(offset * ratio))


def _get_convert_args(archive, width, height, fmt, tmp_path, output_dir):
    '''
    Retuns the array of argument for the given image format
    '''
    args = CONVERT.split()

    # For small images we use -thumbnail which optimize the file size
    if _format_is_lte_size(fmt, 700):
        RESIZE = '-thumbnail'
    else:
        RESIZE = '-resize'

    # Crop/Resize
    if fmt.type.size:
        if width > height:
            args += [RESIZE, '%sx' % fmt.type.size]
        else:
            args += [RESIZE, 'x%s' % fmt.type.size]

    elif fmt.type.width and fmt.type.height:
        if width / height > fmt.type.width / fmt.type.height:
            args += [RESIZE, 'x%s' % fmt.type.height]
        else:
            args += [RESIZE, '%sx' % fmt.type.width]

        # Check if the archive has custom crop offset
        crop_offset = _get_crop_offset(archive, fmt)

        args += [
            '-gravity', 'center', '-crop',
            '%sx%s%s' % (fmt.type.width, fmt.type.height, crop_offset),
            '+repage'
        ]
    elif fmt.type.width or fmt.type.height:
        args += [
            RESIZE, '%sx%s' % (fmt.type.width or '', fmt.type.height or '')
        ]
    elif fmt.type.exts[0] == 'jpg' and (width > 65500 or height > 65500):
        # JPEG has a maximum size of 65,535×65,535 pixels
        if width > height:
            args += [RESIZE, '65500x']
        else:
            args += [RESIZE, 'x65500']

    # Unsharp
    if fmt.type.unsharp:
        # The Unsharp value correspond to the amount in % (like in Photoshop)
        # We use Radius of 1, and treshold of 0
        # https://redskiesatnight.com/2005/04/06/sharpening-using-image-magick/
        args += ['-unsharp', '1x1+%s+0' % (fmt.type.unsharp / 100.0)]

    # Compression quality
    if hasattr(fmt.type, 'compression_quality'):
        args += ['-quality', '%s' % fmt.type.compression_quality]

    # Compression type
    if hasattr(fmt.type, 'compression_type'):
        args += ['-compress', '%s' % fmt.type.compression_type]

    # Density
    if hasattr(fmt.type, 'density'):
        args += ['-density', fmt.type.density]

    # Add sRGB color profile if necessary
    args += ['-profile', SRGB_PROFILE]

    # Input file
    args += [tmp_path]

    # Output path
    output_path = os.path.join(output_dir, '%s.%s' % (archive.pk, fmt.type.exts[0]))

    if hasattr(fmt.type, 'force_format'):
        # In some cases we force a different format than the extension's default
        # e.g.: bmp defaults to BMP4 but we might want to force BMP3
        output_path = '{0}:{1}'.format(fmt.type.force_format, output_path)

    args += [output_path]

    return args


def _order_formats(model, formats):
    '''
    Return an ordered dict of name and formats ordered by their derived dependency.
    '''
    def get_derived(fmt_name):
        if fmt_name == 'original':
            return []

        fmt = getattr(model.Archive, fmt_name)

        if fmt.derived:
            return get_derived(fmt.derived) + [(fmt.name, fmt)]
        else:
            return [(fmt.name, fmt)]

    res = []
    for fmt_name in formats:
        res.extend([x for x in get_derived(fmt_name) if x not in res])

    return OrderedDict(res)


def _generate_zoomify(archive, width, height, tmp_dir, dest_dir):
    '''
    Generate a zoomify image for the given archive
    Starting from the original image we create tiles of 256x256 pixels
    We then shrink the image by 50% and create a new tier of tiles, until
    we only have one tile of <=256px
    '''
    # Check that the image is larger than 256px in at least one dimension:
    if width <= 256 and height <= 256:
        logger.info('Image too small to zoomify: %dx%d', width, height)
        return

    # Calculate the number of tiers needed
    if width > height:
        size = width
    else:
        size = height
    tiers = math.ceil(math.log((size / 256), 2))

    source = archive.resource_original.path

    tiles_dir = os.path.join(tmp_dir, 'tiles')
    if not os.path.exists(tiles_dir):
        os.makedirs(tiles_dir)

    while True:
        # Generate tiles for given tier
        logger.debug('Generating tiles for Zoomify tier %d', tiers)
        args = CONVERT.split() + [
            source, '-flatten', '-crop', '256x256', '-strip', '-set',
            'filename:tile', '%[fx:page.x/256]-%[fx:page.y/256]', '+repage',
            '+adjoin', '-quality', '85',
            '%s/%d-%%[filename:tile].jpg' % (tiles_dir, tiers)
        ]
        logger.debug(' '.join(args))

        convert = Popen(args)
        convert.communicate()

        tiers -= 1

        if tiers < 0:
            break

        # Generate source for next tier
        next_tier_source = os.path.join(tmp_dir, 'tier_%d_source.mpc' % tiers)
        args = CONVERT.split() + [
            source, '-resize', '50%', next_tier_source
        ]

        logger.debug('Generating source for tier %d', tiers)
        logger.debug(' '.join(args))
        convert = Popen(args)
        convert.communicate()

        source = next_tier_source

    zoomable_dir = os.path.join(tmp_dir, archive.pk, '')  # '' is to add trailing /
    if not os.path.exists(zoomable_dir):
        os.makedirs(zoomable_dir)

    # Get numerically sorted list of files
    def filename_to_int_list(filename):
        filename = filename.rstrip('.jpg')
        return [int(x) for x in filename.split('-')]

    def tile_cmp(x, y):
        '''
        Compare two tiles filenames, filenames are of the form:
        <tier number>-<column-number>-<row number>.jpg
        Tiles are sorted by increasing Tier number, and then by left to right,
        top top bottom
        '''
        x = filename_to_int_list(x)
        y = filename_to_int_list(y)

        if x[0] < y[0]:
            return -1

        if x[0] > y[0]:
            return 1

        if x[2] < y[2]:
            return -1

        if x[2] > y[2]:
            return 1

        if x[1] < y[1]:
            return -1

        if x[1] > y[1]:
            return 1

        return 0  # Should never happen

    fileslist = sorted(os.listdir(tiles_dir), cmp=tile_cmp)

    i = 0  # Current TileGroup index
    count = 0
    tile_group_path = ''

    for filename in fileslist:
        if count % 256 == 0:
            tile_group_path = os.path.join(zoomable_dir, 'TileGroup%d' % i)
            i += 1
            os.makedirs(tile_group_path)

        # Move the current tile in the TileGroup directory
        shutil.move(os.path.join(tiles_dir, filename), tile_group_path)

        count += 1

    # Generate XML configuration file
    template = get_template('cutter/zoomify.xml')
    with open(os.path.join(zoomable_dir, 'ImageProperties.xml'), 'w') as f:
        f.write(template.render({'width': width, 'height': height, 'numtiles': count}))

    # Remove old files and put the new files in place
    target = os.path.join(dest_dir, 'zoomable/')
    if not os.path.exists(target):
        logger.debug('Creating missing targer directory: %s', target)
        os.makedirs(target)
    old_zoomify = os.path.join(dest_dir, 'zoomable', archive.pk)
    if os.path.exists(old_zoomify):
        logger.info('Deleting old zoomify "%s"', old_zoomify)
        shutil.rmtree(old_zoomify)

    logger.debug('Moving "%s" to "%s"', zoomable_dir, target)
    shutil.move(zoomable_dir, target)


def identify_image(path):
    '''
    Returns the image resolution
    '''
    identify_args = IDENTIFY.split()
    identify_args += ['-quiet', '-format', '%w %h;', '%s' % path]

    # We use Popen instead of identify as a bug with libtiff makes it
    # return -1
    identify = Popen(identify_args, stdout=PIPE)
    output = identify.communicate()[0]  # Get stdout

    # If the TIFF file has multiple layer (or a transparent layer 0) the format
    # string will be displayed multiple time, so we end it with a semicolon
    # and use it as a separator
    width, height = output.split(';')[0].split()

    return int(width), int(height)


def process_image_derivatives(app_label, module_name, pk, formats,
        imported_formats, tmp_dir, user_id):
    '''
    Generate the given formats for Archive with pk, temporary files are
    created in tmp_dir. The caller is responsible for the cleanup.
    '''

    # We only process derivatives if original has changed, if e.g.
    # only newsfeature was imported then we do nothing
    if imported_formats and 'original' not in imported_formats:
        logging.info('"original" not in the list of imported formats (%s)'
        'skipping', ', '.join(imported_formats))
        return

    model = apps.get_model(app_label, module_name)
    user = None
    if user_id:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            pass

    msg = 'Processing %s: %s' % (module_name, pk)
    if user:
        msg += ' (for: %s)' % user
    logger.info(msg)

    if formats is None:
        # If no formats are given generate all formats
        formats = [
            x for x in dir(model.Archive)
            if isinstance(getattr(model.Archive, x), ImageResourceManager)
        ]

    ordered_formats = _order_formats(model, formats)

    try:
        archive = model.objects.get(pk=pk)
    except model.DoesNotExist:
        error = 'No archive found for %s.%s "%s"', app_label, module_name, pk
        logging.error(error)
        raise Exception(error)

    dest_dir = os.path.join(settings.MEDIA_ROOT, archive.Archive.Meta.root)

    original = wait_for_resource(archive)

    if not original:
        error = 'No original format found for "%s"', pk
        logging.error(error)
        raise Exception(error)

    # Get the original file resolution:
    width, height = identify_image(original.path)

    # We keep track of the required formats which can't be generated, and
    # formats which we have to upscale:
    missing_required = []
    upscaled_formats = []

    for fmt_name in ordered_formats.keys():
        fmt = ordered_formats[fmt_name]
        derived = fmt.derived

        if formats and fmt_name not in formats:
            # We only (re)generate formats derived from if they are asked
            # for explicitely and don't already exist
            if getattr(archive, 'resource_%s' % fmt_name):
                continue

        # TODO: 8/16 bits?

        if not derived:
            # Format is not derived
            continue

        if fmt.type.verbose_name == 'Zoomable':
            logger.info('Generating "%s" for %s', fmt.name, archive.pk)
            _generate_zoomify(archive, width, height, tmp_dir, dest_dir)
            continue

        if not fmt.type.exts:
            # This format isn't generated by Imagemagick
            continue

        logger.info('Generating "%s" for %s', fmt.name, archive.pk)

        if derived == 'original':
            source = original
        else:
            # If the original file is smaller than the derived format then
            # we use it instead
            source = getattr(archive, 'resource_%s' % derived)
            source_fmt = getattr(model.Archive, derived )

            # Use the original if it is smaller than the derived format
            if _format_is_gte_width_height(source_fmt, width, height):
                source = original
                derived = 'original'

        if not source:
            logger.debug('No source for %s (%s)', fmt_name, derived)
            continue

        # Skip formats larger than the original, unless 'upscale' is True,
        # If the format is mandatory we save it to notify the user
        if _format_is_gte_width_height(fmt, width, height):
            if not fmt.type.upscale:
                logger.info('Skipping %s, larger than original', fmt_name)

                if fmt.type.required:
                    missing_required.append(fmt_name)

                # Delete file if not generated but there
                # (from a previous other image with same id)
                try:
                    fmt_file = os.path.join(dest_dir, fmt_name, '{}.{}'.format(pk, fmt.type.exts[0]))
                    if os.path.exists(fmt_file):
                        os.remove(fmt_file)
                except OSError as e:
                    if e.errno == errno.ENOENT:
                        logger.info('%s, no such file or directory', fmt_name)
                    logger.info('format %s could not be removed from the server error', fmt_name, e.message)
                continue
            else:
                upscaled_formats.append(fmt)
                logger.info('Upscaling "%s" for format %s', archive.pk, fmt_name)

        # Create temporary MPC file
        tmp_path = os.path.join(tmp_dir, '%s-%s.mpc' % (archive.pk, derived))
        if not os.path.exists(tmp_path):
            logger.debug('Creating MPC file: %s', tmp_path)
            # -background none is to keep the transparency untouched (if any)
            args = CONVERT.split() + [source.path, '-alpha', 'Deactivate',
                '-flatten', tmp_path]
            logger.debug(' '.join(args))

            convert = Popen(args)
            convert.communicate()

        # Create output directory
        output_dir = os.path.join(tmp_dir, fmt.name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        convert_args = _get_convert_args(archive, width, height, fmt,
                            tmp_path, output_dir)

        env = {}
        if os.path.isdir(IM_TMP_DIR):
            env['MAGICK_TMPDIR'] = IM_TMP_DIR

        logger.debug('Generating "%s" from "%s": %s', fmt_name, derived,
                        ' '.join(convert_args))

        convert = Popen(convert_args, env=env)
        convert.communicate()

        # Copy the output files to the archive
        path = glob.glob(os.path.join(tmp_dir, fmt_name, '%s.*' % pk))
        if not path:
            raise Exception('Could not generate %s for "%s"' % (fmt_name, pk))

        fmt_dir = os.path.join(dest_dir, fmt_name)
        if not os.path.exists(fmt_dir):
            os.makedirs(fmt_dir)

        dest_path = os.path.join(fmt_dir, os.path.basename(path[0]))
        shutil.move(path[0], dest_path)

        # Make sure permissions are correct
        os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    subject = None
    message = None

    if missing_required:
        subject = 'Could not generate all required image formats for %s: %s'
        body = '''The following images formats could not be generated:
  %s

The original image size (%dx%d px) is too small, please replace the original
format by a higher resolution one and re-import.
'''
         # The original image size is too small
        message = body % (', '.join(missing_required), width, height)

    if upscaled_formats and not (getattr(model.Archive.Meta, 'ignore_upsale_warnings', False) or
            getattr(settings, 'DJANGOPLICITY_IGNORE_UPSCALE_WARNING', False)):
        subject = 'Please verify upscaled formats for %s: %s'
        body = '''The original image for {pk} is smaller than some of the required derived
formats, and the image was upscaled to match.

Please verify that the following images have been upscaled correctly:
'''
        for fmt in upscaled_formats:
            resource = getattr(archive, 'resource_%s' % fmt.name)

            url = resource.url
            if not (url.startswith('http') or url.startswith('//')):
                url = 'https://%s%s' % (Site.objects.get_current().domain, url)

            body += '\n - %s: %s' % (fmt.name, url)
            # Please verify that the following images have been upscaled correctly
            message = body.format(pk=pk)

    # Send mail
    if message is not None and subject is not None:
        if user and user.email:
            rcpt = user.email
            send_mail(
                subject % (module_name, pk),
                message,
                settings.DEFAULT_FROM_EMAIL,
                [rcpt],
                fail_silently=True,
            )
        else:
            mail_admins(
                subject % (module_name, pk),
                message,
                fail_silently=True,
            )

    # Clear the cache for the archive
    cache_handler(model, created=False, instance=archive)
