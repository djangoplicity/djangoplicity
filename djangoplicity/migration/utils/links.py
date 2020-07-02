# -*- coding: utf-8 -*-
#
# djangoplicity-migration
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
#

from bs4 import BeautifulSoup
from django.contrib.redirects.models import Redirect
from urlparse import urljoin, urlsplit, urlunsplit

# HTML 4.0 URI type attributes - see http://www.w3.org/TR/REC-html40/index/attributes.html
LINK_ATTRS = ['href', 'src', 'action', 'cite', 'codebase', 'data', 'longdesc', 'usemap', 'profile', ]

URI_SCHEMES = ['http', 'https', 'feed']


def redirect_list():
    """
    Obtain a list of redirects from old to new path.
    """
    redirects = {}

    objs = Redirect.objects.all()
    for obj in objs:
        redirects[obj.old_path] = obj.new_path

    return redirects


def _check_tag( tag ):
    for a in [x[0] for x in tag.attrs]:
        if a in LINK_ATTRS:
            return True
    return False


def extract_links( html ):
    """
    Extract all links from HTML
    """
    soup = BeautifulSoup( html )

    # Find all tags with an attribute that can contain links
    linktags = soup.findAll( lambda tag: _check_tag( tag )  )

    links = []

    for l in linktags:
        for a in l.attrs:
            if a[0] in LINK_ATTRS:
                links.append( a[1] )

    return links


def normalize_link( link, bases ):
    """
    Remove the base from the page.
    """
    parts = urlsplit( link )

    if parts[0] in URI_SCHEMES and parts[1] in bases:
        return urlunsplit( ('', '', '/' if parts[1] != "" and parts[2] == "" else parts[2], parts[3], parts[4]) )
    else:
        return link


def is_internal_link( link, bases ):
    """
    Filter out external links from list of links.
    """
    parts = urlsplit( link )

    if not parts[1] or parts[1] in bases:
        if (parts[0] and parts[0] in URI_SCHEMES) or not parts[0]:
            return True

    return False

    #return not reduce( lambda x, y: x or y, [link.startswith( "%s:" % s ) for s in URI_SCHEMES] )


def is_ext( link, ext, inverse=False ):
    """
    Filter out external links from list of links.
    """
    parts = urlsplit( link )

    for e in ext:
        if parts[2].endswith( e ):
            return True if not inverse else False
    return False if not inverse else True


def to_absolute_link( link, base ):
    """
    """
    return urljoin( base, link )


def replace_links( html, replacements, logger=None ):
    for r in replacements:
        if r[1][1]:
            old = r[0]
            new = r[1][0]

            if logger:
                logger.debug( "Replacing link %s with %s" % ( old, new ) )

            html = html.replace(old, new)

    return html
