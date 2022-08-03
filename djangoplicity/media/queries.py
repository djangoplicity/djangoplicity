# coding: utf-8
#
# Djangoplicity
# Copyright 2008 ESA/Hubble & International Astronomical Union
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from datetime import datetime
from djangoplicity.archives.contrib.queries import AllPublicQuery
from djangoplicity.metadata.archives.queries import WebCategoryQuery
from djangoplicity.archives.contrib.queries.defaults import StagingQuery, EmbargoQuery


class WebCategoryPublicQuery(WebCategoryQuery):
    """
    Query for public images in a certain category, which takes into account that an
    image can be bound by its release.
    """
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( WebCategoryPublicQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.prefetch_related('pictureoftheweek_set')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        qs = qs.filter( published=True )
        return ( qs, query_data )


class VideoWebCategoryPublicQuery(WebCategoryPublicQuery):
    '''
    Query to prefetch the subtitles
    '''
    def queryset( self, model, options, request, **kwargs ):
        ( qs, query_data ) = super( VideoWebCategoryPublicQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.prefetch_related('videosubtitle_set')
        return ( qs, query_data )


class WallpaperQuery( AllPublicQuery ):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( WallpaperQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( wallpapers=True ).prefetch_related('pictureoftheweek_set')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class ObservationQuery( AllPublicQuery ):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( ObservationQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( published=True ).prefetch_related('pictureoftheweek_set')
        qs = qs.filter( spatial_quality='Full', type='Observation' )
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class ZoomableQuery( AllPublicQuery ):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( ZoomableQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( zoomify=True ).prefetch_related('pictureoftheweek_set')
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class PrintLayoutQuery( AllPublicQuery ):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( PrintLayoutQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( print_layout=True )
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class VideoQuery( AllPublicQuery ):
    '''
    Query to prefetch the subtitles
    '''
    def queryset( self, model, options, request, **kwargs ):
        ( qs, query_data ) = super( VideoQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.prefetch_related('videosubtitle_set')
        return ( qs, query_data )


class WWTQuery( AllPublicQuery ):
    def queryset( self, model, options, request, **kwargs ):
        now = datetime.now()
        ( qs, query_data ) = super( WWTQuery, self ).queryset( model, options, request, **kwargs )
        qs = qs.filter( spatial_quality='Full' )
        qs = self._filter_datetime( qs, now, 'release_date', False, True )
        qs = self._filter_datetime( qs, now, 'embargo_date', False, True )
        return ( qs, query_data )


class ImageAllPublicQuery(AllPublicQuery):
    '''
    Query to prefetch the related potws
    '''
    def queryset(self, model, options, request, **kwargs):
        (qs, query_data) = super(ImageAllPublicQuery, self).queryset(model, options, request, **kwargs)
        qs = qs.prefetch_related('pictureoftheweek_set')
        return (qs, query_data)


class ImageStagingQuery(StagingQuery):
    '''
    Query to prefetch the related potws
    '''
    def queryset(self, model, options, request, **kwargs):
        (qs, query_data) = super(ImageStagingQuery, self).queryset(model, options, request, **kwargs)
        qs = qs.prefetch_related('pictureoftheweek_set')
        return (qs, query_data)


class ImageEmbargoQuery(EmbargoQuery):
    '''
    Query to prefetch the related potws
    '''
    def queryset(self, model, options, request, **kwargs):
        (qs, query_data) = super(ImageEmbargoQuery, self).queryset(model, options, request, **kwargs)
        qs = qs.prefetch_related('pictureoftheweek_set')
        return (qs, query_data)


class PotwAllPublicQuery(AllPublicQuery):
    '''
    Query to prefetch the related potws
    '''
    def queryset(self, model, options, request, **kwargs):
        (qs, query_data) = super(PotwAllPublicQuery, self).queryset(model, options, request, **kwargs)
        qs = qs.select_related('image', 'image__source')
        return (qs, query_data)
