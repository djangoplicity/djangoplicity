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

from __future__ import division
from future import standard_library
standard_library.install_aliases()
from past.utils import old_div
from bs4 import BeautifulStoneSoup
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.html import strip_tags
from django.utils.encoding import force_text
import urllib.request, urllib.parse, urllib.error

WWT_BASE_URL = "http://www.worldwidetelescope.org/wwtweb/ShowImage.aspx?"


def prepare_str( s, html=False ):
    """
    Clean string for any mark-up so that string can be shown by other applications (WWT/XMP).
    """
    s = force_text( s )
    if html:
        s = strip_tags(s)
        s = s.replace("\r\n", " ")
        s = s.replace("\n", " ")
        s = s.replace("\r", " ")
        if s:
            s = BeautifulStoneSoup( s, convertEntities=BeautifulStoneSoup.HTML_ENTITIES ).contents[0]
    return s.encode('utf8')


def rescale_wcs( new_w, new_h, ref_w, ref_h, ref_x, ref_y, scale_x, scale_y):
    """
    Rescale computed WCS for reference dimensions to picture dimensions.

    Notes:
        - Only one scale is returned and in arcseconds/pixel instead of degree/pixel
    """
    # Ratio (pixel aspect ratio must be the same, so ratio can be calculated like below)
    ratio = old_div(max( float( new_w ), float( new_h ) ), max( float( ref_w ), float( ref_h ) ))

    return (
        float( ref_x ) * ratio,
        float( ref_y ) * ratio,
        old_div(abs( float( scale_x ) ) * 3600, ratio),
    )


def wwt_show_image_url( im ):
    """
    Generate a link to show image in MS WorldWide Telescope.

    Returns None if image cannot be shown in WWT (e.g. no or incomplete WCS)
    """
    try:
        def field_to_python(obj, attr):
            return obj.__class__._meta.get_field(attr).from_internal( getattr(obj, attr) )

        spatial_reference_value = field_to_python( im, 'spatial_reference_value' )
        spatial_reference_pixel = field_to_python( im, 'spatial_reference_pixel' )
        spatial_reference_dimension = field_to_python( im, 'spatial_reference_dimension' )
        spatial_scale = field_to_python( im, 'spatial_scale' )
        rotation = im.spatial_rotation

        #
        # Perform checks
        #
        if im.spatial_quality != "Full" and im.spatial_quality != "Position":
            return None
        if not( spatial_reference_value and len( spatial_reference_value ) == 2 ):
            return None
        if not( spatial_reference_dimension and len( spatial_reference_dimension ) == 2 ):
            return None
        if not( spatial_reference_pixel and len( spatial_reference_pixel ) == 2 ):
            return None
        # Note we are currently only using one of the scales (which are usually the same for all
        # pretty pictures). WWT only want's one value for scale.
        if not( spatial_scale and len(spatial_scale) >= 1 ):
            return None

        try:
            float( rotation )
            float( spatial_reference_value[0] )
            float( spatial_reference_value[1] )
        except ValueError:
            return None

        #
        # Rescale WCS to screen resource format
        #
        # Note: all resource screen 1280px in width
        resize_ratio = 1280.0 / im.width
        screen_w = im.width * resize_ratio
        screen_h = im.height * resize_ratio

        ( ref_x, ref_y, scale ) = rescale_wcs(
            screen_w,
            screen_h,
            spatial_reference_dimension[0],
            spatial_reference_dimension[1],
            spatial_reference_pixel[0],
            spatial_reference_pixel[1],
            spatial_scale[0],
            spatial_scale[1]
        )

        ## Fix rotation to WWT expected value.
        rotation = float( rotation )
        rotation = 180 - rotation  # WWT calibration - don't know why, but we need to subtract 180 (ask Jonathan Faye)

        # Not needed
        ## WWT expect rotation within 0-360 degrees.
        #while rotation < 0: rotation += 360
        #while rotation >= 360: rotation -= 360

        #
        # WCS parameters
        #
        params = {}
        params['ra'] = float(spatial_reference_value[0])
        params['dec'] = float(spatial_reference_value[1])
        params['x'] = ref_x
        params['y'] = ref_y
        params['scale'] = scale
        params['rotation'] = rotation

        #
        # Text parameters
        #

        # Title
        subject_name = im.subject_name.all()[:1]
        if len(subject_name) > 0:
            params['name'] = prepare_str( subject_name[0].name )
        else:
            title = prepare_str( im.title )
            MAX_LEN = 40
            if len(title) > MAX_LEN:
                title = "%s..." % title[:MAX_LEN - 3]
            params['name'] = title

        # Image URL
        params['imageurl'] = "http://%s%s%s%s" % (Site.objects.get_current().domain, settings.MEDIA_URL, settings.IMAGES_ARCHIVE_ROOT, "screen/%s.jpg" % im.id )
        params['thumb'] = "http://%s%s%s%s" % (Site.objects.get_current().domain, settings.MEDIA_URL, settings.IMAGES_ARCHIVE_ROOT, "thumbs/%s.jpg" % im.id )

        # Credits
        credits = prepare_str( im.credit, html=True )
        if credits:
            if len(credits) > 20:
                params['credits'] = "For full credits, see image URL below."
            else:
                params['credits'] = credits
        else:
            params['credits'] = settings.DEFAULT_CREATOR
        params['credits'] = ""
        params['creditsUrl'] = "http://%s%s" % ( Site.objects.get_current().domain, im.get_absolute_url() )

        return "%s%s" % ( WWT_BASE_URL, urllib.parse.urlencode( params ) )
    except Exception:
        return None
