# -*- coding: utf-8 -*-
#
# djangoplicity
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

from djangoplicity.archives.resources import ImageResourceManager


register = template.Library()


@register.filter
def srcset(archive):
    '''
    Returns a srcset value for the given archive with all the formats with
    original aspect ratio and fixed width
    '''

    sources = []

    for fmt_name in dir(archive.Archive):
        # Ignore pl (print layout) formats
        if fmt_name.startswith('pl_'):
            continue

        fmt = getattr(archive.Archive, fmt_name)

        # Ignore non-images or non-file based
        if not isinstance(fmt, ImageResourceManager) or not fmt.type.exts:
            continue

        # Ignore non-JPEG
        if fmt.type.content_type != 'image/jpeg':
            continue

        # Ignore cropped formats or formats with fixed height
        if fmt.type.height or not fmt.type.width:
            continue

        resource = getattr(archive, 'resource_' + fmt_name, None)
        if not resource:
            continue

        sources.append('%s %sw' % (resource.url, fmt.type.width  ))

    return ', '.join(sources)
