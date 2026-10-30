# -*- coding: utf-8 -*-
#
# djangoplicity-media
#
# Generation of video derivatives from the master file using ffmpeg.
# The master file (VIDEOS_MASTER_FORMAT) is used to generate the formats in
# VIDEOS_DERIVED_FORMATS (and optionally VIDEOS_PORTRAIT_FORMATS) when they
# don't already exist.

import logging
import os
import shutil
import stat
from subprocess import PIPE, Popen

from django.apps import apps
from django.conf import settings

from djangoplicity.archives.utils import wait_for_resource
from djangoplicity.contentserver.tasks import download_from_content_server
from djangoplicity.utils.history import add_admin_history
from djangoplicity.media.consts import FFMPEG_PATH, VIDEOS_MASTER_FORMAT, \
    VIDEOS_DERIVED_FORMATS, VIDEOS_PORTRAIT_FORMATS

logger = logging.getLogger(__name__)

# Options shared by all the formats: source framerate is preserved
# automatically (unless FPS_2997 is used), -y forces overwrite, -nostdin prevents background process
# stalling, -loglevel warning keeps stderr for warnings and errors only
FFMPEG_DEFAULTS = ['-y', '-nostdin', '-hide_banner', '-loglevel', 'warning']
BT709 = ['-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709']
AAC_AUDIO = ['-c:a', 'aac', '-b:a', '320k']
# HD and portrait formats are always 29.97 fps
FPS_2997 = ['-r', '30000/1001']
# Crop the central 9:16 part of the master (even width) and scale it to 1080x1920
PORTRAIT_CROP = 'crop=trunc(ih*9/16/2)*2:ih,scale=1080:1920:flags=spline'

# Extension and ffmpeg output options for each derived format
# (based on scripts/encode_UHD_and_HD_formats.sh)
FFMPEG_FORMATS = {
    # 4K Ultra HD Preview H.264 (40 Mbps, 8-bit)
    'ultra_hd': ('mp4', [
        '-c:v', 'libx264', '-vf', 'format=yuv420p',
        '-b:v', '40M', '-maxrate', '40M', '-bufsize', '80M',
    ] + BT709 + AAC_AUDIO + ['-movflags', '+faststart']),

    # 4K Ultra HD Preview H.265 (45 Mbps, 10-bit Main 10)
    'ultra_hd_h265': ('mp4', [
        '-c:v', 'libx265', '-profile:v', 'main10', '-vf', 'format=yuv420p10le',
        '-tag:v', 'hvc1', '-x265-params', 'log-level=error',
        '-b:v', '45M', '-maxrate', '45M', '-bufsize', '90M',
    ] + BT709 + AAC_AUDIO + ['-movflags', '+faststart']),

    # Full HD Preview 1080p H.264 (8 Mbps, 8-bit, 29.97 fps)
    'hd_1080_screen': ('mp4', [
        '-c:v', 'libx264', '-vf', 'scale=1920:1080:flags=spline,format=yuv420p',
        '-b:v', '8M', '-maxrate', '8M', '-bufsize', '16M',
    ] + FPS_2997 + BT709 + AAC_AUDIO + ['-movflags', '+faststart']),

    # Full HD Broadcast 1080p (Apple ProRes 422 HQ, 29.97 fps)
    'hd_1080_broadcast': ('mov', [
        '-c:v', 'prores_ks', '-profile:v', '3', '-vendor', 'apl0',
        '-vf', 'scale=1920:1080:flags=spline,format=yuv422p10le',
    ] + FPS_2997 + BT709 + ['-c:a', 'pcm_s24le']),

    # HD Portrait 1080x1920 H.264 (20 Mbps, 8-bit, 29.97 fps), center crop of the master
    'portrait_hd': ('mp4', [
        '-c:v', 'libx264', '-vf', PORTRAIT_CROP + ',format=yuv420p',
        '-b:v', '20M', '-maxrate', '20M', '-bufsize', '40M',
    ] + FPS_2997 + BT709 + AAC_AUDIO + ['-movflags', '+faststart']),

    # HD Portrait Broadcast 1080x1920 (Apple ProRes 422 HQ, 29.97 fps), center crop of the master
    'portrait_hd_broadcast': ('mov', [
        '-c:v', 'prores_ks', '-profile:v', '3', '-vendor', 'apl0',
        '-vf', PORTRAIT_CROP + ',format=yuv422p10le',
    ] + FPS_2997 + BT709 + ['-c:a', 'pcm_s24le']),
}


def get_master_path(obj):
    '''
    Return the local path of the master file for the given video or None
    if it is not available. We wait for the resource in case the NFS share is
    slow to update, and download it from the content server if it is not
    available locally (e.g. removed by cleanup_old_local_resources)
    '''
    resource = wait_for_resource(obj, VIDEOS_MASTER_FORMAT)
    if not resource:
        return None

    if not os.path.exists(resource.path) and getattr(obj, 'content_server', None):
        logger.info('Master file "%s" not found locally, downloading from content server',
            resource.path)
        download_from_content_server(
            obj.__module__,
            obj.__class__.__name__,
            obj.pk,
            formats=[VIDEOS_MASTER_FORMAT],
            include_directories=False,
        )

    if not os.path.exists(resource.path):
        logger.error('Master file "%s" is not available locally nor in the content server',
            resource.path)
        return None

    return resource.path


