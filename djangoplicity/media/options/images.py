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

import os

from django.db.models import Case, Value, When, IntegerField
from django.utils.translation import ugettext_lazy as _, ugettext_noop

from djangoplicity.archives.contrib import security
from djangoplicity.archives.contrib.browsers import NormalBrowser, \
    ViewAllBrowser, SerializationBrowser
from djangoplicity.archives.contrib.info import release_date, link_field, \
    admin_edit_for_site, admin_add_translation, published, featured, priority
from djangoplicity.archives.contrib.queries.defaults import AdvancedSearchQuery, \
    UnpublishedQuery, StagingQuery, EmbargoQuery
from djangoplicity.archives.contrib.search.fields import ImageSizeSearchField, \
    PrioritySearchField, AVMImageInstrumentSearchField, AVMImageFacilitySearchField, \
    SeparatorField, IdSearchField, RelatedIdSearchField, DateSinceSearchField, \
    DateUntilSearchField, TextSearchField, AVMSubjectNameSearchField, \
    AVMTypeSearchField, AVMSubjectCategorySearchField, BooleanSearchField, \
    ManyToManySearchField, FOVSearchField
from djangoplicity.archives.contrib.serialization.serializers import XMPEmitter, \
    JSONEmitter
from djangoplicity.archives.importer.import_actions import move_resources, \
    process_image_derivatives, compute_archive_checksums
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.views import SerializationDetailView
from djangoplicity.contentserver.import_actions import sync_content_server
from djangoplicity.cutter.imagemagick import identify_image
from djangoplicity.media import views
from djangoplicity.media.forms import ImageImportForm
from djangoplicity.media.info import related_releases, related_announcements, \
    related_science_announcements, pixel_size, distance, constellation, \
    zoomable, wallpapers, zoomable_link, object_language, object_id, \
    object_type, rel_shop_link, image_magnet_uri_link, fov, web_categories
from djangoplicity.media.models.images import Color, ImageProxy
from djangoplicity.media.queries import ImageAllPublicQuery, \
    WebCategoryPublicQuery, ZoomableQuery, WallpaperQuery, \
    PrintLayoutQuery, WWTQuery, ImageStagingQuery, ImageEmbargoQuery, \
    ObservationQuery
from djangoplicity.media.serializers import AVMImageSerializer, MiniImageSerializer
from djangoplicity.metadata.archives.info import subject_name, subject_category
from djangoplicity.metadata.consts import SPECTRAL_COLOR_ASSIGNMENT_CHOICES, \
    get_file_type


