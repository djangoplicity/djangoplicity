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

from __future__ import division
from builtins import str
from past.utils import old_div
import codecs
import datetime
import os
import piexif
import shutil
import stat
import tempfile
import time
from hashlib import md5
from subprocess import Popen, PIPE, call
from zipfile import ZipFile

from apiclient.errors import HttpError
from celery import current_app
from celery.task import task
from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from djangoplicity.archives.contrib.serialization import XMPEmitter
from djangoplicity.archives.resources import get_instance_resource, ResourceError
from djangoplicity.archives.tasks import compute_checksums
from djangoplicity.celery.serialtaskset import str_keys
from djangoplicity.cutter.imagemagick import identify_image
from djangoplicity.media.consts import MP4BOX_PATH, MP4FRAGMENT_PATH
from djangoplicity.media.audio_tasks import encode_audio_derivatives, \
    get_audio_duration
from djangoplicity.metadata.consts import get_file_type
from djangoplicity.utils.history import add_admin_history
from djangoplicity.utils.templatetags.djangoplicity_text_utils import remove_html_tags

LOCK_EXPIRE = 60 * 30  # 30 mins

logger = get_task_logger(__name__)


@task( name="media.image_extras", ignore_result=True )
def image_extras( image_id, sendtask_callback=None, sendtask_tasksetid=None ):
    """
    Celery task to determine extra information about an image after
    saving. This allows speeding up the save queries.
    """
    from djangoplicity.media.models import Image

    # We sleep for 30s to give enough time for NFS to catch in case the
    # sync task will run on a different server, otherwise we have the risk
    # of getting the information from the placeholder file
    time.sleep(30)

    try:
        # Load image
        im = Image.objects.get( id=image_id )
        logger.debug( "Found image %s " % ( im.id ) )

        try:
            original_file = im.resource_original.path
            update_fields = []
            fields = {}

            if original_file:
                # File size/type
                fields['file_size'] = int( old_div(os.path.getsize( original_file ), 1024) )

                fields['file_type'] = get_file_type( original_file )

                w, h = identify_image(im.resource_original.path)
                fields['width'] = w
                fields['height'] = h

                # Set spatial_reference_dimension if empty
                if not im.spatial_reference_dimension:
                    fields['spatial_reference_dimension'] = '%s;%s' % \
                            (float(w), float(h))

                fields['n_pixels'] = fields['width'] * fields['height']

                for key, value in list(fields.items()):
                    if value != getattr(im, key):
                        setattr(im, key, value)
                        update_fields.append(key)

                # We specify which fields to save to prevent overwriting
                # any changes that might have happen since we read from
                # the DB
                if update_fields:
                    im.save(run_tasks=False, update_fields=update_fields)
                    add_admin_history(im, 'media.image_extras updated: %s' %
                        ', '.join(update_fields))
        except AttributeError:
            pass
    except Image.DoesNotExist:
        logger.warning( "Could not find image %s." % image_id )

    # send_task callback
    if sendtask_callback:
        # pylint: disable=W0633
        args, kwargs = sendtask_callback
        current_app.send_task( *args, **str_keys( kwargs ) )


