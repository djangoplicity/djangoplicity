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
from past.utils import old_div
import math

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext

from djangoplicity.archives.contrib.info import boolean_property
from djangoplicity.media.models import Video
from djangoplicity.translation.models import TranslationModel


import django
if django.VERSION >= (2, 2):
    from django.urls import reverse, NoReverseMatch
else:
    from django.core.urlresolvers import NoReverseMatch, reverse

# =================
# Utility functions
# =================

def _related_objects( obj, attr ):
    """ Get the link to a related objects. """
    try:
        objects = getattr( obj, attr ).all()
        link = '<a href="%s">%s</a>'

        links = []
        for o in objects:
            # If both are models allow translations, then get the correct language of the releated object
            o_id = o.id
            if settings.USE_I18N and isinstance( obj, TranslationModel ) and isinstance( o, TranslationModel ):
                if obj.lang != o.lang:
                    try:
                        o = o.translations.select_related( 'source' ).get( lang=obj.lang )
                        o_id = o.id if o.is_source() else o.source.id
                    except ObjectDoesNotExist:
                        pass
            links.append( link % ( o.get_absolute_url(), o_id ) )

        return mark_safe( ", ".join( links ) )
    except (NoReverseMatch, AttributeError):
        pass
    return None


def _distance( x ):
    """
    Round distance to two digits (if error is acceptable second digit
    will be 0 or 5).
    """
    l = int( math.log10( x ) )
    x1 = old_div(x, math.pow(10, l))  # x, scale to [0,10[ (i.e one digit)
    x2 = old_div(x, math.pow(10, l - 1))  # x, scale to [0,100[ (i.e two digits)

    digit2 = int(x2 + 0.5) - 10 * int(x1)  # second digit
    digit2_05 = int(digit2 / 5.0 + 0.5) * 5.0   # second digit, rounded to 0 or 5

    x_round2_05 = ( int(x1) + digit2_05 / 10.0 ) * math.pow( 10, l )  # x, with 2nd digit rounded to 0 or 5
    x_error2_05 = abs( old_div(( x_round2_05 - x ), x) )  # error on x_round2_05
    x_round2 = int( x2 + 0.5 ) * math.pow( 10, l - 1 )  # x, with 2nd digit rounded

    if x_error2_05 <= 0.07:
        return x_round2_05
    else:
        return x_round2


def _intword(value):
    value = int(value)
    if value < 1000000:
        return value
    if value < 1000000000:
        new_value = value / 1000000.0
        return '%(value).0f %(name)s' % {'value': new_value, 'name': ugettext('million') }
    if value < 1000000000000:
        new_value = value / 1000000000.0
        return '%(value).0f %(name)s' % {'value': new_value, 'name': ugettext('billion') }
    if value < 1000000000000000:
        new_value = value / 1000000000000.0
        return '%(value).0f %(name)s' % {'value': new_value, 'name': ugettext('trillion')}
    return value

# ===============
# Display helpers
# ===============


def zoomable( obj ):
    """ Admin display helper - show if image has zoomify enabled """
    return boolean_property( obj.zoomify )


def wallpapers( obj ):
    """ Admin display helper - show if image has wallpapers enabled """
    return boolean_property( obj.wallpapers )


def pixel_size( obj ):
    """ Display helper - output the dimensions of an image. """
    if obj.width and obj.height:
        return '%s x %s px' % ( obj.width, obj.height )
    else:
        return None
pixel_size.short_description = _( 'Size' )


def fov(obj):
    '''
    Display helper: Image FOV (x and y)
    '''
    if obj.fov_x and obj.fov_y:
        return u'%g° x %g°' % (obj.fov_x, obj.fov_y)
    elif obj.fov_x:
        return u'%g° x' % obj.fov_x
    elif obj.fov_y:
        return u'x %g°' % obj.fov_y
    else:
        return None
fov.short_description = _('Field of View')


def related_releases( obj ):
    """ Display related releases """
    return _related_objects( obj, 'release_set' )
related_releases.short_description = _( 'Related releases' )


def related_announcements( obj ):
    """ Display related announcements """
    return _related_objects( obj, 'announcement_set' )
related_announcements.short_description = _( 'Related announcements' )


def related_science_announcements( obj ):
    """ Display related science announcements """
    return _related_objects( obj, 'scienceannouncement_set' )
related_science_announcements.short_description = _( 'Related science announcements' )


def object_id( obj ):
    if settings.USE_I18N and isinstance( obj, TranslationModel ) and obj.id:
        return obj.id if obj.is_source() else obj.source_id
    return obj.id
object_id.short_description = _( 'Id' )


def object_type( obj ):
    if settings.USE_I18N and isinstance( obj, TranslationModel ) and obj.type:
        return _( obj.type )
    return obj.type
object_type.short_description = _( 'Type' )


def object_language( obj ):
    if settings.USE_I18N and isinstance( obj, TranslationModel ):
        if not obj.is_source() and obj.lang:
            return obj.lang
    return None
object_language.short_description = _( 'Language' )


