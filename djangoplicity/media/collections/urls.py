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
# A URL scheme for browsing an archive with a string parameter
#
# An example of the URLs generated for category query
# for an image archive, being installed in resource/images/..
# would be::
#
#     .../archive/category/astro/
#     .../archive/category/astro/page/1/
#     .../archive/category/astro/viewall/
#     .../archive/category/astro/viewall/page/1/
#
# "astro" is here parameteres that will be passed on to
# ArchiveQuery.queryset method as the keyword argument "stringparam".

# Note: These are transformed in an array of url() in get_list_urls

from djangoplicity.archives.views import archive_list

urlpatterns_template = (
    (r'(?P<stringparam>[-\w]+)/$', archive_list, {}, "%s" ),
    (r'(?P<stringparam>[-\w]+)/%(page_prefix)s/(?P<page>[0-9]+)/$', archive_list, {}, "%s_page" ),
    (r'(?P<stringparam>[-\w]+)/(?P<viewmode_name>%(viewmodes)s)/$', archive_list, {}, "%s_viewmode" ),
    (r'(?P<stringparam>[-\w]+)/(?P<viewmode_name>%(viewmodes)s)/%(page_prefix)s/(?P<page>[0-9]+)/$', archive_list, {}, "%s_viewmode_page" ),
)
