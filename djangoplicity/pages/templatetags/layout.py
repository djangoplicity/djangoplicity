# -*- coding: utf-8 -*-
#
# djangoplicity-pages
# Copyright (c) 2007-2018, European Southern Observatory (ESO)
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

from __future__ import unicode_literals

from django import template
from django.utils.html import format_html

from djangoplicity.media.models import Image, ImageComparison

register = template.Library()


@register.inclusion_tag('templatetags/image_frame.html')
def image_frame(**kwargs):
    pk = kwargs.get('id', None)

    try:
        obj = Image.objects.get(pk=pk)
    except Image.DoesNotExist:
        obj = None

    # If not url is given default to link to image
    url = kwargs.get('url', None)
    if url is None and obj:
        url = obj.get_absolute_url()

    # If no alt is given default to image title
    alt = kwargs.get('alt', None)
    if not alt and obj:
        alt = obj.title

    # If no credit is given default to image credit
    credit = kwargs.get('credit', None)
    if credit is None and obj:
        # We don't use "if not credit" as we may get credit = '' if
        # we don't want to show any credit
        credit = obj.credit

    return {
        'object': obj,
        'alt': alt,
        'legend': kwargs.get('legend', None),
        'credit': credit,
        'url': url,
        'position': kwargs.get('position', None),
        'width': kwargs.get('width', None),
    }


@register.inclusion_tag('templatetags/comparison_frame.html')
def comparison_frame(**kwargs):
    pk = kwargs.get('id', None)

    try:
        obj = ImageComparison.objects.get(pk=pk)
    except ImageComparison.DoesNotExist:
        obj = None

    # If no alt is given default to image title
    alt = kwargs.get('alt', None)
    if not alt and obj:
        alt = obj.title

    # If no credit is given default to image credit
    credit = kwargs.get('credit', None)
    if credit is None and obj:
        # We don't use "if not credit" as we may get credit = '' if
        # we don't want to show any credit
        credit = obj.credit

    return {
        'object': obj,
        'alt': alt,
        'legend': kwargs.get('legend', None),
        'credit': credit,
        'position': kwargs.get('position', None),
        'width': kwargs.get('width', None),
    }


@register.inclusion_tag('templatetags/static_image_frame.html')
def static_image_frame(**kwargs):
    return {
        'src': kwargs.get('src', None),
        'alt': kwargs.get('alt', None),
        'url': kwargs.get('url', None),
        'legend': kwargs.get('legend', None),
        'credit': kwargs.get('credit', None),
        'position': kwargs.get('position', None),
        'width': kwargs.get('width', None),
    }


@register.simple_tag
def spacer(height):
    return format_html('<div style="height: {}"></div>', height)


@register.simple_tag
def dropcaps(text, **kwargs):
    width = kwargs.get('width', '50%')
    position = kwargs.get('position', 'left')
    if position not in ('left', 'right', 'center'):
        position = 'left'

    return format_html('<div style="width: {}" class="drop-caps {}">{}</div>',
        width, position, text)


@register.inclusion_tag('templatetags/youtube_frame.html')
def youtube_frame(youtube_id, *args, **kwargs):
    return {
        'youtube_id': youtube_id,
        'legend': kwargs.get('legend', None),
        'credit': kwargs.get('credit', None),
        'autoplay': 'autoplay' in args,
        'mute': 'mute' in args,
    }