def duration(obj):
    '''
    Write duration for videos
    '''
    if obj.file_duration:
        (h, m, s, _f) = obj.file_duration.split(':')

        if int(h) > 0:
            return _('%(hours)s h %(minutes)s m %(seconds)s s') % {
                'hours': h, 'minutes': m, 'seconds': s}
        elif int(m) > 0:
            return _('%(minutes)s m %(seconds)s s') % {
                'minutes': m, 'seconds': s}
        else:
            return _('%(seconds)s s') % {'seconds': s}
    return None
duration.short_description = _('Duration')


def frame_rate(obj):
    if obj.frame_rate:
        return _('{} fps'.format(obj.frame_rate))

    return None
frame_rate.short_description = _('Frame rate')


def distance( obj ):
    """
    Display human readable distance to an object based
    on light years distance or redshift.
    """
    if obj.distance_ly or obj.distance_z:
        ly = obj.distance_ly

        if ly:
            try:
                ly = float( ly )
            except ValueError:
                ly = None

        z = obj.distance_z
        if z:
            try:
                z = float( z )
            except ValueError:
                z = None

        if ly and obj.distance_ly_is_accurate:
            lystr = ("%s <a href=\"http://en.wikipedia.org/wiki/Light-year\">%s</a><br />" % ( _intword( ly ), ugettext("light years") ))
        elif ly:
            lystr = ("%s <a href=\"http://en.wikipedia.org/wiki/Light-year\">%s</a><br />" % ( _intword( _distance( ly ) ), ugettext("light years") ))
        else:
            lystr = ''

        zstr = "z=%s (<a href=\"http://en.wikipedia.org/wiki/Redshift\">%s</a>)<br />" % ( z, ugettext('redshift') ) if z else ""

        str = ""
        if lystr:
            str += lystr
        if zstr:
            str += zstr

        return mark_safe( str )
    else:
        return ""


def constellation(obj):
    try:
        import ephem
    except ImportError:
        return ''
    a = obj.get_ra_verbose(om=False)
    b = obj.get_dec_verbose(om=False)

    if a == '' or b == '':
        return ''
    try:
        _abbr, const = ephem.constellation([ephem.hours(a), ephem.degrees(b)])
    except SystemError:
        return ''
    return const


# ================
# Info helpers
# ================

def rel_shop_link( obj ):
    """
    Display helper - output link to product in shop
    """

    #  Check if the media is linked to shop items and return the first one found:
    #  TODO: return all valid items from shop
    if hasattr( obj, 'mountedimage_set' ):
        for rel in obj.mountedimage_set.all():
            if hasattr( rel, 'product' ) and rel.sale and rel.product:
                return rel.product.get_absolute_url()
    return ''
rel_shop_link.short_description = mark_safe( _( '<img src="%sicons/icon_shop.png" /> Buy in shop' % settings.MEDIA_URL ) )


# ================
# Download helpers
# ================

def zoomable_link( obj ):
    """ Generate a zoomify link"""
    if obj.zoomify:
        return {
            'url': 'zoomable/',
            'size': None,
#           'extra_attrs': mark_safe(flatatt({'rel': 'shadowbox;player=iframe', 'title': obj.title})),
        }
    else:
        return None
zoomable_link.short_description = _( 'Zoomable' )


def image_magnet_uri_link( obj ):
    """  Generate an image's magnet_uri"""
    if obj.magnet_uri:
        return {
            'url': obj.magnet_uri,
            'extra_attrs': None,
            'size': getattr( obj, "resource_original" ).size,
        }
    else:
        return None
image_magnet_uri_link.short_description = _( 'Magnet Fullsize Original' )


def video_magnet_uri_link( obj ):
    """  Generate a video's magnet_uri"""
    if obj.magnet_uri:
        return {
            'url': obj.magnet_uri,
            'extra_attrs': None,
            'size': getattr( obj, "resource_hd_and_apple" ).size
        }
    else:
        return None
video_magnet_uri_link.short_description = _( 'Magnet Hd & Apple TV' )


def wwt_link( obj ):
    """ Get link to Microsoft World Wide Telescope """
    if obj.spatial_quality == 'Full':
        wwturl = obj.get_wwt_url()

        return wwturl if wwturl else None
    return None
wwt_link.short_description = _("View in WorldWide Telescope")


def shadowbox_link( resource, default_width, default_height, player=None ):
    """ Make a shadow box link """
    def shadowbox_link( obj ):  # pylint: disable=W0621
        if getattr( obj, "resource_%s" % resource ):
            return {
                    'url': getattr( obj, "resource_%s" % resource ).url,
                    'size': getattr( obj, "resource_%s" % resource ).size,
                    'extra_attrs': mark_safe( flatatt( {
                        'rel': 'shadowbox;width=%s;height=%s%s' % ( default_width, default_height, ';player=%s' % player if player else '' ),
                        'title': obj.title,
                    } ) ),
                    }
        else:
            return None
    shadowbox_link.short_description = getattr( Video.Archive, resource ).verbose_name
    return shadowbox_link


def web_categories( obj ):
    '''
    Display helper for showing the web categories
    '''
    cat = ''.join([
        '<a href="%s">%s</a><br>' % (
            reverse('%ss_query_category' % obj._meta.model_name, args=[c.url]), c
        )
        for c in obj.web_category.all()
    ])

    if cat:
        return mark_safe( cat )
    else:
        return ''
web_categories.short_description = _('Category')
