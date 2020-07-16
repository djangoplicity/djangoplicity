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
from django.utils.translation import ugettext_noop
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.contrib import security
from djangoplicity.archives.contrib.browsers import NormalBrowser, \
    ViewAllBrowser, SerializationBrowser
from djangoplicity.archives.contrib.info import release_date, \
    admin_edit_for_site, admin_add_translation, published, priority
from djangoplicity.archives.contrib.queries.defaults import AllPublicQuery, \
    EmbargoQuery, StagingQuery, YearQuery, UnpublishedQuery
from djangoplicity.archives.contrib.serialization.serializers import JSONEmitter, \
    ICalEmitter
from djangoplicity.archives.importer.import_actions import move_resources, \
    process_image_derivatives
from djangoplicity.archives.utils import related_archive_item_fk
from djangoplicity.archives.views import SerializationDetailView
from djangoplicity.media import views
from djangoplicity.media.forms import ImageComparisonImportForm
from djangoplicity.media.info import object_id, related_releases
from djangoplicity.media.models import ImageComparisonProxy, \
    ImageComparison
from djangoplicity.media.serializers import ImageComparisonSerializer, \
    ICalImageComparisonSerializer


class ImageComparisonOptions( ArchiveOptions ):
    """
    Archive options definitions for image comparison archive.
    """
    description_template = 'archives/imagecomparison/object_description.html'

    urlname_prefix = "imagecomparisons"

    detail_views = (
        { 'url_pattern': 'api/(?P<serializer>json)/', 'view': SerializationDetailView( serializer=ImageComparisonSerializer, emitters=[JSONEmitter] ), 'urlname_suffix': 'serialization', },
        { 'url_pattern': 'fullscreen/', 'view': views.ImageComparisonFullscreenDetailView(), 'urlname_suffix': 'fullscreen', },
    )

    info = (
        ( ugettext_noop( u'About the Image Comparison' ), { 'fields': ( object_id, release_date, related_releases ), } ),
    )

    admin = (
        ( ugettext_noop( u'Admin' ), { 'links': (
            admin_edit_for_site( 'admin_site', translation_proxy=ImageComparisonProxy ),
            admin_add_translation( 'admin_site', translation_proxy=ImageComparisonProxy ),
            ), 'fields': ( published, 'embargo_date', 'release_date_owner', 'last_modified', 'created', priority ), } ),
    )

    downloads = (
        ( ugettext_noop( u'Images' ), {'resources': ( 'original', 'large', 'screen', ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot' } } ),
    )

    search_fields = (
        'id', 'title', 'description', 'credit',
    )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Image Comparisons"), feed_name="default" )
        embargo = EmbargoQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Image Comparisons (embargoed)") )
        staging = StagingQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Image Comparisons (staging)") )
        year = YearQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Image Comparisons %d"), feed_name="default" )

    class Browsers(object):
        normal = NormalBrowser( paginate_by=52 )
        viewall = ViewAllBrowser( paginate_by=100 )
        json = SerializationBrowser( serializer=ImageComparisonSerializer, emitter=JSONEmitter, paginate_by=20, display=False, verbose_name=ugettext_noop( "JSON" ) )
        ical = SerializationBrowser( serializer=ICalImageComparisonSerializer, emitter=ICalEmitter, paginate_by=100, display=False, verbose_name=ugettext_noop( "iCal" ) )

    class ResourceProtection( object ):
        unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
        staging = ( StagingQuery, security.STAGING_PERMS )
        embargo = ( EmbargoQuery, security.EMBARGO )

    class Import( object ):
        form = ImageComparisonImportForm
        uploadable = True
        metadata = 'original'
        scan_directories = [
            ( 'original', ( '.jpg', '.jpeg', '.tif', '.tiff', '.png', ) ),
        ]
        actions = [
            move_resources,
            process_image_derivatives(),
        ]

    @staticmethod
    def extra_context( obj, lang=None ):
        return {
            'image_before': related_archive_item_fk( ImageComparison.image_before, obj ),
            'image_after': related_archive_item_fk( ImageComparison.image_after, obj ),
            'translations': obj.get_translations(),
        }

    @staticmethod
    def handle_import( obj, id=None, data={}, form_values={} ):
        """
        Copy values from import form to object
        """
        from djangoplicity.archives.importer.utils import handle_import
        obj = handle_import( obj, id=id, data=data, form_values=form_values, save=False )

        obj.image_before = None
        obj.image_after = None
        obj.save()

        obj.image_before = form_values['image_before']
        obj.image_after = form_values['image_after']
        obj.save()

        return obj
