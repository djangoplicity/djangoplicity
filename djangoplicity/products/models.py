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
Product archive definitions.

Archive models
--------------
Not all product archives support being sold in the web shop.

The enable items in an product archive to be sold, the archive must:
 * inherit from ShopModel and PhysicalInfo
 * provide a _get_subtype function
 * connect the post_save and post delete signals to post_save_handler and post_delete_handler.
 * add the product type in get_product_types function.

"""

from datetime import date

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils.translation import ugettext_lazy as _

from djangoplicity.archives import fields as archivesfields
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.contrib import types
from djangoplicity.archives.resources import AudioResourceManager, \
    ImageFileType, ResourceManager, ImageResourceManager
from djangoplicity.media.models import Image
from djangoplicity.products.base import *
from djangoplicity.products.conf import archive_settings
from djangoplicity.translation.models import TranslationForeignKey
from djangoplicity.products.base.consts import DEFAULT_CREDIT

from django.conf import settings

if hasattr(settings, 'ENABLE_SATCHMO'):
    ENABLE_SATCHMO = settings.ENABLE_SATCHMO
else:
    ENABLE_SATCHMO = False

if ENABLE_SATCHMO:
    from product.models import Category
    from djangoplicity.archives.contrib.satchmo.models import ShopModel, \
    DEFAULT_JOB_NO_HELP_TEXT_FUNC, DEFAULT_JSP_NO_FUNC, DEFAULT_ACCOUNT_NO_FUNC
else:
    DEFAULT_JOB_NO_HELP_TEXT_FUNC = ''
    DEFAULT_JSP_NO_FUNC = ''
    DEFAULT_ACCOUNT_NO_FUNC = ''


# SATCHMO RELATED
# ===============
# Following functions are needed for Satchmo to find the custom product models.
#
# See details at http://www.satchmoproject.com/docs/rel/latest/custom-product.html
# and in the djangoplicity.archives.contrib.satchmo application.
#
SATCHMO_PRODUCT = True

class EmptyClass:
    pass

def get_product_types():
    """ Return a list of custom product models to satchmo - special function """
    if ENABLE_SATCHMO:
        return ('AnnualReport', 'Apparel', 'Book', 'Brochure', 'Bulletin', 'Calendar', 'CapJournal', 'STECFNewsletter', 'EducationalMaterial', 'Media', 'Flyer', 'Handout', 'Messenger', 'PrintedPoster', 'TechnicalDocument', 'Map', 'Merchandise', 'ScienceInSchool', 'Sticker', 'PostCard', 'ConferenceItem', 'MountedImage')
    else:
        return ()


#############################
# NON-SHOP PRODUCT ARCHIVES #
#############################

class Application ( ArchiveModel, StandardArchiveInfo ):

    itunes_link = models.URLField(blank=True, help_text='iTunes Store Link')
    marketplace_link = models.URLField(blank=True, help_text='Google Play store Link')

    class Archive( StandardArchiveInfo.Archive ):

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.APPLICATION_ROOT
            rename_pk = ( 'products_application', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        ordering = ['-priority', 'id']

    def get_absolute_url(self):
        return reverse('applications_detail', args=[str(self.id)])


# =============================================================
# Mini-sites
# =============================================================
class MiniSite( ArchiveModel, StandardArchiveInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.MINISITE_ROOT
            rename_pk = ('products_minisite', 'id')

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url(self):
        return reverse('minisites_detail', args=[str(self.id)])


# =============================================================
# Paper models
# =============================================================
class PaperModel ( ArchiveModel, StandardArchiveInfo, PrintInfo, PhysicalInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager(type=types.PDFType)

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.PAPER_MODEL_ROOT
            rename_pk = ('products_papermodel', 'id')

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url(self):
        return reverse('papermodels_detail', args=[str(self.id)])


# =============================================================
# Planetarium shows
# =============================================================
class PlanetariumShow( ArchiveModel, StandardArchiveInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.PLANETARIUM_SHOW_ROOT
            rename_pk = ( 'products_planetariumshow', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'planetariumshows_detail', args=[str( self.id )] )


# =============================================================
# Virtual tours
# =============================================================
class VirtualTour( ArchiveModel, StandardArchiveInfo, PrintInfo, PhysicalInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        tour = ResourceManager( type=types.VirtualTourType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.VIRTUAL_TOUR_ROOT
            rename_pk = ( 'products_virtualtour', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url(self):
        return reverse( 'virtualtours_detail', args=[str( self.id )] )


# =============================================================
# Kids drawings
# =============================================================
class KidsDrawing( ArchiveModel, StandardArchiveInfo ):
    name = models.CharField( max_length=255, blank=True )
    city = models.CharField( max_length=255, blank=True )
    country = models.CharField( max_length=255, blank=True )
    age = models.PositiveSmallIntegerField( blank=True )

    class Archive( StandardArchiveInfo.Archive ):
        class Meta (StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.KIDS_DRAWING_ROOT
            rename_pk = ( 'products_kidsdrawing', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( u'Kids Drawing' )

    def get_absolute_url( self ):
        return reverse( 'drawings_detail', args=[str( self.id )] )


# =============================================================
# Press kits
# =============================================================
class PressKit( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'Small PDF File' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.PRESSKIT_ROOT
            rename_pk = ( 'products_presskit', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url(self):
        return reverse('presskits_detail', args=[str(self.id)])


class Music( ArchiveModel, StandardArchiveInfo ):
    file_duration = metadatafields.AVMFileDuration()

    class Archive(StandardArchiveInfo.Archive):
        wav = AudioResourceManager(type=types.WaveAudioType)
        aac = AudioResourceManager(derived='wav', type=types.AACAudioType)
        mp3 = AudioResourceManager(type=types.Mp3AudioType)

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.MUSIC_ROOT
            rename_pk = ('products_music', 'id')

    class Meta(StandardArchiveInfo.Meta):
        verbose_name_plural = 'music'

    def get_absolute_url(self):
        return reverse('music_detail', args=[str(self.pk)])


# =============================================================
# Logos
# =============================================================
class Logo( ArchiveModel, StandardArchiveInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        original = ImageResourceManager( verbose_name=_( 'Fullsize (RGB)' ), type=types.OriginalImageType )
        original_cmyk = ImageResourceManager( verbose_name=_( 'Fullsize (CMYK)' ), type=types.OriginalImageType )
        original_trans = ImageResourceManager( verbose_name=_( 'Fullsize Transparent (RGB)' ), type=types.OriginalImageType )
        original_trans_cmyk = ImageResourceManager( verbose_name=_( 'Fullsize Transparent (CMYK)' ), type=types.OriginalImageType )

        eps = ResourceManager( type=types.EpsType )
        illustrator = ResourceManager( type=types.IllustratorType )
        transparent = ResourceManager( type=ImageFileType, verbose_name=_( 'Transparent PNG' ) )

        large = ImageResourceManager( derived='original', type=types.LargeJpegType )
        screen = ImageResourceManager( derived='original', type=types.ScreensizeJpegType )
        news = ImageResourceManager( derived='original', type=types.NewsJpegType )
        newsmini = ImageResourceManager( derived='original', type=types.NewsMiniJpegType )
        newsfeature = ImageResourceManager( derived='original', type=types.NewsFeatureType )
        medium = ImageResourceManager( derived='original', type=types.MediumJpegType )
        wallpaperthumbs = ImageResourceManager( derived='original', type=types.WallpaperThumbnailType )
        thumbs = ImageResourceManager( derived='original', type=types.ThumbnailJpegType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.LOGO_ROOT
            rename_pk = ( 'products_logo', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url(self):
        return reverse('logos_detail', args=[str(self.id)])


# =============================================================
# Art
# =============================================================
class OnlineArtAuthor ( ArchiveModel, StandardArchiveInfo ):
    title = None  # Overwrite inherited field

    name = models.CharField( max_length=255, blank=True )
    city = models.CharField( max_length=255, blank=True )
    country = models.CharField( max_length=255, blank=True )
    email = models.CharField( max_length=255, blank=True )
    link = models.CharField( max_length=255, blank=True )

    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.ONLINE_ART_AUTHOR_ROOT
            rename_pk = ( 'products_onlineartauthor', 'id' )
            rename_fks = (
                ( 'products_online_art', 'artist_id' ),
            )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = 'Space Artist'

    def get_absolute_url( self ):
        return reverse( 'artists_detail', args=[str( self.id )] )

    def __unicode__( self ):
        return self.name


class OnlineArt ( ArchiveModel, StandardArchiveInfo, ):
    artist = models.ForeignKey( OnlineArtAuthor )
    credit = None  # Overwrite inherited website.

    class Archive( StandardArchiveInfo.Archive ):
        newsmini = ImageResourceManager( derived='original', type=types.NewsMiniJpegType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.ONLINE_ART_ROOT
            rename_pk = ( 'products_onlineart', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = 'Space Art'
        verbose_name_plural = 'Space Art'

    def get_absolute_url( self ):
        return reverse( 'art_detail', args=[str( self.id )] )


# =============================================================
# Electronic Card
# =============================================================
class ElectronicCard( ArchiveModel, StandardArchiveInfo, ScreenInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        flash = ResourceManager(type=types.SwfType)

        pdf = ResourceManager(type=types.PDFType, verbose_name=_('PDF File'))
        pdfsm = ResourceManager(type=types.PDFType, verbose_name=_('Small PDF File'))

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.ELECTRONICCARD_ROOT
            rename_pk = ( 'products_electroniccard', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _('Electronic Card')
        verbose_name_plural = _('Electronic Cards')

    def get_absolute_url(self):
        return reverse('electroniccards_detail', args=[str(self.id)])


# =============================================================
# Exhibition
# =============================================================
class ExhibitionGroup( models.Model ):
    name = models.CharField( max_length=255 )
    priority = archivesfields.PriorityField( default=0 )

    class Meta:
        pass

    def __unicode__(self):
        return self.name


class Exhibition( ArchiveModel, StandardArchiveInfo ):
    group = models.ForeignKey( ExhibitionGroup, blank=True, null=True )
    group_order = models.PositiveIntegerField( blank=True, null=True )

    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager(type=types.PDFType, verbose_name=_('PDF File'))
        pdfsm = ResourceManager(type=types.PDFType, verbose_name=_('Small PDF File'))

        illustrator = ResourceManager(type=types.IllustratorType, verbose_name=_('Adobe Illustrator File'))
        doc = ResourceManager(type=types.DocType, verbose_name=_('Microsoft Word Document'))
        zip = ResourceManager( type=types.ZipType, verbose_name=_( 'InDesign file' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.EXHIBITION_ROOT
            rename_pk = ( 'products_exhibition', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        ordering = ['title', '-group__priority', 'group_order', '-priority']

    def get_absolute_url(self):
        return reverse('exhibitions_detail', args=[str(self.id)])


# =============================================================
# FITS images
# =============================================================
class FITSImage( ArchiveModel, StandardArchiveInfo ):
    name = models.CharField( max_length=255, blank=True )
    country = models.CharField( max_length=255, blank=True )
    city = models.CharField( max_length=255, blank=True )

    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.FITS_IMAGE_ROOT
            rename_pk = ( 'products_fitsimage', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( 'FITS Liberator Image' )

    def get_absolute_url( self ):
        return reverse( 'fitsimages_detail', args=[str( self.id )] )


# =============================================================
# User videos
# =============================================================
class UserVideo( ArchiveModel, StandardArchiveInfo ):
    duration = metadatafields.AVMFileDuration()
    name = models.CharField( max_length=255, blank=True )
    country = models.CharField( max_length=255, blank=True )
    city = models.CharField( max_length=255, blank=True )
    email = models.CharField( max_length=255, blank=True )
    link = models.CharField( max_length=255, blank=True )

    class Archive:
        original = ImageResourceManager( type=types.OriginalImageType )
        thumb = ImageResourceManager( derived='original', type=types.ThumbnailJpegType )
        videoframe = ImageResourceManager( derived='original', type=types.VideoFrameType )

        mov_small = ResourceManager( type=types.MovType, verbose_name=_( u"Small QT" ) )
        mov_medium = ResourceManager( type=types.MovType, verbose_name=_( u"Medium QT" ) )
        mpg_small = ResourceManager( type=types.MpegType, verbose_name=_( u"Small MPEG" ) )
        mpg_medium = ResourceManager( type=types.MpegType, verbose_name=_( u"Medium MPEG" ) )
        h264 = ResourceManager( type=types.H264Type, verbose_name=_( u"Large MPEG" ) )
        broadcast = ResourceManager( type=types.ZipType, verbose_name=_( u"Broadcast" ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.USER_VIDEO_ROOT
            rename_pk = ( 'products_uservideo', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( 'User Video' )

    def get_absolute_url( self ):
        return reverse( 'uservideos_detail', args=[str( self.id )] )


# =============================================================
# Presentations
# =============================================================
class Presentation( ArchiveModel, StandardArchiveInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF Presentation' ) )
        ppt = ResourceManager( type=types.PowerpointPresentationType )
        pps = ResourceManager( type=types.PowerpointSlideshowType )
        zip = ResourceManager( type=types.ZipType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.PRESENTATION_ROOT
            rename_pk = ( 'products_presentation', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'presentations_detail', args=[str( self.id )] )


#########################
# SHOP PRODUCT ARCHIVES #
#########################

# =============================================================
# AnnualReport
# =============================================================
class AnnualReport( ArchiveModel, StandardArchiveInfo, PrintInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager(type=types.PDFType)
        pdfsm = ResourceManager(type=types.PDFType, verbose_name=_( 'PDF File (Small)' ))
        epub = ResourceManager(type=types.EPUBType)

        ps = ResourceManager(type=types.PostScriptType)

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.ANNUAL_REPORT_ROOT
            rename_pk = ( 'products_annualreport', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url(self):
        return reverse( 'annualreports_detail', args=[str( self.id )] )

    def _get_subtype(self):
        """
        Needed by Satchmo for custom product models.
        See http://www.satchmoproject.com/docs/rel/latest/custom-product.html
        """
        return 'AnnualReport'

if ENABLE_SATCHMO:
    post_save.connect( AnnualReport.post_save_handler, sender=AnnualReport )
    post_delete.connect( AnnualReport.post_delete_handler, sender=AnnualReport )


# =============================================================
# Educational material
# =============================================================
class EducationalMaterial( ArchiveModel, StandardArchiveInfo, PrintInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.EDUMATERIAL_ROOT
            rename_pk = ( 'products_educationalmaterial', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'education_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'EducationalMaterial'

if ENABLE_SATCHMO:
    post_save.connect( EducationalMaterial.post_save_handler, sender=EducationalMaterial )
    post_delete.connect( EducationalMaterial.post_delete_handler, sender=EducationalMaterial )


# =============================================================
# Media
# =============================================================
class Media(ArchiveModel, StandardArchiveInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    """
    Optical Media such as CDs/DVDs/BluRays...
    """

    class Archive( StandardArchiveInfo.Archive ):
        zip = ResourceManager( type=types.ZipType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.MEDIA_ROOT
            rename_pk = ( 'products_media', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "Medium" )
        verbose_name_plural = _( "Media" )

    def get_absolute_url(self):
        return reverse('media_detail', args=[str(self.id)])

    def _get_subtype(self):
        return 'Media'

if ENABLE_SATCHMO:
    post_save.connect(Media.post_save_handler, sender=Media)
    post_delete.connect(Media.post_delete_handler, sender=Media)


# =============================================================
# Book
# =============================================================
class Book( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    isbn = models.CharField( max_length=255, blank=True, verbose_name=_( "ISBN" ) )
    doi = models.CharField( max_length=255, blank=True, verbose_name=_( "DOI" ) )

    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF File (Small)' ) )
        zip = ResourceManager( type=types.ZipType, verbose_name=_( 'InDesign file' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.BOOK_ROOT
            rename_pk = ( 'products_book', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'books_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Book'

if ENABLE_SATCHMO:
    post_save.connect( Book.post_save_handler, sender=Book )
    post_delete.connect( Book.post_delete_handler, sender=Book )


# =============================================================
# Brochures
# =============================================================
class Brochure( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF File (Small)' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.BROCHURE_ROOT
            rename_pk = ( 'products_brochure', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'brochures_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Brochure'

if ENABLE_SATCHMO:
    post_save.connect( Brochure.post_save_handler, sender=Brochure )
    post_delete.connect( Brochure.post_delete_handler, sender=Brochure )


# =============================================================
#  Handouts
# =============================================================
class Handout ( ArchiveModel, StandardArchiveInfo, ShopModel if ENABLE_SATCHMO else EmptyClass, PrintInfo, PhysicalInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.HANDOUT_ROOT
            rename_pk = ( 'products_handout', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'handouts_detail', args=[str( self.id )] )

    def _get_subtype(self):
        """
        Needed by Satchmo for custom product models.
        See http://www.satchmoproject.com/docs/rel/latest/custom-product.html
        """
        return 'Handout'

if ENABLE_SATCHMO:
    post_save.connect( Handout.post_save_handler, sender=Handout )
    post_delete.connect( Handout.post_delete_handler, sender=Handout )


# =============================================================
# Flyers
# =============================================================
class Flyer( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF File (Small)' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.FLYER_ROOT
            rename_pk = ( 'products_flyer', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'flyers_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Flyer'

if ENABLE_SATCHMO:
    post_save.connect( Flyer.post_save_handler, sender=Flyer )
    post_delete.connect( Flyer.post_delete_handler, sender=Flyer )


# =============================================================
# Maps
# =============================================================
class Map( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF File (Small)' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.MAP_ROOT
            rename_pk = ( 'products_map', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'maps_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Map'

if ENABLE_SATCHMO:
    post_save.connect( Map.post_save_handler, sender=Map )
    post_delete.connect( Map.post_delete_handler, sender=Map )


# =============================================================
# Stationery
# =============================================================
class Stationery( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF File (Small)' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.STATIONERY_ROOT
            rename_pk = ( 'products_stationery', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name_plural = _( 'Stationery' )

    def get_absolute_url( self ):
        return reverse( 'stationery_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Stationery'

if ENABLE_SATCHMO:
    post_save.connect( Stationery.post_save_handler, sender=Stationery )
    post_delete.connect( Stationery.post_delete_handler, sender=Stationery )


# =============================================================
# Merchandise
# =============================================================
class Merchandise( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.MERCHANDISE_ROOT
            rename_pk = ( 'products_merchandise', 'id' )

    def get_absolute_url( self ):
        return reverse( 'merchandise_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Merchandise'

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name_plural = _( 'Merchandise' )

if ENABLE_SATCHMO:
    post_save.connect( Merchandise.post_save_handler, sender=Merchandise )
    post_delete.connect( Merchandise.post_delete_handler, sender=Merchandise )


# =============================================================
# Apparel
# =============================================================
class Apparel( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.APPAREL_ROOT
            rename_pk = ( 'products_apparel', 'id' )

    def get_absolute_url( self ):
        return reverse( 'apparel_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Apparel'

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name_plural = _( 'Apparel' )

if ENABLE_SATCHMO:
    post_save.connect( Apparel.post_save_handler, sender=Apparel )
    post_delete.connect( Apparel.post_delete_handler, sender=Apparel )


# =============================================================
# STECF Newsletter
# =============================================================
class STECFNewsletter( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.STECFNEWSLETTER_ROOT
            rename_pk = ( 'products_stecfnewsletter', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "STECF Newsletter" )

    def get_absolute_url( self ):
        return reverse( 'stecfnewsletters_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'STECFNewsletter'

if ENABLE_SATCHMO:
    post_save.connect( STECFNewsletter.post_save_handler, sender=STECFNewsletter )
    post_delete.connect( STECFNewsletter.post_delete_handler, sender=STECFNewsletter )


# =============================================================
# Cap Journal
# =============================================================
class CapJournal( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF File (Small)' ) )
        epub = ResourceManager(type=types.EPUBType)

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.CAPJOURNAL_ROOT
            rename_pk = ( 'products_capjournal', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "CAPjournal" )

    def get_absolute_url( self ):
        return reverse( 'capjournals_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'CapJournal'

if ENABLE_SATCHMO:
    post_save.connect( CapJournal.post_save_handler, sender=CapJournal )
    post_delete.connect( CapJournal.post_delete_handler, sender=CapJournal )


# =============================================================
# Messenger
# =============================================================
class Messenger( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF File (Small)' ) )
        epub = ResourceManager(type=types.EPUBType)

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.MESSENGER_ROOT
            rename_pk = ( 'products_messenger', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "Messenger" )

    def get_absolute_url( self ):
        return reverse( 'messengers_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Messenger'

if ENABLE_SATCHMO:
    post_save.connect( Messenger.post_save_handler, sender=Messenger )
    post_delete.connect( Messenger.post_delete_handler, sender=Messenger )


# =============================================================
# ScienceInSchool
# =============================================================
class ScienceInSchool( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF File (Small)' ) )
        epub = ResourceManager(type=types.EPUBType)

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.SCIENCEINSCHOOL_ROOT
            rename_pk = ( 'products_scienceinschool', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "Science In School" )

    def get_absolute_url( self ):
        return reverse( 'schools_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'ScienceInSchool'

if ENABLE_SATCHMO:
    post_save.connect( ScienceInSchool.post_save_handler, sender=ScienceInSchool )
    post_delete.connect( ScienceInSchool.post_delete_handler, sender=ScienceInSchool )


# =============================================================
# Bulletin
# =============================================================
class Bulletin( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.BULLETIN_ROOT
            rename_pk = ( 'products_bulletin', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "Bulletin" )

    def get_absolute_url( self ):
        return reverse( 'bulletins_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Bulletin'

if ENABLE_SATCHMO:
    post_save.connect( Bulletin.post_save_handler, sender=Bulletin )
    post_delete.connect( Bulletin.post_delete_handler, sender=Bulletin )


# =============================================================
# Postcards
# =============================================================
class PostCard( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.POSTCARD_ROOT
            rename_pk = ( 'products_postcard', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( 'Postcard' )

    def get_absolute_url( self ):
        return reverse( 'postcards_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'PostCard'

if ENABLE_SATCHMO:
    post_save.connect( PostCard.post_save_handler, sender=PostCard )
    post_delete.connect( PostCard.post_delete_handler, sender=PostCard )


# =============================================================
# Mounted Images
# =============================================================
class MountedImage( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    image = TranslationForeignKey( Image )

    def __init__( self, *args, **kwargs ):
        # We override __init__ to prevent StandardArchiveInfo from
        # setting credit to DEFAULT_CREDIT if it's empty (instead
        # we want to take the image's credit
        super( MountedImage, self ).__init__( *args, **kwargs )
        if not self.credit:
            self.credit = self.image.credit

    def __getattr__( self, name ):
        """
        Bridge resource lookups straight to the image model. Using this method
        we don't have to change shop templates and similar to used the image
        resources.
        """
        if name.startswith( "resource_" ):
            if name == "resource_thumb":
                name = "resource_thumbs"
            return getattr( super( MountedImage, self ).__getattribute__( 'image' ), name )
        raise AttributeError

    class Archive:
        # Mounted images are relying on resources from the related image.

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.MOUNTED_IMAGE_ROOT
            rename_pk = ( 'products_mountedimage', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'mountedimages_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'MountedImage'

if ENABLE_SATCHMO:
    post_save.connect( MountedImage.post_save_handler, sender=MountedImage )
    post_delete.connect( MountedImage.post_delete_handler, sender=MountedImage )


# =============================================================
# Printed Posters
# =============================================================

class PrintedPoster( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ScreenInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):

    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        zip = ResourceManager( type=types.ZipType, verbose_name=_( 'InDesign file' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.PRINTEDPOSTER_ROOT
            rename_pk = ( 'products_printedposter', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'print_posters_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'PrintedPoster'

if ENABLE_SATCHMO:
    post_save.connect(PrintedPoster.post_save_handler, sender=PrintedPoster)
    post_delete.connect(PrintedPoster.post_delete_handler, sender=PrintedPoster)


# =============================================================
# Conference Posters
# =============================================================

class ConferencePoster( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ScreenInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):

    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        zip = ResourceManager( type=types.ZipType, verbose_name=_( 'InDesign file' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.CONFERENCEPOSTER_ROOT
            rename_pk = ( 'products_conferenceposter', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'conf_posters_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'ConferencePoster'

if ENABLE_SATCHMO:
    post_save.connect(ConferencePoster.post_save_handler, sender=ConferencePoster)
    post_delete.connect(ConferencePoster.post_delete_handler, sender=ConferencePoster)


# =============================================================
# Electronic Posters
# =============================================================

class ElectronicPoster( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ScreenInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):

    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType )
        zip = ResourceManager( type=types.ZipType, verbose_name=_( 'InDesign file' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.ELECTRONICPOSTER_ROOT
            rename_pk = ( 'products_electronicposter', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'elec_posters_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'ElectronicPoster'

if ENABLE_SATCHMO:
    post_save.connect(ElectronicPoster.post_save_handler, sender=ElectronicPoster)
    post_delete.connect(ElectronicPoster.post_delete_handler, sender=ElectronicPoster)


# =============================================================
# Stickers
# =============================================================
class Sticker( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.STICKER_ROOT
            rename_pk = ( 'products_sticker', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url(self):
        return reverse('stickers_detail', args=[str(self.id)])

    def _get_subtype(self):
        return 'Sticker'

if ENABLE_SATCHMO:
    post_save.connect(Sticker.post_save_handler, sender=Sticker)
    post_delete.connect(Sticker.post_delete_handler, sender=Sticker)


# =============================================================
# Technical Documents
# =============================================================
class TechnicalDocument( ArchiveModel, StandardArchiveInfo, PhysicalInfo, PrintInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )
        pdfsm = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.TECHDOC_ROOT
            rename_pk = ( 'products_technicaldocument', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'techdocs_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'TechnicalDocument'

if ENABLE_SATCHMO:
    post_save.connect( TechnicalDocument.post_save_handler, sender=TechnicalDocument )
    post_delete.connect( TechnicalDocument.post_delete_handler, sender=TechnicalDocument )

# =============================================================
# Calendar
# =============================================================
MONTHS_CHOICES = (
    ( 0, _( '(Main Calendar Entry)' ) ),
    ( 1, _( 'January' ) ),
    ( 2, _( 'February' ) ),
    ( 3, _( 'March' ) ),
    ( 4, _( 'April' ) ),
    ( 5, _( 'May' ) ),
    ( 6, _( 'June' ) ),
    ( 7, _( 'July' ) ),
    ( 8, _( 'August' ) ),
    ( 9, _( 'September' ) ),
    ( 10, _( 'October' ) ),
    ( 11, _( 'November' ) ),
    ( 12, _( 'December' ) ),
)


class Calendar( ArchiveModel, StandardArchiveInfo, PhysicalInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    year = models.CharField( max_length=4, blank=False, null=False, )
    month = archivesfields.ChoiceField( choices=MONTHS_CHOICES, blank=True, default=0 )

    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType, verbose_name=_( 'PDF' ) )
        pdfsm = ResourceManager( type=types.PDFType, verbose_name=_( 'Small PDF' ) )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.CALENDAR_ROOT
            release_date = True
            embargo_date = True
            last_modified = True
            created = True
            published = True
            rename_pk = ( 'products_calendar', 'id' )
            sort_fields = ['last_modified', 'release_date', 'priority', 'year', 'month', 'price']

    class Meta( StandardArchiveInfo.Meta ):
        ordering = ['-year', 'month']

    def get_absolute_url( self ):
        return reverse( 'calendars_detail', args=[str( self.id )] )

    def _get_subtype( self ):
        return 'Calendar'

    def __unicode__( self ):
        if self.month != 0:
            return 'Calendar %s %s' % ( date( year=1901, month=self.month, day=1 ).strftime( '%b' ), self.year )
        else:
            return 'Calendar %s' % self.year

if ENABLE_SATCHMO:
    post_save.connect(Calendar.post_save_handler, sender=Calendar)
    post_delete.connect(Calendar.post_delete_handler, sender=Calendar)


class Donation( ArchiveModel, StandardArchiveInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    """
    Donations
    """
    weight = 0

    def __unicode__( self ):
        return "%s - %s " % ( self.id, self.title )

    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.DONATION_ROOT
            release_date = True
            last_modified = True
            created = True
            published = True

    def _get_subtype(self):
        """
        Needed by Satchmo for custom product models.
        See http://www.satchmoproject.com/docs/rel/latest/custom-product.html
        """
        return 'Donation'

if ENABLE_SATCHMO:
    post_save.connect(Donation.post_save_handler, sender=Donation)
    post_delete.connect(Donation.post_delete_handler, sender=Donation)


class SupernovaActivity( ArchiveModel, StandardArchiveInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    """
    SupernovaActivities
    """
    weight = 0

    def __unicode__( self ):
        return "%s - %s " % ( self.id, self.title )

    class Meta:
        verbose_name = _( "ESO supernova activity" )
        verbose_name_plural = _( "ESO supernova activities" )

    class Archive( StandardArchiveInfo.Archive ):
        class Meta( StandardArchiveInfo.Archive.Meta ):
            rename_pk = ('products_supernovaactivity', 'id')
            root = archive_settings.SUPERNOVA_ACTIVITY_ROOT
            release_date = True
            last_modified = True
            created = True
            published = True

    def _get_subtype(self):
        """
        Needed by Satchmo for custom product models.
        See http://www.satchmoproject.com/docs/rel/latest/custom-product.html
        """
        return 'SupernovaActivity'

if ENABLE_SATCHMO:
    post_save.connect(SupernovaActivity.post_save_handler, sender=SupernovaActivity)
    post_delete.connect(SupernovaActivity.post_delete_handler, sender=SupernovaActivity)


# =============================================================
# IMAX Films
# =============================================================
class IMAXFilm( ArchiveModel, StandardArchiveInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.IMAX_FILM_ROOT
            rename_pk = ( 'products_imaxfilm', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        pass

    def get_absolute_url( self ):
        return reverse( 'imaxfilms_detail', args=[str( self.id )] )


# =============================================================
# ePublication
# =============================================================
class EPublication( ArchiveModel, StandardArchiveInfo ):
    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.EPUBLICATION_ROOT
            rename_pk = ( 'products_epublication', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "ePublication" )

    def get_absolute_url( self ):
        return reverse( 'epublications_detail', args=[str( self.id )] )


# =============================================================
# Conferences
# =============================================================
class ConferenceItem( ArchiveModel, StandardArchiveInfo, ShopModel if ENABLE_SATCHMO else EmptyClass ):
    """
    A conference item can be anything that should be sold in connection with payment for a conference.
    This could include items such as:
        * registration fee
        * registration fee student
        * dinner ticket
        * guest dinner ticket
        * some social event
        * etc.
    """
    # Since we shouldn't add any shipping costs to conference items, we set the weight to 0. (attr required by ShopModel)
    weight = 0
    conference = models.ForeignKey( 'products.Conference' )

    def save( self, **kwargs ):
        if self.conference and self.conference.job:
            self.job = self.conference.job
        if self.conference and self.conference.jsp:
            self.jsp = self.conference.jsp
        if self.conference and self.conference.account_no:
            self.account_no = self.conference.account_no
        super( ConferenceItem, self ).save( **kwargs )

    class Archive( StandardArchiveInfo.Archive ):
        pdf = ResourceManager( type=types.PDFType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.CONFERENCEITEM_ROOT
            rename_pk = ( 'products_conferenceitem', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "Conference" )

    def _get_subtype( self ):
        return 'ConferenceItem'

    def update_categories( self, product, add=True ):
        """
        Override hook for specifying the product categories.
        """
        # First create the main category as usual.
        categories = super( ConferenceItem, self ).update_categories( product, add=False )

        if len( categories ) != 1 or self.conference is None:
            # TODO: Error handling. We need only one main category.
            return categories

        main_category = categories[0]

        # Add a sub category for each conference
        try:
            category = Category.objects.get( site=Site.objects.get_current(), slug=self.conference.id, parent=main_category )
        except Category.DoesNotExist:
            category = Category( site=Site.objects.get_current(), slug=self.conference.id, parent=main_category, name=self.conference.title )
            category.save()

        if add:
            product.category.add( category )

        return [main_category, category]


if ENABLE_SATCHMO:
    post_save.connect( ConferenceItem.post_save_handler, sender=ConferenceItem )
    post_delete.connect( ConferenceItem.post_delete_handler, sender=ConferenceItem )


def DEFAULT_CONFERENCE_JOB_NO_HELP_TEXT_FUNC():
    return DEFAULT_JOB_NO_HELP_TEXT_FUNC(ConferenceItem.default_job())


def DEFAULT_CONFERENCE_JSP_NO_FUNC():
    return DEFAULT_JSP_NO_FUNC(ConferenceItem.default_jsp())


def DEFAULT_CONFERENCE_ACCOUNT_NO_FUNC():
    return DEFAULT_ACCOUNT_NO_FUNC(ConferenceItem.default_account_no())


class Conference( models.Model ):
    """
    A conference groups together related items (registration fee, dinner tickets etc), and
    ensures that all items have proper job/jsp set.
    """
    id = archivesfields.IdField()
    title = archivesfields.TitleField()
    description = archivesfields.DescriptionField()
    start_date = models.DateField( blank=True, null=True )
    end_date = models.DateField( blank=True, null=True )
    max_participants = models.PositiveIntegerField( blank=True, null=True )
    # Navision job no.
    job = models.CharField( max_length=4, blank=True, help_text=DEFAULT_CONFERENCE_JOB_NO_HELP_TEXT_FUNC )

    # Navision JSP no.
    jsp = models.IntegerField( verbose_name=_( 'JSP' ), null=True, blank=True, help_text=DEFAULT_CONFERENCE_JSP_NO_FUNC )

    # Navision account no.
    account_no = models.CharField( max_length=10, blank=True, help_text=DEFAULT_CONFERENCE_ACCOUNT_NO_FUNC )

    class Meta:
        verbose_name = _( "conference type" )
        verbose_name_plural = _( "conference type" )

    def __unicode__( self ):
        return "%s - %s " % ( self.id, self.title )

    @classmethod
    def post_save_handler( cls, sender, instance, created, raw=False, **kwargs ):
        """ Ensure job/jsp/account no is propagated to conference items """
        if raw:
            return
        if instance.job or instance.jsp or instance.account_no:
            for item in instance.conferenceitem_set.all():
                item.save()  # ConferenceItem will copy the job/jsp/account_no on save.

if ENABLE_SATCHMO:
    post_save.connect( Conference.post_save_handler, sender=Conference )


# =============================================================
# 3D models
# =============================================================
class Model3d( ArchiveModel, StandardArchiveInfo ):
    sketchfab_id = models.CharField( max_length=255, blank=True, help_text=_('Model ID if uploaded on sketchfab'))

    class Archive( StandardArchiveInfo.Archive ):
        model_3d_obj = ResourceManager( type=types.Model3dObjType )
        model_3d_c4d = ResourceManager( type=types.Model3dC4DType )

        class Meta( StandardArchiveInfo.Archive.Meta ):
            root = archive_settings.MODEL3D_FILM_ROOT
            rename_pk = ( 'products_model3d', 'id' )

    class Meta( StandardArchiveInfo.Meta ):
        verbose_name = _( "3D Model" )

    def get_absolute_url( self ):
        return reverse( 'models3d_detail', args=[str( self.id )] )

########################
# NON-PRODUCT ARCHIVES #
########################


# =============================================================
# Media visits
# =============================================================
class Visit( ArchiveModel, models.Model ):
    """
    Archive of media visits
    """
    id = archivesfields.IdField()
    title = archivesfields.TitleField()
    description = archivesfields.DescriptionField( blank=True )
    image = models.ForeignKey( Image, null=True, blank=True )

    def get_absolute_url( self ):
        return "%s?search=%s" % ( reverse( 'visits_defaultquery' ), self.id )

    class Archive:
        class Meta:
            root = archive_settings.VISIT_ROOT
            release_date = True
            embargo_date = False
            last_modified = True
            created = True
            published = True
            sort_fields = ['release_date', ]

    class Meta:
        ordering = ['-release_date']

    def __unicode__( self ):
        return "%s: %s" % ( self.id, self.title)
