# -*- coding: utf-8 -*-
#
# djangoplicity-feeds
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#   * Neither the name of the European Southern Observatory nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
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

from builtins import object
from django.conf import settings

feed_settings = None

try:
    feed_settings = __import__( settings.FEED_SETTINGS_MODULE )
    feed_settings = feed_settings.feed_settings
except ( AttributeError, ImportError ):
    pass


class DefaultFeedSettings( object ):
    title = 'Feed'
    link = '/'
    description = 'Generic RSS Feed'
    title_template = None
    description_template = None
    enclosure_resources = { '': None }
    override_guids = None
    external_feed_url = None


def get( clsname, attrname, default=None ):
    """
    Main method for getting attributes, e.g.::

        from djangoplicity.feeds import conf
        conf.get( 'ReleaseFeed', 'title' )
    """
    try:
        # look for class name in feed settings
        cls = getattr( feed_settings, clsname )
        # look for attribute in custom class
        return getattr( cls, attrname )
    except AttributeError:
        if default is not None:
            # if default, return it,
            return default
        else:
            # otherwise get it from DefaultFeedSetings
            return getattr( DefaultFeedSettings, attrname )


def get_by_category( category, attrname, default=None ):
    """
    """
    try:
        catspec = getattr( feed_settings, 'CATEGORY_SPECIFIC_SETTINGS' )
        if not category in catspec:
            raise AttributeError( 'Category not found' )
        else:
            return get( catspec[category], attrname, default )
    except AttributeError:
        return default


def get_formats( default=None ):
    """
    """
    try:
        return feed_settings.FORMATS
    except AttributeError:
        return default