def get_formats_to_generate(obj, formats=None, imported_formats=None,
        generate_portrait=False, replace_formats=False):
    '''
    Return the list of formats to generate for the given video:
    - If formats is given (e.g. from the admin) those are generated
    - Otherwise the derived formats (plus the portrait formats if
      generate_portrait is True) which were not imported together with the
      master and which don't already exist, unless replace_formats is True
    '''
    if formats:
        return list(formats)

    candidates = list(VIDEOS_DERIVED_FORMATS)
    if generate_portrait:
        candidates += VIDEOS_PORTRAIT_FORMATS

    imported_formats = imported_formats or []

    fmts = []
    for fmt in candidates:
        # Never overwrite a format imported together with the master
        if fmt in imported_formats:
            continue

        if not replace_formats and getattr(obj, 'resource_' + fmt, None):
            logger.info('Video "%s" already has "%s", skipping', obj.pk, fmt)
            continue

        fmts.append(fmt)

    return fmts


def get_ffmpeg_args(fmt, master_path, output_path):
    '''
    Return the ffmpeg command (as a list of arguments) to generate the
    given format from the master file, or None if the format is not supported
    '''
    try:
        _ext, options = FFMPEG_FORMATS[fmt]
    except KeyError:
        return None

    return [FFMPEG_PATH] + FFMPEG_DEFAULTS + ['-i', master_path] + options + [output_path]


def run_ffmpeg(args):
    '''
    Run the given ffmpeg command, log the errors and return True on success,
    False on failure
    '''
    logger.info('Running: %s', ' '.join(args))

    try:
        proc = Popen(args, stdout=PIPE, stderr=PIPE, encoding='utf8')
    except OSError as e:
        logger.error('Could not run ffmpeg (%s): %s', e, ' '.join(args))
        return False

    _stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        logger.error('ffmpeg failed (exit=%s): %s%s', proc.returncode,
            ' '.join(args), '\nstderr: %s' % stderr.strip() if stderr.strip() else '')
        return False

    # With -loglevel warning, stderr only contains warnings on success
    if stderr.strip():
        logger.warning('ffmpeg warnings (%s): %s', ' '.join(args), stderr.strip())

    return True


def generate_format(obj, fmt, master_path, tmp_dir):
    '''
    Generate the given format from the master file in tmp_dir/<fmt>/<pk>.<ext>
    and move it to the archive. Returns True on success, False on failure
    '''
    if fmt not in FFMPEG_FORMATS:
        logger.warning('No ffmpeg options defined for "%s", skipping', fmt)
        return True

    ext = FFMPEG_FORMATS[fmt][0]
    output_dir = os.path.join(tmp_dir, fmt)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '%s.%s' % (obj.pk, ext))

    logger.info('Generating "%s" for video "%s"', fmt, obj.pk)

    if not run_ffmpeg(get_ffmpeg_args(fmt, master_path, output_path)):
        return False

    # ffmpeg can exit with 0 and still not write a valid file
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        logger.error('ffmpeg did not generate "%s" for video "%s": %s',
            fmt, obj.pk, output_path)
        return False

    # Move the output file to the archive
    fmt_dir = os.path.join(settings.MEDIA_ROOT, obj.Archive.Meta.root, fmt)
    os.makedirs(fmt_dir, exist_ok=True)
    dest_path = os.path.join(fmt_dir, os.path.basename(output_path))
    shutil.move(output_path, dest_path)

    # Make sure permissions are correct
    os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    logger.info('Generated "%s" for video "%s": %s', fmt, obj.pk, dest_path)
    add_admin_history(obj, 'Generated %s from %s' % (fmt, VIDEOS_MASTER_FORMAT))

    return True


def process_video_derivatives(app_label, model_name, pk, formats=None,
        imported_formats=None, tmp_dir=None, user_id=None,
        generate_portrait=False, replace_formats=False):
    '''
    Generate the video derivatives from the master file, temporary files are
    created in tmp_dir. The caller is responsible for the cleanup.
    '''
    # We only process derivatives if the master has changed, if e.g.
    # only hd_1080_screen was imported then we do nothing
    if imported_formats and VIDEOS_MASTER_FORMAT not in imported_formats:
        logger.info('"%s" not in the list of imported formats (%s), skipping',
            VIDEOS_MASTER_FORMAT, ', '.join(imported_formats))
        return

    model = apps.get_model(app_label, model_name)

    try:
        obj = model.objects.get(pk=pk)
    except model.DoesNotExist:
        logger.warning('Could not find %s.%s "%s"', app_label, model_name, pk)
        return

    master_path = get_master_path(obj)
    if not master_path:
        logger.warning('Video "%s" has no master file (%s), skipping derivatives',
            pk, VIDEOS_MASTER_FORMAT)
        return

    fmts = get_formats_to_generate(obj, formats, imported_formats,
        generate_portrait, replace_formats)
    if not fmts:
        logger.info('Video "%s" has all derivatives already, nothing to do', pk)
        return

    logger.info('Generating derivatives for video "%s" from "%s": %s',
        pk, master_path, ', '.join(fmts))

    # We try to generate all the formats even if one fails
    failed = [fmt for fmt in fmts if not generate_format(obj, fmt, master_path, tmp_dir)]

    # Make sure the new files are found
    obj.clear_resource_cache()

    if failed:
        raise Exception('Could not generate %s for video "%s"' % (', '.join(failed), pk))

    logger.info('Finished derivatives for video "%s"', pk)
