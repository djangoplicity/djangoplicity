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

from django.db.models.fields import FieldDoesNotExist
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from djangoplicity.archives.contrib.admin import ArchiveAdmin, RenameAdmin, \
    view_link, product_link
from djangoplicity.archives.contrib.satchmo.models import ShopModel
from djangoplicity.contrib.admin import DjangoplicityModelAdmin
from djangoplicity.products.base.models import StandardArchiveInfo, PhysicalInfo, \
    PrintInfo, ScreenInfo
from djangoplicity.products.models import *
from djangoplicity.products.options import *
from djangoplicity.products.base.models import ArchiveCategory


class ExhibitionGroupAdmin( DjangoplicityModelAdmin ):
    list_display = ( 'id', 'name', 'priority', )
    list_editable = ( 'name', 'priority' )
    ordering = ('-priority', )


class OnlineArtAuthorAdmin( DjangoplicityModelAdmin, RenameAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'name', 'city', 'country', 'email', 'published', 'priority', 'last_modified', view_link('artists') )
    list_filter = ( 'city', 'country',)
    list_editable = ( 'name', 'priority' )
    search_fields = ( 'name', 'city', 'country', 'email',)
    date_hierarchy = 'last_modified'
    fieldsets = (
                    ( None, {'fields': ( 'id', ) } ),
                    ( 'Publishing', {'fields': ( 'published', 'priority', ), } ),
                    ( 'Archive', {'fields': ( 'name', 'description', 'credit', 'city', 'country', 'link'), } ),
                )
    ordering = ('name', )
    richtext_fields = ('description',)
    actions = ['action_toggle_published', ]
    links = ()


class ConferenceAdmin( DjangoplicityModelAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'title', 'start_date', 'end_date', 'max_participants', 'job', 'jsp', 'account_no' )
    list_editable = ( 'title', )
    search_fields = ( 'title', 'description', 'job', 'account_no', 'jsp' )
    date_hierarchy = 'start_date'
    fieldsets = (
                    ( None, {'fields': ( 'id', ) } ),
                    ( 'Description', {'fields': ( 'title', 'description', ), } ),
                    ( 'Information', {'fields': ( 'start_date', 'end_date', 'max_participants',), } ),
                    ( 'ERP', {'fields': ( 'job', 'jsp', 'account_no',), } ),
                )
    ordering = ('id', )
    richtext_fields = ('description',)


