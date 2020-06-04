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


def enable_faststart( *args ):
    """
    Action to enable fast start of a specific video format
    """
    def action( taskset, model, options, obj, data, form_values, conf={}, reimport=False ):
        """
        Action to remove old resources prior to import
        """
        for fmt in args:
            if fmt in data.get('formats', []):
                taskset.add( 'media.fast_start', args=[ obj.id, fmt ], kwargs={} )
        return taskset, conf
    return action


def fragment_mp4(*args):
    """
    Action to fragment a mp4 for streaming of a specific video format
    """
    def action(taskset, model, options, obj, data, form_values, conf={}, reimport=False):
        """
        Action to remove old resources prior to import
        """
        for fmt in args:
            if fmt in data.get('formats', []):
                taskset.add(
                    'media.fragment_mp4',
                    args=['media', 'Video', obj.pk, fmt],
                    kwargs={}
                )
        return taskset, conf
    return action


def embed_subtitles( formats ):
    """
    Import action to embed subtitles into specific formats
    """
    def action( taskset, model, options, obj, data, form_values, conf={}, reimport=False ):
        """
        Embed subtitles into format in case format requires it
        """
        for fmt in formats:
            if fmt in data.get('formats', []):
                taskset.add( 'media.video_embed_subtitles', args=[ obj.id, fmt ], kwargs={} )
        return taskset, conf
    return action


def video_extras():
    '''
    Import action to fetch resolution, etc. from video
    '''
    def action(taskset, model, options, obj, data, form_values, conf={}, reimport=False):
        taskset.add(
            'media.video_extras',
            args=['media', 'Video', obj.pk],
            kwargs={},
        )

        return taskset, conf
    return action


def upload_youtube_action():
    """
    Upload the video to Youtube
    """
    def action(taskset, model, options, obj, data, form_values, conf={}, reimport=False):
        if reimport:
            return taskset, conf

        args = [obj.pk]
        kwargs = {'user_id': conf.get('user_id')}

        taskset.add('media.upload_youtube', args=args, kwargs=kwargs)
        return taskset, conf
    return action


def generate_thumbnail_action():
    '''
    If no thumbnail (i.e. original format) is available we generate one
    '''
    def action(taskset, model, options, obj, data, form_values, conf={}, reimport=False):
        taskset.add('media.generate_thumbnail', args=['media', 'Video', obj.pk], kwargs={})
        return taskset, conf
    return action
