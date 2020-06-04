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
Base archive definitions across all product archives.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _
from djangoplicity.archives import fields as archivesfields
from djangoplicity.archives.contrib import types
from djangoplicity.archives.resources import ImageResourceManager
from djangoplicity.metadata.archives import fields as metadatafields
from djangoplicity.products.base.consts import DEFAULT_CREDIT, COVER_CHOICES, \
    LANGUAGE_CHOICES
from djangoplicity.products.base.consts import DEFAULT_CREDIT_FUNC


class ArchiveCategory(models.Model):
    '''
    Categories for Archive Items
    '''
    name = models.CharField(max_length=10, primary_key=True)
    fullname = models.CharField(max_length=50, verbose_name='Archive Item Category')

    class Meta:

        verbose_name = 'Archive Category'
        verbose_name_plural = 'Archive Categories'

    def __unicode__(self):

        return self.fullname


class StandardArchiveInfo( models.Model ):
    """
    Abstract model containing fields shared across all archives
    """
    def __init__( self, *args, **kwargs ):
        super( StandardArchiveInfo, self ).__init__( *args, **kwargs )
        # If credit is not set, the set default credit in object.
        if not self.credit:
            self.credit = DEFAULT_CREDIT

    id = archivesfields.IdField()
    title = archivesfields.TitleField()
    description = archivesfields.DescriptionField()
    priority = archivesfields.PriorityField( default=0 )
    credit = metadatafields.AVMCreditField( default=DEFAULT_CREDIT_FUNC )

    # Add the possibility to choose categories
    archive_category = models.ManyToManyField(ArchiveCategory, blank=True)

    class Meta:
        abstract = True
        ordering = ['-priority', '-id', ]

    class Archive:
        """
        All product archives will inherit these resources.
        """
        original = ImageResourceManager( type=types.OriginalImageType )
        large = ImageResourceManager( derived='original', type=types.LargeJpegType )
        medium = ImageResourceManager( derived='original', type=types.MediumJpegType )
        screen = ImageResourceManager( derived='original', type=types.ScreensizeJpegType )
        thumb = ImageResourceManager( derived='original', type=types.ThumbnailJpegType )

        class Meta:
            release_date = True
            embargo_date = True
            last_modified = True
            created = True
            published = True
            sort_fields = ['last_modified', 'release_date', 'priority', ]

    def __unicode__( self ):
        """
        Default is to return the id as name.
        """
        return self.id


class PhysicalInfo ( models.Model ):
    """
    Abstract model containing fields shared across all archives of
    physical objects e.g. brochures, posters, merchandise etc.
    """
    width = models.CharField( blank=True, max_length=10, help_text=_( u'(cm)' ) )
    height = models.CharField( blank=True, max_length=10, help_text=_( u'(cm)' ) )
    depth = models.CharField( blank=True, max_length=10, help_text=_( u'(cm)' ) )
    weight = models.CharField( blank=True, max_length=10, help_text=_( u'(g)' ), default=0 )

    def _dimensions( self ):
        """
        Get a formatted string of the dimensions
        """
        dim = []

        if self.width:
            dim.append( "%s cm (W)" % self.width )
        if self.height:
            dim.append( "%s cm (H)" % self.height )
        if self.depth:
            dim.append( "%s cm (D)" % self.depth )

        return " x ".join( dim )

    size = property( _dimensions )
    dimensions = property( _dimensions )

    class Meta:
        abstract = True


class PrintInfo( models.Model ):
    """
    Abstract model containing fields shared across all archives of
    print products
    """
    pages = models.PositiveSmallIntegerField( blank=True, help_text=_( u'Number of pages' ), null=True )
    cover = models.CharField( blank=True, choices=COVER_CHOICES, max_length=9, help_text=_( u'Type of cover' ) )
    language = models.CharField( blank=True, choices=LANGUAGE_CHOICES, max_length=2 )

    class Meta:
        abstract = True


class ScreenInfo ( models.Model ):
    """
    Abstract model containing fields shared across all archives of
    screen products (e.g. resolution, x_res, y_res)
    """
    resolution = models.IntegerField( blank=True, help_text=_( u'Resolution (DPI)' ), default=0 )
    x_size = models.IntegerField( blank=True, help_text=_( u'X size (px)' ), null=True )
    y_size = models.IntegerField( blank=True, help_text=_( u'Y size (px)' ), null=True )

    class Meta:
        abstract = True