@task(name='media.video_extras', ignore_result=True)
def video_extras(app_label, model_name, pk, sendtask_callback=None, sendtask_tasksetid=None):
    """
    Celery task to determine extra information about an video after
    saving. This allows speeding up the save queries.
    """
    try:
        # Load video
        cls = apps.get_model(app_label, model_name)
        v = cls.objects.get(pk=pk)

        logger.debug("Found video %s " % (v.pk))
        update_fields = []
        fields = {}

        # Identify the format with the largest resolution
        for resource in ('cylindrical_16kmaster', 'dome_8kmaster', 'cylindrical_8kmaster', 'vr_8k', 'vr_4k', 'dome_4kmaster', 'cylindrical_4kmaster', 'ultra_hd_broadcast', 'ultra_hd', 'dome_2kmaster', 'hd_1080p25_screen', 'hd_1080_screen', 'hd_1080_broadcast', 'dome_preview', 'hd_broadcast_720p25', 'hd_and_apple', 'large_qt', 'broadcast_sd', 'medium_flash', 'medium_podcast', 'medium_mpeg1', 'qtvr', 'ext_highres', 'ext_playback', 'old_video'):
            try:
                r = getattr(v, 'resource_' + resource)
                if not r:
                    continue
                path = r.path
            except AttributeError:
                continue

            if resource in ('cylindrical_16kmaster', 'cylindrical_8kmaster', 'cylindrical_4kmaster', 'dome_8kmaster', 'dome_4kmaster', 'dome_2kmaster') and path.endswith('.zip'):
                # dome_xkmaster and cylindrical_xkmaster formats are a .zip
                # file of .jpg, which can't be read by mplayer, but their
                # resolution is known and we count the number of included files
                # to get the duration (divided by the frame rate)

                if r.size == 0:
                    # This should not happen, unless we have some "fake"
                    # files on the volume which are served by the CDN
                    # but only there locally so that Djangoplicity sees them
                    continue

                z = ZipFile(path)

                # Divide the number of includes files (frames) by the framerate
                # to get the duration in seconds
                fields['file_duration'] = old_div(len(z.infolist()), v.frame_rate)

                # Assume the width and height is 8k, 4k or 2k unless it's already set
                if resource == 'dome_8kmaster':
                    fields['width'] = v.width or 8192
                    fields['height'] = v.height or 8192
                elif resource == 'dome_4kmaster':
                    fields['width'] = v.width or 4096
                    fields['height'] = v.height or 4096
                elif resource == 'dome_2kmaster':
                    fields['width'] = v.width or 2048
                    fields['height'] = v.height or 2048
                elif resource == 'cylindrical_16kmaster':
                    fields['width'] = v.width or 16384
                    fields['height'] = v.height or 8192
                elif resource == 'cylindrical_8kmaster':
                    fields['width'] = v.width or 8192
                    fields['height'] = v.height or 4096
                elif resource == 'cylindrical_4kmaster':
                    fields['width'] = v.width or 4096
                    fields['height'] = v.height or 2048
            else:
                # Use midentify to fetch a dict of key/values about the file
                args = ['/usr/bin/mplayer', '-noconfig', 'all', '-cache-min', '0', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify', path]
                try:
                    output = Popen(args, stdout=PIPE, stderr=PIPE).communicate()[0].split('\n')
                except OSError as e:
                    logger.error('Can\'t run mplayer identify command: "%s"' % ' '.join(args))
                    raise e
                output_d = dict([data.split('=') for data in output if data.startswith('ID_')])

                try:
                    fields['width'] = int(output_d['ID_VIDEO_WIDTH'])
                    fields['height'] = int(output_d['ID_VIDEO_HEIGHT'])
                    fields['file_duration'] = float(output_d['ID_LENGTH'])
                except KeyError as e:
                    logger.warning('mplayer could not detect {} for video {} '
                        ', format {}'.format(e, pk, resource))

                    continue

            # Convert the duration from seconds to h:mm:ss, we happen :000 at the
            # end to ignore the extra frames.
            # We use int(duration) to drop the microseconds
            fields['file_duration'] = str(datetime.timedelta(seconds=int(fields['file_duration']))) + ':000'

            for key, value in list(fields.items()):
                if value != getattr(v, key):
                    setattr(v, key, value)
                    update_fields.append(key)

            if update_fields:
                v.save(run_tasks=False, update_fields=update_fields)
                add_admin_history(v, 'media.video_extras updated: %s' %
                    ', '.join(update_fields))

            break

        else:
            # No format found
            logger.exception('No video format could be found to identify resolution for "%s"' % pk)
    except cls.DoesNotExist:
        logger.warning("Could not find video %s." % pk)

    # send_task callback
    if sendtask_callback:
        # pylint: disable=W0633
        args, kwargs = sendtask_callback
        current_app.send_task(*args, **str_keys(kwargs))


@task( name="media.image_color", ignore_result=True )
def image_color( image_id, sendtask_callback=None, sendtask_tasksetid=None ):
    """
    Celery task to determine color of image.
    """
    from djangoplicity.media.models import Image, Color

    try:
        # Load image
        im = Image.objects.get( id=image_id )
        logger.debug( "Found image %s " % ( im.id ) )

        # Determine color of image.
        if not im.colors.all():
            imcolors = Color.create_dominant_colors( im, 'resource_medium' )
            if imcolors:
                for imc in imcolors:
                    imc.save()
    except Image.DoesNotExist:
        logger.warning( "Could not find image %s." % image_id )

    # send_task callback
    if sendtask_callback:
        # pylint: disable=W0633
        args, kwargs = sendtask_callback
        current_app.send_task( *args, **str_keys( kwargs ) )


@task(name="media.image_metadata", ignore_result=True)
def write_metadata(image_id, formats, cdn_sync=True):
    """
    Celery task for writing AVM metadata to file.
    """
    if settings.SITE_ENVIRONMENT != 'prod':
        logger.info('%s only runs on a production system', write_metadata.__name__)
        return

    # Imports
    from djangoplicity.media.models import Image
    from djangoplicity.media.serializers import AVMImageSerializer
    from libavm.utils import avm_to_file

    try:
        # Load image
        im = Image.objects.get(id=image_id)
        logger.debug("Found image %s " % (im.id))
    except Image.DoesNotExist:
        logger.warning("Could not find image %s." % image_id)
        return

    for fmt in formats:
        # Get image file.
        try:
            res = get_instance_resource(im, fmt)
        except ResourceError:
            logger.error("%s is not a valid resource on image instances." % fmt)
            continue

        if not res:
            logger.warning("File for resource %s does not exist for image %s." % (fmt, image_id))
            continue

        filepath = res.path

        # We can't write AVM to large PSB as it corrupts them, so we skip them:
        if res.path.endswith('.psb'):
            logger.debug("Skipping writing AVM for PSB '%s'" % fmt)
            continue

        logger.debug("Found %s resource file '%s' for image '%s'" % (fmt, filepath, image_id))

        # Serialize to AVM
        serializer = AVMImageSerializer()
        serialization = serializer.serialize(im)
        logger.debug("Serialized image %s to AVM" % image_id)

        # Get XMP
        emitter = XMPEmitter()
        avm = emitter.emit(serialization, type='AVMMeta')
        logger.debug("Generated XMP for image %s" % image_id)

        # Write AVM to file
        avm_to_file(filepath, avm.data, replace=False)
        logger.info("Wrote AVM for image %s to %s" % (image_id, filepath))

        # Write custom EXIF Camera/Make to mark the image as a 360° pano
        # for social sites:
        if fmt == 'publicationjpg' and im.fov_x == 360 and im.fov_y == 180:
            exif = piexif.dump({u'0th': {
                piexif.ImageIFD.Make: u'RICOH',
                piexif.ImageIFD.Model: u'RICOH THETA S'
            }})
            piexif.insert(exif, filepath)
            logger.info('Wrote VR EXIF to %s', filepath)

    # Re-compute the checksums
    compute_checksums('media', 'image', im.pk)

    # Synchronise with content server if necessary
    if cdn_sync:
        # We sleep for 30s to give enough time for NFS to catch in case the
        # sync task will run on a different server
        time.sleep(30)
        im.sync_content_server(delay=True)


@task(name="media.fast_start", ignore_result=True)
def fast_start(video_id, fmt, sendtask_callback=None, sendtask_tasksetid=None):
    """
    Enable fast start of video
    """
    try:
        from djangoplicity.media.models import Video
        obj = Video.objects.get(id=video_id)

        if hasattr(obj, 'resource_%s' % fmt):
            res = getattr(obj, 'resource_%s' % fmt)
            if res:
                os.system(MP4BOX_PATH + " -quiet -tmp %s -inter 500 %s" % (settings.TMP_DIR, res.path))
                logger.info('Video %s set to fast start' % video_id)
    except Exception as e:
        logger.warning("Exception: %s." % e)

    # send_task callback
    if sendtask_callback:
        # pylint: disable=W0633
        args, kwargs = sendtask_callback
        current_app.send_task(*args, **str_keys(kwargs))


@task(name="media.fragment_mp4", ignore_result=True)
def fragment_mp4(app_label, model_name, pk, fmt, sendtask_callback=None, sendtask_tasksetid=None):
    """
    Enable fragmentation of mp4 for streaming
    """
    cls = apps.get_model(app_label, model_name)

    obj = cls.objects.get(pk=pk)

    if hasattr(obj, 'resource_%s' % fmt):
        res = getattr(obj, 'resource_%s' % fmt)
        if res:
            # Create temporary file to get unique path
            f = tempfile.NamedTemporaryFile(dir=settings.TMP_DIR,
                suffix='.mp4', delete=False)
            os.chmod(f.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

            cmd = '{mp4frag} --fragment-duration 1000 {input} {output}'.format(
                mp4frag=MP4FRAGMENT_PATH, input=res.path, output=f.name
            )

            if os.system(cmd) == 0:
                shutil.move(f.name, res.path)
                logger.info('Video %s fragmented' % pk)
            else:
                logger.error('mp4fragment error for %s' % res.path)

    # send_task callback
    if sendtask_callback:
        # pylint: disable=W0633
        args, kwargs = sendtask_callback
        current_app.send_task( *args, **str_keys(kwargs))


@task( name="media.video_embed_subtitles", ignore_result=True )
def video_embed_subtitles( video_id, resource_name, sendtask_callback=None, sendtask_tasksetid=None  ):
    """
    Celery task for embedding subtitles into m4v formats
    """

    # The cache key consists of the task name and the MD5 digest
    # of the video id and format
    fmt_digest = md5('%s%s' % (video_id, resource_name)).hexdigest()
    lock_id = "video_embed_subtitles-lock-%s" % fmt_digest

    # cache.add fails if if the key already exists
    def acquire_lock():
        cache.add( lock_id, "true", LOCK_EXPIRE )

    # memcache delete is very slow, but we have to use it to take
    # advantage of using add() for atomic locking
    def release_lock():
        cache.delete( lock_id )

    if acquire_lock():
        try:
            try:
                from djangoplicity.media.models import Video

                # Load Video
                v = Video.objects.get( id=video_id )
                logger.debug( "Found video %s " % ( v.id ) )

                # Get available Video Subtitles

                vs_set = v.videosubtitle_set.all()

                if not vs_set:
                    logger.debug( "No subtitles for video %s " % ( v.id ) )
                    vs_set = []

                lang = ""
                # loop and build lang string
                first = True
                for vs in vs_set:

                    res = None
                    try:
                        res = get_instance_resource( vs, 'srt' )

                    except ResourceError:
                        logger.error( "%s is not a valid resource on video subtitles instances." % 'srt' )
                        continue

                    if res:
                        logger.info( "Found '%s' Subtitles for Video %s" % ( vs.lang, v.id ) )
                        lang += " -add %s:lang=%s:group=2%s " % ( vs.resource_srt.file, vs.lang, ":disable" if not first else '' )
                        first = False
                    else:
                        logger.warning( "File for resource 'srt' does not exist for Video Subtitle %s." % ( vs.id ) )

                # empty lang string means problems
                if not lang:
                    logger.debug( "No available subtitle files for video %s " % ( v.id ) )
                else:
                    # get video resource
                    res = None
                    try:
                        res = get_instance_resource( v, resource_name )
                    except ResourceError:
                        logger.error( "%s is not a valid resource on video instances." % resource_name )
                    except Exception as e:
                        logger.error( "Error: %s" % e )

                    file = None
                    # get video file
                    if res:
                        file = res.file
                        os.system( MP4BOX_PATH + " -add %s#video -add %s#audio %s -new %s" % ( file, file, lang, file ) )
                        logger.info( 'Subtitles muxed for %s.' % v.id )
                    else:
                        logger.error( "File for resource '%s' does not exist for Video %s." % ( resource_name, v.id ) )

            except Video.DoesNotExist:
                logger.warning( "Could not find video %s." % video_id )
        finally:
            release_lock()
    else:
        logger.warning( "Task already running for %s: %s" % (video_id, resource_name) )

    # send_task callback
    if sendtask_callback:
        # pylint: disable=W0633
        args, kwargs = sendtask_callback
        current_app.send_task( *args, **str_keys( kwargs ) )


@task(name="media.generate_top100", ignore_result=True)
def generate_top100(output_dir=''):
    from djangoplicity.media.models import Image
    from djangoplicity.media.options import ImageOptions

    qs, dummy = ImageOptions.Queries.top100.queryset(Image, ImageOptions, None)

    if not output_dir:
        logger.warning("Can't generate top 100 zip files, no output_dir given.")
        return

    for format in ('large', 'original'):
        logger.info('Generating zip file for format "%s"' % format)
        # Create temp directory
        dir = tempfile.mkdtemp()

        txt_path = os.path.join(dir, 'top100.txt')
        zip_path = os.path.join(dir, 'top100-%s.zip' % format)
        f = codecs.open(txt_path, 'w', 'utf-8')
        z = ZipFile(zip_path, 'w', allowZip64=True)

        for i, image in enumerate(qs[:100], 1):
            f.write(u'%d: %s\n' % (i, image.id))
            f.write(u'Title: %s\n' % image.title)
            f.write(u'Description: %s\n' % remove_html_tags(image.description))
            f.write(u'Credit: %s\n\n' % remove_html_tags(image.credit))

            resource = getattr(image, 'resource_%s' % format, None)
            if not resource:
                continue

            z.write(resource.path, 'top100/%s' % os.path.basename(resource.path))

        f.close()
        z.write(txt_path, 'top100/top100.txt')
        z.close()
        logger.info('Wrote zip file: "%s"' % zip_path)

#       shutil.move(zip_path, output_dir)

#       os.removedirs(dir)


@task(name='media.update_youtube_snippet')
def update_youtube_snippet(video_id):
    from djangoplicity.media.models import Video

    try:
        v = Video.objects.get(pk=video_id)
        logger.info('Updating snippet for video "%s" on YouTube (%s)' %
            (v.pk, v.youtube_video_id))
        v.update_youtube_snippet()
    except Video.DoesNotExist:
        logger.warning("Could not find video %s." % video_id)


@task(name='media.update_youtube_caption')
def update_youtube_caption(videosubtitle_id):
    from djangoplicity.media.models import VideoSubtitle

    try:
        s = VideoSubtitle.objects.get(pk=videosubtitle_id)

        if not s.published or not s.video or not s.video.youtube_video_id:
            return

        logger.info('Updating caption for "%s" on YouTube (%s)' %
            (s, s.video.youtube_video_id))
        s.update_youtube_caption(logger)
    except VideoSubtitle.DoesNotExist:
        logger.warning("Could not find videosubtitle %s." % videosubtitle_id)


@task(name="media.upload_youtube", ignore_result=True)
def upload_youtube(video_id, user_id=None):
    from djangoplicity.media.models import Video
    from djangoplicity.media.youtube import youtube_configured, \
    youtube_thumbnails_set, youtube_videos_insert, youtube_videos_resumable_upload

    user = None
    if user_id:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            pass

    def mail_user(subject, body=''):
        if user and user.email:
            send_mail(subject, body, 'no-reply@eso.org', [user.email])

    if not youtube_configured:
        logger.warning('YouTube not configured, won\'t upload "%s"', video_id)

    try:
        # Load video
        v = Video.objects.get( id=video_id )
    except Video.DoesNotExist:
        logger.warning("Could not find video %s." % video_id)
        return

    # Check if the video already has a YouTube ID
    if v.youtube_video_id:
        mail_user(
            'Video already on YouTube: %s' % video_id,
            'Video "%s" was already uploaded on YouTube as: https://www.youtube.com/watch?v=%s'
            % (video_id, v.youtube_video_id)
        )
        return

    # Identify the format with the largest resolution to upload
    path = ''
    for fmt in Video.UPLOAD_FORMATS:
        try:
            r = getattr(v, 'resource_' + fmt)
            if not r:
                continue
            logger.info('Will use format: %s' % fmt)
            path = r.path
            break
        except AttributeError:
            continue
    else:
        logger.warning('Couldn\'t find valid format to upload for "%s"' %
            video_id)

        mail_user(
            'Couldn\'t find valid format to upload "%s" to YouTube' % video_id,
            'Expected one of: %s' % ', '.join(Video.UPLOAD_FORMATS)
        )
        return

    # Prepare the body of the insert request
    body = dict(
        snippet=dict(
            title=v.get_youtube_title(),
            description=v.get_youtube_description(),
            tags=v.get_youtube_tags(),
            categoryId='28',  # Science & Technology
        ),
        status=dict(
            privacyStatus='unlisted',
            license='creativeCommon',
        )
    )

    # Some formats such as hd_and_apple use .m4v extensions which is not
    # support by YouTube, so we cheat by creating a symbolic link with .mp4
    symlink = False
    if path.endswith('.m4v'):
        target = path.replace('.m4v', '.mp4')
        os.symlink(path, target)
        symlink = True
        path = target
        logger.info('Creating symlink to bypass .m4v restriction: "%s"', target)

    # Call the API's videos.insert method to create and upload the video.
    logger.info('Found resource to upload: %s', path)
    insert_request = youtube_videos_insert(body, path)

    if symlink:
        # Remove the temporary symlink
        logger.info('Removing temporary symlink"%s"', target)
        os.remove(path)

    v.youtube_video_id = youtube_videos_resumable_upload(insert_request, logger)
    v.use_youtube = True
    v.save()

    # Set thumbnail
    if v.resource_videoframe:
        logger.info('Uploading thumbnail')
        try:
            youtube_thumbnails_set(v.youtube_video_id, v.resource_videoframe.path)
            logger.info('Thumbnail successfully uploaded')
        except HttpError as e:
            # Account doesn't have permissions to upload thumbnails, only
            # verified accounts can do so
            if e.resp['status'] == '403':
                logger.warning('No permissions to upload thumbnail')
            else:
                raise e

    add_admin_history(v, 'Uploaded to YouTube: http://youtu.be/%s' %
        v.youtube_video_id)

    mail_user('%s successfully  uploaded to YouTube: http://youtu.be/%s' %
                (v.pk, v.youtube_video_id))


@task
def process_audio_derivatives(app_label, module_name, pks, formats=None,
                                sendtask_callback=None, sendtask_tasksetid=None):
    '''
    Generate the given formats (or all applicable) for the given archives
    '''
    for pk in pks:
        # Create temporary directory
        tmp_dir = tempfile.mkdtemp(dir=settings.TMP_DIR)

        try:
            encode_audio_derivatives(app_label, module_name, pk, tmp_dir)
        finally:
            # Clean up temporary directory
            shutil.rmtree(tmp_dir)

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task(*args, **str_keys(kwargs))


@task
def audio_extras(app_label, module_name, pks, formats=None,
                                sendtask_callback=None, sendtask_tasksetid=None):
    '''
    Generate the given formats (or all applicable) for the given archives
    '''
    for pk in pks:
        get_audio_duration(app_label, module_name, pk)

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task(*args, **str_keys(kwargs))


@task(name='media.generate_thumbnail', ignore_result=True)
def generate_thumbnail(app_label, model_name, pk, sendtask_callback=None, sendtask_tasksetid=None, **kwargs):
    '''
    Generate a thumbnail if no original format is available
    '''
    cls = apps.get_model(app_label, model_name)

    try:
        # Load video
        v = cls.objects.get(pk=pk)
    except cls.DoesNotExist:
        error = 'Could not find video %s.%s %s.', app_label, model_name, pk
        logger.warning(error)
        raise Exception(error)

    force_generation = kwargs.get('force_generation', False)
    if not v.resource_original or force_generation:
        # Identify the largest useable format
        path = ''
        for fmt in cls.UPLOAD_FORMATS:
            try:
                r = getattr(v, 'resource_' + fmt)
                if not r:
                    continue
                logger.info('Will use format: %s' % fmt)
                path = r.path
                break
            except AttributeError:
                continue
        else:
            error = 'Couldn\'t find valid format to upload for "%s"', pk
            logger.warning(error)
            raise Exception(error)

        output = os.path.join(settings.MEDIA_ROOT, cls.Archive.Meta.root, 'original', pk + '.tif')

        # Takes the screenshot at 5s by default or using setting
        position = getattr(settings, 'VIDEOS_THUMBNAIL_POSITION', 5)
        if position == 'middle':
            position = int(v.duration_in_seconds() / 2)

        cmd = 'ffmpeg -ss {position} -i {input} -vframes 1 -q:v 2 {output}'.format(position=position, input=path, output=output)
        if force_generation:
            cmd += ' -y' # To overwrite image

        logger.info(cmd)
        # Check output raises and error if return code of command is not zero and returns the error as a byte string
        import subprocess
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            error = 'The command "{}" returned error: {}'.format(cmd, e.output)
            logger.warning(e)
            raise Exception(error)

        add_admin_history(v, 'Generated thumbnail from {} at {} seconds'.format(fmt, position))  # pylint: disable=undefined-loop-variable

    # Send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback
        current_app.send_task(*args, **str_keys(kwargs))


@task
def image_observation_tagging_notification(pk):
    '''
    Send an email notification if the image is marked as Observation
    '''
    from djangoplicity.media.models import Image

    try:
        i = Image.objects.get(pk=pk)
    except Image.DoesNotExist:
        return

    if i.type != 'Observation':
        return

    if i.tagging_status.filter(slug='no_coords').exists():
        return

    url = 'https://' + settings.SITE_DOMAIN + \
        reverse('admin_site:media_image_change', args=[pk])

    send_mail(
        'New Observation image: {}'.format(url),
        '',
        'no-reply@eso.org',
        ['zidmani@gmail.com'],
    )