def admin_factory( model, options, exclude=['release_date', 'embargo_date', 'created', 'last_modified'], name='Extra information', extra={} ):
    """
    Builds options class for administration interface.
    """
    def check_fields( fs ):
        tmp = []
        for f in fs:
            try:
                model._meta.get_field( f )
                tmp.append( f )
            except FieldDoesNotExist:
                pass
        return tmp

    def exclude_fields( fs ):
        return [x for x in fs if x not in exclude]

    product_list_display = check_fields( [ 'id', 'list_link_thumbnail', ] )
    product_list_filter = exclude_fields( exclude_fields( ['published', 'priority'] ) )
    product_list_editable = check_fields( [ 'priority', ] )
    product_search_fields = [ 'id', ]
    product_richtext_fields = []
    product_actions = ['action_toggle_published', ]
    product_fieldsets = [ ( None, {'fields': ( 'id', ) } ), ]

    _pub_field_set = tuple( check_fields( exclude_fields( ['published', 'priority', 'release_date', 'embargo_date'] ) ) )
    if _pub_field_set:
        product_fieldsets += [ ( 'Publishing', {'fields': _pub_field_set, } ), ]

    product_raw_id_fields = []
    product_readonly_fields = []
    product_inlines = []

    # Default extra values
    default_extra = {
        'list_display': [],
        'list_filter': [],
        'list_editable': [],
        'search_fields': [],
        'richtext_fields': [],
        'actions': [],
        'fieldsets': [],
        'raw_id_fields': [],
        'readonly_fields': [],
        'inlines': [],
    }

    default_extra.update( extra )

    #
    # Standard archive info
    #
    if issubclass( model, StandardArchiveInfo ):
        product_list_display += exclude_fields( ['title', ] )
        product_list_editable += exclude_fields( [ 'title', ] )
        product_search_fields = exclude_fields( ['title', 'description', 'credit'] )
        product_richtext_fields += exclude_fields( ['description', 'credit', ] )
        product_fieldsets += [ ( 'Archive', {'fields': exclude_fields( ['title', 'description', 'credit', 'archive_category'] ), } ), ]
    else:
        product_list_display += check_fields( exclude_fields( ['title', ] ) )
        product_list_editable += check_fields( exclude_fields( [ 'title', ] ) )
        product_search_fields = check_fields( exclude_fields( ['title', 'description', 'credit'] ) )
        product_richtext_fields += check_fields( exclude_fields( ['description', 'credit', ] ) )
        product_fieldsets += [ ( 'Archive', {'fields': check_fields( exclude_fields(  ['title', 'description', 'credit', ] ) ), } ), ]

    # archive info
    product_list_display += exclude_fields( [ 'published', 'priority', ] )
    product_list_display += default_extra['list_display']
    product_list_filter += default_extra['list_filter']
    product_list_editable += default_extra['list_editable']
    product_search_fields += default_extra['search_fields']
    product_richtext_fields += default_extra['richtext_fields']
    product_actions += default_extra['actions']
    product_fieldsets += default_extra['fieldsets']
    product_raw_id_fields += default_extra['raw_id_fields']
    product_readonly_fields += default_extra['readonly_fields']
    product_inlines += default_extra['inlines']

    try:
        if options.Import.actions:
            product_actions += ['action_reimport']
    except AttributeError:
        pass

    #
    # Physical information
    #
    if issubclass( model, PhysicalInfo ):
        product_fieldsets += [ ( 'Physical information', {'fields': ( 'width', 'height', 'depth', 'weight', ), } ), ]

    #
    # Print info
    #
    if issubclass( model, PrintInfo ):
        product_fieldsets += [ ( 'Print information', {'fields': ( 'pages', 'cover', 'language' ), } ), ]
        product_list_display += [ 'cover', 'language', ]
        product_list_editable += [ 'cover', 'language', ]

    #
    # ScreenInfio
    #
    if issubclass( model, ScreenInfo ):
        product_fieldsets += [ ( 'Screen information', {'fields': ( 'resolution', 'x_size', 'y_size' ), } ), ]

    #archive info
    product_list_display += ['last_modified', view_link( options.urlname_prefix )]

    #
    # Shop information
    #
    if issubclass( model, ShopModel ):
        try:
            model._meta.get_field('weight')  # Test if field exists.
            product_list_display += ['sale', 'free', 'price', 'weight', product_link( 'adminshop_site' ) ]
            product_list_editable += ['price', 'weight', ]
        except FieldDoesNotExist:
            product_list_display += ['sale', 'free', 'price', product_link( 'adminshop_site' ) ]
            product_list_editable += ['price', ]
        product_list_filter += ['sale', 'free', 'shippable', ]
        product_actions += ['action_toggle_sale', 'action_toggle_free']
        product_fieldsets += [( 'Shop', {'fields': ( 'sale', 'free', 'price', 'shippable', ), } ), ]
        product_fieldsets += [( 'ERP', {'fields': ( 'job', 'jsp', 'account_no', ), } ), ]
        exclude += ['product', ]

    exclude += ['reserve_count', 'low_stock_level', 'delivery_date', ]  # should be removed if above three lines are uncommmented

    #
    # Add missing fields
    #

    # Create list of all shown fields
    fields = []

    for ( dummy, f ) in product_fieldsets:
        fields += list( f['fields'] )

    fields = list( set( fields ) )

    # Find all fields not being shown
    local_fields = [x.name for x in model._meta.local_fields]
    missing_fields = [x for x in local_fields if x not in fields + exclude]

    if missing_fields:
        product_fieldsets += [( name, { 'fields': tuple( missing_fields ) } ), ]

    #
    # Build product admin
    #
    class ProductAdmin( DjangoplicityModelAdmin, RenameAdmin, ArchiveAdmin ):
        thumbnail_resource = 'thumb'
        list_display = tuple( product_list_display )
        list_filter = tuple( product_list_filter )
        list_editable = tuple( product_list_editable )
        search_fields = tuple( product_search_fields )
        richtext_fields = tuple( product_richtext_fields )
        date_hierarchy = 'last_modified'
        ordering = ('-last_modified', )
        actions = product_actions
        fieldsets = tuple( product_fieldsets )
        raw_id_fields = tuple( product_raw_id_fields )
        readonly_fields = tuple( product_readonly_fields )
        inlines = list( product_inlines )

        def formfield_for_dbfield(self, db_field, **kwargs):
            field = super( ProductAdmin, self ).formfield_for_dbfield( db_field, **kwargs )
            if db_field.name == 'weight':
                field.widget.attrs['class'] = "vIntegerField"
            if db_field.name == 'price':
                field.widget.attrs['class'] = "vIntegerField"
            return field

    return ProductAdmin


def register_if_installed( admin_site, model, options, **kwargs ):
    admin_site.register( model, admin_factory( model, options, **kwargs ) )


