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
Options file for product archives.
"""

from builtins import object
from django.conf.urls import *
from django.utils.translation import ugettext_lazy as _
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.contrib.browsers import *
from djangoplicity.archives.contrib.info import *
from djangoplicity.archives.contrib.queries import AllPublicQuery
from djangoplicity.archives.importer.import_actions import move_resources, \
    process_audio_extras, process_audio_derivatives, process_image_derivatives
from djangoplicity.media.info import duration
from djangoplicity.metadata.archives.info import *
from djangoplicity.products.base import *
from djangoplicity.products.info import *
from djangoplicity.products.models import *
from djangoplicity.products.queries import *


def product_options( prefix, about_name, view_name, with_pages, nopaper=False, extra_fields=(), description_template=None ):
    """
    Factory function to generate an archive options file.
    """
    if with_pages:
        fields = ( 'id', release_date, dimensions, 'pages', 'cover', language ) + extra_fields
    elif nopaper:
        fields = ( 'id', release_date ) + extra_fields
    else:
        fields = ( 'id', release_date, dimensions ) + extra_fields

    class Options( StandardOptions ):
        urlname_prefix = prefix

        info = (
            ( _( u'About the %s' % about_name ), { 'links': ( shop_link, ), 'fields': fields, } ),
        )

        class Queries(object):
            default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name=view_name )

    if description_template:
        Options.description_template = description_template

    return Options


#######################
# Options definitions #
#######################
AnnualReportOptions = product_options( "annualreports", "Annual Report", "Annual Reports", False )
BookOptions = product_options( "books", "Book", "Books", True, extra_fields=( 'isbn', 'doi' ) )
BrochureOptions = product_options( "brochures", "Brochure", "Brochures", True )
FlyerOptions = product_options( "flyers", "Flyer", "Flyers", True )
StationeryOptions = product_options( "stationery", "Stationery", "Stationery", True )
MapOptions = product_options( "maps", "Map", "Maps", True )
MediaOptions = product_options( "media", "Medium", "Media", False )
ConferenceItemOptions = product_options( "conferenceitems", "Conference", "Conferences", False )
EducationalMaterialOptions = product_options( "education", "Material", "Educational Material", True )
MiniSiteOptions = product_options( "minisites", "Mini-Site", "Mini-Sites", False, nopaper=True )
MountedImageOptions = product_options( "mountedimages", "Mounted Image", "Mounted Images", False, extra_fields=(archive_image,), description_template='archives/mountedimage/object_description.html'  )
MountedImageOptions.search_fields = ('id', 'title', 'description', 'credit', 'image__title', 'image__description')
MerchandiseOptions = product_options( "merchandise", "Merchandise", "Merchandise", False )
ApparelOptions = product_options( "apparel", "Apparel", "Apparel", False )
PaperModelOptions = product_options( "papermodels", "Paper Model", "Paper Models", False )
PlanetariumShowOptions = product_options( "planetariumshows", "Planetarium Show", "Planetarium Shows", False, nopaper=True )
PostCardOptions = product_options( "postcards", "Postcard", "Postcards", False )
StickerOptions = product_options( "stickers", "Sticker", "Stickers", False )
TechnicalDocumentOptions = product_options( "techdocs", "Document", "Technical Documents", True )
VirtualTourOptionsSC = product_options( "virtualtours", "Virtual Tour", "Virtual Tours", False )
PrintedPosterOptions = product_options( "print_posters", "PrintedPoster", "PrintedPosters", False, extra_fields=(pixel_size, resolution) )
ConferencePosterOptions = product_options( "conf_posters", "ConferencePoster", "ConferencePosters", False, extra_fields=(pixel_size, resolution) )
ElectronicPosterOptions = product_options( "elec_posters", "ElectronicPoster", "ElectronicPosters", False, extra_fields=(pixel_size, resolution) )
CapJournalOptions = product_options( "capjournals", "CAPjournal", "CAPjournals", True )
STECFNewsletterOptions = product_options( "stecfnewsletters", "STECF Newsletter", "STECF Newsletters", True )
MessengerOptions = product_options( "messengers", "Messenger", "Messengers", True )
ScienceInSchoolOptions = product_options( "schools", "Science In School", "Science In School", True )
BulletinOptions = product_options( "bulletins", "Bulletin", "Bulletins", True )
IMAXFilmOptions = product_options( "imaxfilms", "IMAX Film", "IMAX Films", False, nopaper=True )
EPublicationOptions = product_options( "epublications", "ePublication", "ePublications", False, nopaper=True )
DonationOptions = product_options( "donations", "Donation", "Donations", False )
SupernovaActivityOptions = product_options( "supernovaactivities", "Supernova Activity", "Supernova Activities", False )


class VirtualTourOptions( VirtualTourOptionsSC ):
    description_template = 'archives/virtualtour/object_description.html'


class ApplicationOptions (StandardOptions):
    urlname_prefix = 'applications'
    description_template = 'archives/application/object_description.html'

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'screen'  ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'  } } ),

        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Applications" )


class HandoutOptions( StandardOptions ):
    urlname_prefix = 'handouts'

    info = (
        ( _(u'About the Handout'), { 'links': ( shop_link, ), 'fields': ( 'id', release_date, dimensions, 'pages', 'cover', language ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'screen'  ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'  } } ),
        ( _(u'File Formats'), {'resources': ( 'pdf', ), 'icons': { 'pdf': 'doc', } } ),

        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Handouts" )


class KidsDrawingOptions ( StandardOptions ):

    urlname_prefix = 'drawings'

    info = (
        ( _(u'Author'), { 'fields': ( 'name', 'age', 'city', 'country' ), } ),
        ( _(u'About the Drawing'), { 'fields': ( 'id', ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'screen'  ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'  } } ),
        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Drawings" )


class PressKitOptions (StandardOptions):
    urlname_prefix = 'presskits'

    info = (
        ( _(u'About the Press Kit'), { 'fields': ( 'id', paper_size, 'pages'  ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'screen'  ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'  } } ),
        ( _(u'File Formats'), {'resources': ( 'pdf', ), 'icons': { 'pdf': 'doc', } } ),
        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Press Kits" )


class MusicOptions (StandardOptions):
    urlname_prefix = 'music'
    description_template = 'archives/music/object_description.html'

    info = (
        (_(u'About the Music'), {'fields': ('id', release_date, duration)}),
    )

    downloads = (
        (
            _(u'Audio'), {
                'resources': ('wav', 'aac', 'mp3'),
                'icons': {
                    'wav': 'audio',
                    'aac': 'audio',
                    'mp3': 'audio',
                }
            }
        ),
    )

    class Queries(object):
        default = AllPublicQuery(browsers=('normal', 'viewall'), verbose_name='Music')

    class Import(StandardOptions.Import):
        scan_directories = [
            ('wav', ('.wav', )),
            ('mp3', ('.mp3', )),
        ]
        actions = [
            move_resources,
            process_audio_derivatives(),
            process_audio_extras(),
        ]


class LogoOptions (StandardOptions):
    urlname_prefix = 'logos'

    info = (
        ( _(u'About the Logo'), { 'fields': ( 'id', release_date, ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'original_cmyk', 'original_trans', 'original_trans_cmyk', 'large', 'screen' ), 'icons': { 'original': 'phot', 'original_cmyk': 'phot', 'original_trans_cmyk': 'phot', 'original_trans': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot' } } ),
        ( _(u'File Formats'), {'resources': ( 'eps', 'illustrator', 'transparent', ), 'icons': { 'eps': 'phot', 'illustrator': 'phot', 'transparent': 'phot', } } )
    )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Logos" )

    class Import( StandardOptions.Import ):
        actions = [
            move_resources,
            process_image_derivatives(),
        ]


class CalendarOptions (StandardOptions):
    urlname_prefix = 'calendars'

    info = (
        ( _(u'About the Calendar'), { 'links': ( shop_link, ), 'fields': ( 'id', 'year', 'month', ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'medium', ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', } } ),
        ( _(u'File Formats'), {'resources': ( 'pdf', 'pdfsm' ), 'icons': { 'pdf': 'doc', 'pdfsm': 'doc' } } ),
        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Calendars" )
        year = CalendarYearQuery( browsers=( 'normal', 'viewall' ), verbose_name="Calendar: %d")


class OnlineArtOptions ( StandardOptions ):

    urlname_prefix = 'art'

    info = (
        ( _(u'About the Piece'), { 'fields': ( 'id', release_date, ), } ),
        ( _(u'Author'), { 'fields': (author_name, author_location, author_link), } ),

    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'medium', 'screen'  ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'  } } ),
        )

    search_fields = (
        'id', 'title', 'description',
    )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Space Art" )

    class Import( StandardOptions.Import ):
        actions = [
            move_resources,
            process_image_derivatives(),
        ]


class OnlineArtAuthorOptions ( StandardOptions ):

    urlname_prefix = 'artists'

    info = (
        ( _(u'About the Piece'), { 'fields': ( 'id', release_date, ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'screen'  ), 'icons': { 'original': 'phot', 'screen': 'phot'  } } ),
        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Artists" )


class ElectronicCardOptions (StandardOptions):
    urlname_prefix = 'electroniccards'

    description_template = 'archives/electroniccard/object_description.html'

    info = (
        ( _(u'About the Electronic Card'), { 'fields': ( 'id', 'x_size', 'y_size', ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'medium', 'screen',), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot', } } ),
        ( _(u'File Formats'), {'resources': ( 'flash', 'pdf', 'pdfsm',), 'icons': { 'flash': 'movie', 'pdf': 'doc', 'pdfsm': 'doc', } } ),
        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Electronic Cards" )


class ExhibitionOptions ( StandardOptions ):

    urlname_prefix = 'exhibitions'

    info = (
        ( _(u'About the Exhibition'), { 'fields': ( 'id', release_date, ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'medium', 'screen',), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot', } } ),
        ( _(u'File Formats'), {'resources': ( 'pdf', 'pdfsm', 'illustrator', 'doc', 'zip'), 'icons': { 'pdf': 'doc', 'pdfsm': 'doc', 'illustrator': 'phot', 'doc': 'doc', 'zip': 'zip'  } } ),
        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Exhibitions" )


class FITSImageOptions ( StandardOptions ):

    urlname_prefix = 'fitsimages'

    info = (
        ( _(u'About the FITS Image'), { 'fields': ( 'id', 'name', 'city', 'country', ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'screen'  ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'  } } ),
    )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="FITS Liberator Images" )


class UserVideoOptions ( StandardOptions ):
    urlname_prefix = 'uservideos'

    info = (
        ( _(u'About the Video'), { 'fields': ( 'id', 'name', 'city', 'country', 'email', 'link' ), } ),
    )

    downloads = (
                ( _(u'Videos'), {
                    'resources': ( 'mov_small', 'mov_medium', 'mpg_small', 'mpg_medium', 'h264', 'broadcast', ),
                    'icons': {
                        'mov_small': 'movie',
                        'mov_medium': 'movie',
                        'mpg_small': 'movie',
                        'mpg_medium': 'movie',
                        'h264': 'movie',
                        'broadcast': 'movie',
                        }
                } ),
        )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="User Videos" )

    class Import( object ):
        uploadable = True
        metadata = 'original'
        scan_directories = [
            ( 'original', ( '.jpg', '.jpeg', '.tif', '.tiff', '.png', ) ),
            ( 'mov_small', ( '.mov', ) ),
            ( 'mov_medium', ( '.mov', ) ),
            ( 'mpg_small', ( '.mpeg', '.mpg' ) ),
            ( 'mpg_medium', ( '.mpeg', '.mpg', ) ),
            ( 'h264', ( '.mp4', '.m4v', ) ),
            ( 'broadcast', ( '.mxf', '.m2t', '.mov', ) ),
        ]
        actions = [
            move_resources,
            process_image_derivatives(),
        ]


class PresentationOptions ( StandardOptions ):
    urlname_prefix = 'presentations'

    info = (
        ( _(u'About the Presentation'), { 'fields': ( 'id', ), } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ( 'original', 'large', 'screen'  ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'  } } ),
        ( _(u'File Formats'), {'resources': ( 'ppt', 'pps', 'pdf', 'zip'  ), 'icons': { 'ppt': 'ppt', 'pps': 'ppt', 'pdf': 'doc', 'zip': 'zip' } } ),
    )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="Presentations" )


class Model3dOptions ( StandardOptions ):
    urlname_prefix = 'models3d'
    description_template = 'archives/models3d/object_description.html'

    info = (
        ( _(u'About the 3D Model'),
          { 'fields': ( 'id', release_date ),
            'category': ('archive_category')
          } ),
    )

    downloads = (
        ( _(u'Images'), {'resources': ('large', 'original'), 'icons': { 'large': 'phot', 'original': 'phot' } } ),
        ( _(u'3D Model Files'), {'resources': ( 'model_3d_c4d', 'model_3d_obj' ), 'icons': { 'model_3d_c4d': 'phot', 'model_3d_obj': 'phot' } } )
    )

    class Queries(object):
        default = AllPublicQuery( browsers=( 'normal', 'viewall' ), verbose_name="3D Models" )

    class Import( object ):
        uploadable = True
        metadata = 'original'
        scan_directories = [
            ( 'original', ( '.jpg', '.jpeg', '.tif', '.tiff', '.png', ) ),
            ( 'model_3d_c4d', ( '.c4d', '.zip') ),
            ( 'model_3d_obj', ( '.obj', '.zip') ),
        ]
        actions = [
            move_resources,
            process_image_derivatives(),
        ]


###############################
# NON-PRODUCT ARCHIVE OPTIONS #
###############################

class VisitOptions( ArchiveOptions ):
    urlname_prefix = 'visits'
    admin = ()
    downloads = ()
    search_fields = ( 'id', 'title', 'description', )

    class Queries( object ):
        default = AllPublicQuery( browsers=( 'normal', ), verbose_name="Stars@ESO", feed_name="default" )

    class Browsers( object ):
        normal = ListBrowser( paginate_by=100 )

    @classmethod
    def get_detail_urls( cls, *args, **kwargs ):
        """ No detail view for this archive """
        return []
