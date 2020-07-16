# -*- coding: utf-8 -*-
#
# djangoplicity-products
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

"""
Base archive options definitions across all product archives.
"""

from builtins import object
from django.utils.translation import ugettext_lazy as _
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.contrib import security
from djangoplicity.archives.contrib.browsers import NormalBrowser, \
    ViewAllBrowser
from djangoplicity.archives.contrib.info import priority, published, \
    admin_edit_for_site
from djangoplicity.archives.contrib.queries import UnpublishedQuery, \
    EmbargoQuery, StagingQuery
from djangoplicity.products.base.consts import IMAGE_DOWNLOADS, FILE_DOWNLOADS
from djangoplicity.archives.importer.import_actions import move_resources, \
    process_image_derivatives


class StandardOptions( ArchiveOptions ):
    """
    Defines common options across all product archives
    """
    admin = (
        ( _( u'Admin' ), {
            'links': ( admin_edit_for_site( 'admin_site' ), ),
            'fields': ( published, 'release_date', 'last_modified', 'created', priority ),
        } ),
    )

    search_fields = (
        'id', 'title', 'description', 'credit',
    )

    downloads = (
        IMAGE_DOWNLOADS,
        FILE_DOWNLOADS,
    )

    class Browsers( object ):
        normal = NormalBrowser( paginate_by=20 )
        viewall = ViewAllBrowser()

    class ResourceProtection( object ):
        unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
        staging = ( StagingQuery, security.STAGING_PERMS )
        embargo = ( EmbargoQuery, security.EMBARGO )

    class Import( object ):
        uploadable = True
        metadata = 'original'
        scan_directories = [
            ( 'original', ( '.jpg', '.jpeg', '.tif', '.tiff', '.png', ) ),
            ( 'original_cmyk', ( '.jpg', '.jpeg', '.tif', '.tiff', '.png', ) ),
            ( 'original_trans', ( '.jpg', '.jpeg', '.tif', '.tiff', '.png', ) ),
            ( 'original_trans_cmyk', ( '.jpg', '.jpeg', '.tif', '.tiff', '.png', ) ),
            ( 'epub', ( '.epub', ) ),
            ( 'pdf', ( '.pdf', ) ),
            ( 'pdfsm', ( '.pdf', ) ),
            ( 'ps', ( '.ps', '.gz' ) ),
            ( 'ppt', ( '.ppt', ) ),
            ( 'pps', ( '.pps', ) ),
            ( 'eps', ( '.eps', ) ),
            ( 'illustrator', ( '.ai', ) ),
            ( 'flash', ( '.swf', ) ),
            ( 'doc', ( '.doc', ) ),
            ( 'zip', ( '.zip', ) ),
            ( 'tour', ( '', ) ),
            ( 'wav', ( '.wav', ) ),
        ]
        actions = [
            move_resources,
            process_image_derivatives(),
        ]

    @staticmethod
    def queryset( request, model ):
        """
        Query set for detail view. Make sure we select related objects right away,
        as we need the later on.
        """
        return model._default_manager.all()