def register_with_admin( admin_site ):
    register_if_installed( admin_site, AnnualReport, AnnualReportOptions )
    register_if_installed( admin_site, Book, BookOptions, extra={ 'search_fields': ['isbn'], 'fieldsets': [( 'Extra', {'fields': ( 'isbn', 'doi'), } ), ] } )
    register_if_installed( admin_site, Brochure, BrochureOptions, exclude=['embargo_date', 'created', 'last_modified'] )
    register_if_installed( admin_site, Flyer, FlyerOptions, exclude=['embargo_date', 'created', 'last_modified'] )
    register_if_installed( admin_site, Stationery, StationeryOptions, exclude=['embargo_date', 'created', 'last_modified'] )
    register_if_installed( admin_site, Map, MapOptions, exclude=['embargo_date', 'created', 'last_modified'] )
    register_if_installed( admin_site, Application, ApplicationOptions, extra={ 'fieldsets': [( 'Shop Links', {'fields': ( 'itunes_link', 'marketplace_link', ), } ), ] } )

    register_if_installed( admin_site, Media, MediaOptions )
    register_if_installed( admin_site, Calendar, CalendarOptions, name='Calendar' )
    register_if_installed( admin_site, EducationalMaterial, EducationalMaterialOptions )
    register_if_installed( admin_site, Exhibition, ExhibitionOptions, extra={ 'list_display': ['group', 'group_order'], 'list_editable': ['group', 'group_order'], } )
    register_if_installed( admin_site, FITSImage, FITSImageOptions, name='Author' )
    register_if_installed( admin_site, Handout, HandoutOptions )
    register_if_installed( admin_site, KidsDrawing, KidsDrawingOptions, name='Author' )
    register_if_installed( admin_site, Logo, LogoOptions )
    register_if_installed( admin_site, Music, MusicOptions )
    register_if_installed( admin_site, Merchandise, MerchandiseOptions )
    register_if_installed( admin_site, Apparel, ApparelOptions )
    register_if_installed( admin_site, MiniSite, MiniSiteOptions )
    register_if_installed( admin_site, STECFNewsletter, STECFNewsletterOptions )
    register_if_installed( admin_site, CapJournal, CapJournalOptions )
    register_if_installed( admin_site, Messenger, MessengerOptions )
    register_if_installed( admin_site, ScienceInSchool, ScienceInSchoolOptions )
    register_if_installed( admin_site, Bulletin, BulletinOptions )
    register_if_installed( admin_site, OnlineArt, OnlineArtOptions, name='Artist' )
    register_if_installed( admin_site, PaperModel, PaperModelOptions )
    register_if_installed( admin_site, PlanetariumShow, PlanetariumShowOptions )
    register_if_installed( admin_site, PostCard, PostCardOptions )
    register_if_installed( admin_site, PrintedPoster, PrintedPosterOptions )
    register_if_installed( admin_site, ConferencePoster, ConferencePosterOptions )
    register_if_installed( admin_site, ElectronicPoster, ElectronicPosterOptions )
    register_if_installed( admin_site, MountedImage, MountedImageOptions, extra={ 'raw_id_fields': ['image'], 'fieldsets': [( 'Related image', {'fields': ( 'image', ), 'description': _("In case title, description or credit is not provided, the image's title, description or credit will be used.") } ), ] } )
    register_if_installed( admin_site, Presentation, PresentationOptions )
    register_if_installed( admin_site, PressKit, PressKitOptions )
    register_if_installed( admin_site, ElectronicCard, ElectronicCardOptions )
    register_if_installed( admin_site, Sticker, StickerOptions )
    register_if_installed( admin_site, TechnicalDocument, TechnicalDocumentOptions )
    register_if_installed( admin_site, UserVideo, UserVideoOptions )
    register_if_installed( admin_site, VirtualTour, VirtualTourOptions )
    register_if_installed( admin_site, ConferenceItem, ConferenceItemOptions, extra={ 'fieldsets': [( 'Conference', {'fields': ( 'conference', ), } ), ] } )
    register_if_installed( admin_site, Visit, VisitOptions, exclude=['credit', 'list_link_thumbnail', 'embargo_date', 'created', 'last_modified', 'priority'], extra={ 'richtext_fields': ['description', ], 'raw_id_fields': ['image', ] } )
    register_if_installed( admin_site, IMAXFilm, IMAXFilmOptions )
    register_if_installed( admin_site, Model3d, Model3dOptions )
    register_if_installed( admin_site, EPublication, EPublicationOptions )
    register_if_installed( admin_site, Donation, DonationOptions )
    register_if_installed( admin_site, SupernovaActivity, SupernovaActivityOptions )

    admin_site.register( OnlineArtAuthor, OnlineArtAuthorAdmin )  # Special
    admin_site.register( Conference, ConferenceAdmin )  # Special
    admin_site.register( ExhibitionGroup, ExhibitionGroupAdmin )  # Special

    class ArchiveCategoryAdmin(DjangoplicityModelAdmin):
       list_display = ('fullname',)

       change_list_template = 'admin/products/change_list_archivecategory.html'

    admin_site.register(ArchiveCategory, ArchiveCategoryAdmin)

# Register with default admin site
register_with_admin( admin.site )
