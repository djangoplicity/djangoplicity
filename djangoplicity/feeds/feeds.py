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

"""
Feeds Module Documentation.
The Feeds module allows dynamic definition of RSS Feeds of any media type.
For archive feeds, please refer to djangoplicity.archives.feeds
"""

from past.builtins import basestring
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.feedgenerator import Rss201rev2Feed


class DjangoplicityFeed( Feed ):
    """
    Base class for RSS Feeds. Several attributes are defined here.
    """
    author = ''
    title_template = 'feeds/title.html'
    description_template = 'feeds/description.html'
    link = '/'

    header_template = None

    def __call__(self, request, *args, **kwargs):
        '''
        Django doesn't provide an easy way to cache a Feed, so we hijack
        the __call__ method and do it here instead
        '''
        key = self.get_cache_key(*args, **kwargs)
        response = cache.get(key)
        if response is None:
            response = super(DjangoplicityFeed, self).__call__(request, *args,
                **kwargs)
            cache.set(key, response, 60 * 10)  # Cache for 10 minutes

        return response

    def get_cache_key(self, *args, **kwargs):
        '''
        Generate a unique key based on all the kwargs
        '''
        model = kwargs['model']
        words = [k + '-' + v for k, v in list(kwargs.items()) if isinstance(v, basestring)]
        words.append(translation.get_language())
        return '{}-{}-{}-{}-feed'.format(
            model._meta.app_label,
            model._meta.model_name,
            kwargs['name'],
            '-'.join(words),
        )


class DjangoplicityFeedGen( Rss201rev2Feed ):
    def add_root_elements( self, handler ):
        """
        Adds root elements to the feed. If header_template var is specified in the
        feed object, this template will be loaded and rendered into the header of the feed
        (just before the first <item />). These keywords can be defined in the
        item_extra_kwargs on the Feed class
        """
        super(DjangoplicityFeedGen, self).add_root_elements( handler )
        template = self.feed.get( 'header_template', None )
        template_vars = {}

        if self.feed.get( 'format', None ):
            template_vars['format'] = self.feed.get( 'format', None )

        if template:
            handler._write( render_to_string( template, template_vars ) )
