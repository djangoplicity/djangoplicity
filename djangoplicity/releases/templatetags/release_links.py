# -*- coding: utf-8 -*-
#
# djangoplicity-releases
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

from django.conf import settings
from django.utils.safestring import mark_safe
from django import template
from django.template.defaultfilters import stringfilter
from djangoplicity.translation.models import translation_reverse
from django.utils import translation
import re
register = template.Library()

if hasattr(settings, 'RELEASE_LINK_PREFIX'):
    RELEASE_LINK_PREFIX = settings.RELEASE_LINK_PREFIX
else:
    RELEASE_LINK_PREFIX = "eso"


pattern = re.compile(r"\[\s*([0-9]+)\s*\]")
pattern_ids = re.compile(r"((\s|\())(" + RELEASE_LINK_PREFIX + r"\d(\d)*)")


@register.filter
@stringfilter
def notes_links( text ):
    (text, _n) = pattern.subn(r'<a class="anchor" name="\g<1>"></a>[\g<1>]', text )
    return mark_safe( text )


@register.filter
@stringfilter
def description_links( text ):
    (text, _n) = pattern.subn(r'<a href="#\g<1>">[\g<1>]</a>', text )
    return mark_safe( text )


def _revid( t, extra='' ):
    str = 'thisismymagic99substring'
    rev = translation_reverse( 'releases_detail', args=[str], lang=translation.get_language() )
    rev = rev.replace( str, t )
    return '%s<a href="%s">%s</a>' % ( extra, rev, t )


@register.filter
@stringfilter
def release_ids( text ):
    (text, _n) = pattern_ids.subn( _revid( r'\g<3>', extra=r'\g<2>' ), text )

    return mark_safe( text )
