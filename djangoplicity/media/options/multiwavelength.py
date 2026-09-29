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
    admin_add_translation, priority, published, release_date
from djangoplicity.archives.contrib.queries import AllPublicQuery, \
    EmbargoQuery, StagingQuery, UnpublishedQuery
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.media import views
from djangoplicity.media.info import object_id
from djangoplicity.media.models import MultiwavelengthImageProxy


class MultiwavelengthImageOptions( ArchiveOptions ):
    urlname_prefix = 'multiwavelength'
    template_name = 'archives/multiwavelength/detail.html'

    # Prefetching doesn't follow translations to their source (see
    # ArchiveOptions.prefetch_related), so the source bands are prefetched
    # through 'source' for translated objects.
    prefetch_related = ( 'bands__image', 'source__bands__image', 'band_translations', )

    detail_views = (
        { 'url_pattern': 'fullscreen-comparison/', 'view': views.ZoomableCompareDetailView(), 'urlname_suffix': 'fullscreen_comparison', },
    )

    search_fields = ( 'id', 'title', 'subtitle', 'description', 'credit', )

    info = (
        ( _( "About the Page" ), { 'fields': ( object_id, release_date, ), } ),
    )

    admin = (
        ( _( "Admin" ), {
            'links': (
                admin_edit_for_site( 'admin_site', translation_proxy=MultiwavelengthImageProxy ),
                admin_add_translation( 'admin_site', translation_proxy=MultiwavelengthImageProxy ),
            ),
            'fields': ( published, 'release_date', 'embargo_date',
                        'last_modified', 'created', priority ),
        } ),
    )

    class Queries( object ):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name=_("Multiwavelength Viewers"), feed_name="default" )
        embargo = EmbargoQuery( browsers=( 'normal', 'viewall' ), verbose_name=_("Multiwavelength Viewers (embargoed)") )
        staging = StagingQuery( browsers=( 'normal', 'viewall' ), verbose_name=_("Multiwavelength Viewers (staging)") )

    class Browsers( object ):
        normal = NormalBrowser( paginate_by=52 )
        viewall = ViewAllBrowser()

    class ResourceProtection( object ):
        unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
        staging = ( StagingQuery, security.STAGING_PERMS )
        embargo = ( EmbargoQuery, security.EMBARGO )
