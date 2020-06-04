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
Functions for generating text for the detail pages' info boxes.
"""

from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


def shop_link( obj ):
    """
    Display helper - output link to product in shop
    """

    if hasattr( obj, 'product' ) and obj.sale and obj.product:
        return obj.product.get_absolute_url()
    else:
        return ''
shop_link.short_description = mark_safe( _( '<img src="%sicons/icon_shop.png" /> Buy in shop' % settings.MEDIA_URL ) )


def dimensions( obj ):
    """
    Display helper - output dimensions
    """
    return obj.dimensions


def language( obj ):
    """
    Display helper - output the a lagnuage
    """
    return obj.get_language_display()


def pixel_size(obj):
    """
    Display helper - output the dimensions of an image.
    """
    if obj.x_size and obj.y_size:
        return '%s x %s px' % ( obj.x_size, obj.y_size )
    else:
        return None
pixel_size.short_description = _('Pixel Size')


def resolution( obj ):
    """
    Display helper - output the resolution of an image.
    """
    if obj.resolution:
        return '%s dpi' % obj.resolution
    else:
        return None
resolution.short_description = _( 'Resolution' )


def author_name( obj ):
    """
    Display helper - output author name.
    """
    return obj.artist.name
author_name.short_description = _( 'Name' )


def author_location( obj ):
    """
    Display helper - output author location
    """
    return obj.artist.city + ', ' + obj.artist.country
author_location.short_description = _( 'Location' )


def author_link( obj ):
    """
    Display helper - output the author link
    """
    return mark_safe("<a href='%s' target='_blank'>%s</a>" % (obj.artist.link, obj.artist.link))
author_link.short_description = _( 'Website' )


def archive_image( obj ):
    """
    Display helper - output author link to image in image archive.
    """
    if obj.image:
        return mark_safe("<a href='%s'>%s</a>" % (obj.image.get_absolute_url(), obj.image.id) )
    else:
        return None
archive_image.short_description = _( 'Related archive image' )
