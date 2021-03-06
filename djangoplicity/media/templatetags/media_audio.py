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

from django import template
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

register = template.Library()


@register.inclusion_tag('audio/embed.html')
def embedaudio(archive, fmt):

    try:
        url = getattr(archive, 'resource_%s' % fmt).url
    except AttributeError:
        url = None

    return {
        # The ID is used as javascript variable so we replace the hyphens
        'archive_id': archive.id.replace('-', '_'),
        'archive': archive,
        'url': url,
        'GA_ID': settings.GA_ID,
    }


@register.filter
def human_duration(duration):
    if not duration or ':' not in duration:
        return None

    (h, m, s, _f) = duration.split(':')

    if int(h) > 0:
        return _('%(hours)s h %(minutes)s m %(seconds)s s') % {'hours': h, 'minutes': m, 'seconds': s}
    elif int(m) > 0:
        return _('%(minutes)s m %(seconds)s s') % {'minutes': m, 'seconds': s}
    else:
        return _('%(seconds)s s') % {'seconds': s}
