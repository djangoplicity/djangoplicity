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

from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_noop
from djangoplicity.media.models import Video

register = template.Library()


def _append_site_url(url):
    if url.startswith('http') or url.startswith('//'):
        return url
    else:
        return 'http://%s%s' % (Site.objects.get_current().domain, url)


def _absolute_resource_url( video, formats ):
    """ Return the first available format. """
    formats = formats.split(",")
    for f in formats:
        try:
            resource = getattr( video, "resource_%s" % f )
            if resource:
                return _append_site_url( resource.url )
        except AttributeError:
            pass
    return None


@register.inclusion_tag( "videos/embed.html")
def embedvideo( video, sd_formats, hd_formats, mobile_formats ):
    width = "640"
    height = "360"

    return {
        # The video ID is used as javascript variable so we replace the hyphens
        'video_id': video.id.replace('-', '_'),
        'video': video,
        'sd_resource': _absolute_resource_url( video, sd_formats ),
        'hd_resource': _absolute_resource_url( video, hd_formats ),
        'ipad_resource': _absolute_resource_url( video, mobile_formats ),
        'mobile_resource': _absolute_resource_url( video, mobile_formats ),
        'SITE_URL': 'http://%s' % Site.objects.get_current().domain,
        'MEDIA_URL': settings.MEDIA_URL,
        'GA_ID': settings.GA_ID,
        'videoframe': _absolute_resource_url( video, 'videoframe' ),
        'width': width,
        'height': height,
        'social': True,
    }


@register.inclusion_tag("videos/embed.html")
def embedvideo_from_id(video_id):
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return {}

    conf = embedvideo_subs(
            video,
            'medium_podcast,h264',
            'hd_and_apple,hd720p_screen,dome_preview',
            '',
            video.videosubtitle_set.all())

    # Add the video to the djp_videos arrays (or create it if it doesn't
    # yet exist. All videos will be setup later on in the main JS
    conf['extra'] = '''
if (typeof djp_videos === 'undefined')
    var djp_videos = ['{id}'];
else
    djp_videos.push('{id}');

'''.format(id=video_id)

    return conf


@register.inclusion_tag( "videos/embed.html")
def embedvideo_subs( video, sd_formats, hd_formats, mobile_formats, subs, social=1 ):
    conf = embedvideo(video, sd_formats, hd_formats, mobile_formats)

    conf['subs'] = subs

    if social == 1:
        conf['social'] = True
    else:
        conf['social'] = False

    return conf


@register.inclusion_tag( "videos/embed.html")
def embed_custom_video( video, sd_formats, hd_formats, mobile_formats, width, height ):
    return {
        # The video ID is used as javascript variable so we replace the hyphens
        'video_id': video.id.replace('-', '_'),
        'video': video,
        'sd_resource': _absolute_resource_url( video, sd_formats ),
        'hd_resource': _absolute_resource_url( video, hd_formats ),
        'ipad_resource': _absolute_resource_url( video, mobile_formats ),
        'mobile_resource': _absolute_resource_url( video, mobile_formats ),
        'SITE_URL': 'http://%s' % Site.objects.get_current().domain,
        'MEDIA_URL': settings.MEDIA_URL,
        'GA_ID': settings.GA_ID,
        'videoframe': _absolute_resource_url( video, 'videoframe' ),
        'width': width,
        'height': height,
        'social': True,
    }


@register.inclusion_tag( "videos/playlist.html")
def embed_playlist(videos, sd_formats, hd_formats):

    playlist = [
        (
            video.title,
            video.headline,
            _absolute_resource_url(video, 'videoframe'),
            _absolute_resource_url(video, sd_formats),
            _absolute_resource_url(video, hd_formats),
            video.videosubtitle_set.all()
        ) for video in videos
    ]

    return {
        'playlist': playlist
    }


@register.inclusion_tag( "videos/frame_rate.html")
def frame_rate(resources_groups):
    # TODO: Calculate the correct video frame rate
    value = 29.97
    name = ugettext_noop("Frame rate")

    if isinstance(resources_groups, list):
        for resource in resources_groups:
            if resource['downloads'] and resource['name'] == ugettext_noop('Fulldome'):
                value = 30

    return {
        'name': name,
        'value': value
    }
