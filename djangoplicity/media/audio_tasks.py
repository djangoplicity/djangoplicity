# -*- coding: utf-8 -*-
#
# djangoplicity-media
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

from builtins import str
import datetime
import glob
import logging
import os
import shutil
import stat
from subprocess import Popen, PIPE

from django.apps import apps
from django.conf import settings

from djangoplicity.archives.resources import AudioResourceManager
from djangoplicity.archives.utils import wait_for_resource
from djangoplicity.utils.history import add_admin_history

logger = logging.getLogger(__name__)

FAAC = '/usr/bin/faac'


def _get_faac_args(archive, fmt, path, output_dir):
    '''
    Retuns the array of argument for the given image format
    '''
    args = FAAC.split()

    # Bitrate
    if fmt.type.bitrate:
        args += ['-b', '%d' % fmt.type.bitrate]

    # Input/Output files
    args += [
        path, '-o',
        os.path.join(output_dir, '%s.%s' % (archive.pk, fmt.type.exts[0]))
    ]

    return args


def encode_audio_derivatives(app_label, module_name, pk, tmp_dir):
    model = apps.get_model(app_label, module_name)

    logger.info('Processing %s: %s', module_name, pk)

    try:
        archive = model.objects.get(pk=pk)
    except model.DoesNotExist:
        logging.error('No archive found for %s.%s "%s"', app_label, module_name, pk)
        return

    original = wait_for_resource(archive, 'wav')

    if not original:
        logging.error('No original format found for "%s"', pk)
        return

    dest_dir = os.path.join(settings.MEDIA_ROOT, archive.Archive.Meta.root)

    # If no formats are given generate all formats
    formats = [
        getattr(model.Archive, x) for x in dir(model.Archive)
        if isinstance(getattr(model.Archive, x), AudioResourceManager)
    ]

    for fmt in formats:
        derived = fmt.derived

        if not derived:
            continue

        derived = getattr(archive, 'resource_%s' % derived)

        # Create output directory
        output_dir = os.path.join(tmp_dir, fmt.name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        faac_args = _get_faac_args(archive, fmt, derived.path, output_dir)

        logger.debug('Generating "%s" from "%s": %s', fmt.name, derived.path,
                        ' '.join(faac_args))

        with open(os.devnull, 'w') as devnull:
            convert = Popen(faac_args, stdout=devnull, stderr=devnull)
            convert.communicate()

        # Copy the output files to the archive
        path = glob.glob(os.path.join(tmp_dir, fmt.name, '%s.*' % pk))
        if not path:
            raise Exception('Could not generate %s for "%s"' % (fmt.name, pk))

        fmt_dir = os.path.join(dest_dir, fmt.name)
        if not os.path.exists(fmt_dir):
            os.makedirs(fmt_dir)

        dest_path = os.path.join(fmt_dir, os.path.basename(path[0]))
        shutil.move(path[0], dest_path)

        # Make sure permissions are correct
        os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


def get_audio_duration(app_label, module_name, pk):

    model = apps.get_model(app_label, module_name)

    logger.info('Processing %s: %s', module_name, pk)

    try:
        archive = model.objects.get(pk=pk)
    except model.DoesNotExist:
        logger.error('No archive found for %s.%s "%s"', app_label, module_name, pk)
        return

    # Search for resource in either wav, aac or mp3
    path = ''
    for resource in ('wav', 'aac', 'mp3'):
        try:
            path = getattr(archive, 'resource_%s' % resource).path
            break
        except AttributeError:
            continue

    if not path:
        logger.error('Could not find audio file for %s.%s "%s"', app_label, module_name, pk)
        return

    args = ['/usr/bin/mplayer', '-noconfig', 'all', '-cache-min', '0', '-vo', 'null', '-ao', 'null', '-frames', '0', '-identify', path]
    try:
        output = Popen(args, stdout=PIPE, stderr=PIPE).communicate()[0].split('\n')
    except OSError as e:
        logger.error('Can\'t run mplayer identify command: "%s"', ' '.join(args))
        raise e
    output_d = dict([data.split('=') for data in output if data.startswith('ID_')])
    duration = float(output_d['ID_LENGTH'])

    # Convert the duration from seconds to h:mm:ss, we happen :000 at the
    # end to ignore the extra frames.
    # We use int(duration) to drop the microseconds
    duration = str(datetime.timedelta(seconds=int(duration))) + ':000'

    if duration != archive.file_duration:
        model.objects.filter(pk=archive.pk).update(file_duration=duration)
        add_admin_history(archive, 'media.audio_extras updated: duration')
