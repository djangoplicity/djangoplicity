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

"""
Display helpers for press release archive
"""

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_noop


def releaseid( obj ):
    """
    Display helper for showing a release number
    """
    return obj.id
releaseid.short_description = ugettext_noop( 'Release No.' )


def oldreleaseids( obj ):
    """
    Display helper for showing a legacy id
    """
    if obj.old_ids:
        return obj.old_ids
    else:
        return ''
oldreleaseids.short_description = ugettext_noop( 'Legacy ID' )


def telbib( obj ):
    """
    Display helper for showing a link to ESO's Telescop Bibliography
    """
    pubs = obj.publications.all()
    if len( pubs ) > 0:
        pubsstr = []
        for p in pubs:
            pubsstr.append( """<a href="%s">%s</a>""" % ( p.get_absolute_url(), p.bibcode ) )
        return mark_safe( "<br />".join( pubsstr ) )
    else:
        return ""
telbib.short_description = ugettext_noop( "Science data" )