class ImageOptions( ArchiveOptions ):
    description_template = 'archives/image/object_description.html'

    urlname_prefix = "images"

    info = (
        ( ugettext_noop( u'About the Image' ), { 'fields': ( object_id, object_language, object_type, release_date, related_releases, related_announcements, related_science_announcements, pixel_size, fov ), 'links': ( link_field( _( 'NASA press release' ), 'press_release_link' ), link_field( _( 'NASA caption' ), 'long_caption_link' ) ) } ),
        ( ugettext_noop( u'About the Object' ), { 'fields': ( subject_name, subject_category, distance, constellation, web_categories ), } ),
        ( ugettext_noop( u'Mounted Image' ), { 'links': ( rel_shop_link, ), } ),
    )

    admin = (
        (
            ugettext_noop( u'Admin' ), {
                'links': (
                    admin_edit_for_site( 'admin_site', translation_proxy=ImageProxy ),
                    admin_add_translation( 'admin_site', translation_proxy=ImageProxy ),
                ),
                'fields': ( published, featured, 'release_date_owner', 'last_modified', 'created', priority, zoomable, wallpapers ),
        } ),
    )

    downloads = (
        ( ugettext_noop( u'Image Formats' ), {'resources': ( 'original', 'large', 'publicationtiff40k', 'publicationtiff25k', 'publicationtiff10k', 'publicationtiff', 'publicationjpg', 'screen', ), 'icons': { 'original': 'phot', 'large': 'phot', 'publicationtiff40k': 'phot', 'publicationtiff25k': 'phot', 'publicationtiff10k': 'phot', 'publicationtiff': 'phot', 'publicationjpg': 'phot', 'screen': 'phot', } } ),
        ( ugettext_noop( u'Print Layout' ), { 'condition': lambda obj: obj.print_layout, 'resources': ( 'pl_original', 'pl_screen', ), 'icons': {'pl_screen': 'phot', 'pl_original': 'phot', }, 'thumbnails': {'pl_thumbs': 'pl_screen'}, }, ),
        ( ugettext_noop( u'Zoomable' ), {'resources': ( zoomable_link, ), 'icons': { 'zoomable_link': 'zoom', } } ),
        ( ugettext_noop( u'BitTorrent Download' ), {'resources': ( image_magnet_uri_link, ), 'icons': { 'image_magnet_uri_link': 'magnet', } } ),
        ( ugettext_noop( u'Logos' ), {'resources': ( 'png', 'eps', 'illustrator', 'illustrator_text', ), 'icons': { 'png': 'phot', 'eps': 'phot', 'illustrator': 'phot', 'illustrator_text': 'phot'} } ),
        ( ugettext_noop( u'Wallpapers' ), { 'condition': lambda obj: obj.wallpapers, 'resources': ( 'wallpaper1', 'wallpaper2', 'wallpaper3', 'wallpaper4', 'wallpaper5', ), 'icons': { 'wallpaper1': 'slides', 'wallpaper2': 'slides', 'wallpaper3': 'slides', 'wallpaper4': 'slides', 'wallpaper5': 'slides', } } ),
        ( ugettext_noop( u'PDF' ), {'resources': ( 'pdf', ), 'icons': { 'pdf': 'doc', } } ),
    )

    detail_views = (
        { 'url_pattern': 'zoomable/', 'view': views.ZoomableDetailView(), 'urlname_suffix': 'zoomable' },
        { 'url_pattern': 'api/(?P<serializer>xmp|xml|json)/', 'view': SerializationDetailView( serializer=AVMImageSerializer, emitters=[XMPEmitter, JSONEmitter] ), 'urlname_suffix': 'serialization', },
    )

    search_fields = (
        'id', 'title', 'headline', 'description', 'subject_name__name', 'subject_name__alias', 'credit', 'type',
    )

    prefetch_related = ('pictureoftheweek_set', )
    archive_list_only_fields = (
        'id', 'title', 'width', 'height', 'credit', 'lang', 'source',
        'content_server', 'content_server_ready'
    )

    class Queries( object ):
        default = ImageAllPublicQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Images") )
        category = WebCategoryPublicQuery( relation_field='web_category', browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Image Archive: %(title)s"), category_type='Images' )
        top100 = ImageAllPublicQuery( browsers=( 'top100', 'json', 'minijson', 'fbtop100', 'fs' ), verbose_name=ugettext_noop("Top 100 Images"), searchable=False, feed_name='top100' )
        observation = ObservationQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Observation Full Spatial Quality Images"), searchable=False, feed_name='observation' )
        bestof = ImageAllPublicQuery( browsers=( 'viewall', 'json' ), verbose_name=ugettext_noop("Hall Of Fame"), searchable=False )
        zoomable = ZoomableQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Zoomable Images") )
        wallpapers = WallpaperQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Wallpapers") )
        wwt = WWTQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop( "WorldWide Telescope" ) )
        print_layouts = PrintLayoutQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Print Layouts") )
        search = AdvancedSearchQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Advanced Image Search"), searchable=False )
        staging = ImageStagingQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Images (staging)") )
        embargo = ImageEmbargoQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Images (embargoed)") )

    class Browsers(object):
        normal = NormalBrowser( paginate_by=50 )
        viewall = ViewAllBrowser( paginate_by=250 )
        top100 = ViewAllBrowser( index_template='index_top100.html', paginate_by=100 )
        fbtop100 = ViewAllBrowser( index_template='index_top100.html', paginate_by=5 )
        fs = ViewAllBrowser( index_template='top100_fs.html', paginate_by=10 )
        json = SerializationBrowser( serializer=AVMImageSerializer, emitter=JSONEmitter, paginate_by=100, display=False, verbose_name=ugettext_noop("JSON") )
        minijson = SerializationBrowser( serializer=MiniImageSerializer, emitter=JSONEmitter, paginate_by=10, display=False, verbose_name=ugettext_noop( "JSON" ) )

    class ResourceProtection (object):
        unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
        staging = ( StagingQuery, security.STAGING_PERMS )
        embargo = ( EmbargoQuery, security.EMBARGO )

    class AdvancedSearch (object):
        minimum_size = ImageSizeSearchField( label=_( "Minimum size" ) )
        ranking = PrioritySearchField( label=_( "Ranking" ) )
        instrument = AVMImageInstrumentSearchField( label=_( "Instrument used" ) )
        facility = AVMImageFacilitySearchField( label=_( "Facility used" ) )
        additional_search_items = SeparatorField( label=_("Additional search terms") )
        id = IdSearchField( label=_('Image ID') )
        release_id = RelatedIdSearchField( label=_('Release ID'), model_field='release__id' )
        published_since = DateSinceSearchField( label=_( "Published since" ), model_field='release_date' )
        published_until = DateUntilSearchField( label=_( "Published until" ), model_field='release_date' )
        title = TextSearchField( label=_( "Title" ), model_field='title' )
        subject_name = AVMSubjectNameSearchField( label=_( "Subject name" ) )
        description = TextSearchField( label=_( "Description" ), model_field='description' )
        credit = TextSearchField( label=_( "Credit" ), model_field='credit' )
        type = AVMTypeSearchField( label=_( "Type" ), )
        category = AVMSubjectCategorySearchField( label=_( "Category" ), )
        zoomable = BooleanSearchField( model_field='zoomify', label=_("Zoomable available") )
        wallpapers = BooleanSearchField( model_field='wallpapers', label=_("Wallpaper available") )
        colours = ManyToManySearchField( label=_( "Colours" ), model_field='colors__id', choices_func=lambda: [( c.id, _( c.name ) ) for c in Color.objects.all() ] )
        fov = FOVSearchField( label=_( "Field of View" ) )

        class Meta:
            verbose_name = ugettext_noop("Advanced Image Search")

    class Import( object ):
        form = ImageImportForm
        uploadable = True
        metadata = 'original'
        scan_directories = [
            ('original', ('.tif', '.psb', '.jpg')),
            ('banner1920', ('.jpg', )),
            ('newsfeature', ('.jpg', )),
        ]
        actions = [
            move_resources,
            process_image_derivatives(),
            compute_archive_checksums(),
            sync_content_server(),
        ]

    @staticmethod
    def extra_context( obj, lang=None ):
        # The colors should be ordered as defined in SPECTRAL_COLOR_ASSIGNMENT_CHOICES
        args = []
        for i, (color, _name) in enumerate(SPECTRAL_COLOR_ASSIGNMENT_CHOICES):
            args.append(When(spectral_color_assignment=color, then=Value(i)))

        imageexposures = obj.imageexposure_set.all().select_related(
            'facility', 'instrument'
        ).annotate(
            color_order=Case(*args, output_field=IntegerField())
        ).order_by('color_order')

        has_wavelength = False

        for e in imageexposures:
            if e.spectral_central_wavelength:
                has_wavelength = True
                break

        # we are being conservative about the exposure time: only display it if it is simple
        exposure_time = None
        if len(imageexposures) == 1:
            exposure_time = imageexposures[0].temporal_integration_time

        return {
            'imageexposures': imageexposures,
            'has_wavelength': has_wavelength,
            'exposure_time': exposure_time,
            'translations': obj.get_translations(),
        }

    @staticmethod
    def queryset( request, model ):
        """
        Query set for detail view. Make sure we select related releases right away,
        as we need the later on.
        """
        return model._default_manager.all()

    @staticmethod
    def feeds():
        from djangoplicity.media.feeds import ImageFeed, Top100Feed, VAMPFeed
        feed_dict = {
            '': ImageFeed,
            'category': ImageFeed,
            'top100': Top100Feed,
            'vamp': VAMPFeed,
        }
        return feed_dict

    @staticmethod
    def handle_import( obj, id=None, data=None, form_values=None ):
        """
        Copy values from import form to object
        """
        if data is None:
            data = {}
        if form_values is None:
            form_values = {}

        from djangoplicity.archives.importer.utils import handle_import
        obj = handle_import( obj, id=id, data=data, form_values=form_values, save=False )

        # Extra fields being handled
        if not obj.description:
            obj.description = ''
        if not obj.credit:
            obj.credit = ''

        obj.wallpapers = form_values["wallpapers"]
        obj.zoomify = form_values["zoomify"]
        if 'credit' in form_values:
            obj.credit = form_values['credit']

        # File Metadata extraction
        try:
            file_path = data["files"][data['formats'].index( 'original' )]

            obj.file_type = get_file_type( file_path )
            obj.file_size = long(os.path.getsize( file_path )) / 1024

            try:
                obj.width, obj.height = identify_image(file_path)
            except IOError:
                pass
        except ValueError:
            pass

        obj.save()
        return obj
