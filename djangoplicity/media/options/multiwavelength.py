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

from builtins import object
from django.utils.translation import ugettext_noop as _

from djangoplicity.archives.contrib import security
from djangoplicity.archives.contrib.browsers import NormalBrowser, \
    ViewAllBrowser
from djangoplicity.archives.contrib.info import admin_edit_for_site, \
    priority, published, release_date
from djangoplicity.archives.contrib.queries import AllPublicQuery, \
    EmbargoQuery, StagingQuery, UnpublishedQuery
from djangoplicity.archives.options import ArchiveOptions


class MultiwavelengthImageOptions( ArchiveOptions ):
    urlname_prefix = 'multiwavelength'
    template_name = 'archives/multiwavelength/detail.html'

    prefetch_related = ( 'bands__image', )

    search_fields = ( 'id', 'title', 'subtitle', 'description', 'credit', )

    info = (
        ( _( "About the Page" ), { 'fields': ( 'id', release_date, ), } ),
    )

    admin = (
        ( _( "Admin" ), {
            'links': ( admin_edit_for_site( 'admin_site' ), ),
            'fields': ( published, 'release_date', 'embargo_date',
                        'last_modified', 'created', priority ),
        } ),
    )

    class Queries( object ):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name=_("Multiwavelength Universe"), feed_name="default" )
        embargo = EmbargoQuery( browsers=( 'normal', 'viewall' ), verbose_name=_("Multiwavelength Universe (embargoed)") )
        staging = StagingQuery( browsers=( 'normal', 'viewall' ), verbose_name=_("Multiwavelength Universe (staging)") )

    class Browsers( object ):
        normal = NormalBrowser( paginate_by=20 )
        viewall = ViewAllBrowser()

    class ResourceProtection( object ):
        unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
        staging = ( StagingQuery, security.STAGING_PERMS )
        embargo = ( EmbargoQuery, security.EMBARGO )
