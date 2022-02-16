# -*- coding: utf-8 -*-
#
# djangoplicity-translation
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

"""
Middleware for setting the active language based on URL prefix.

Installation
------------

Add to settings.py::

    USE_I18N = True
    LANGUAGE_CODE = 'en'
    DEFAULT_PREFIX = "/public/"
    LANGUAGE_PREFIX = {
        "/public/chile/":"es-cl",
        "/public/denmark/":"da",
        # ...  further languages ...
    }

    if USE_I18N:
        MIDDLEWARE_CLASSES += (
            'djangoplicity.translation.middleware.LocaleMiddleware',
        )


Add to project's urls.py::

    urlpatterns = patterns('',
        # ...
        ( r'^public/news/', include('somenewsapp.urls'), { 'translate' : True } ), # Add the translate argument
        # ...
    )


After the above have been installed, you can now access::

    /public/news/... # en
    /public/denmark/news/... # da
    /public/chile/news/... # es-cl

In all three cases above, your views in installed somenewsapp.urls will see it as if the requests
where made to /public/news/ however the active language will be different in each case.

Only the views specified in urls.py with the `translate` keyword argument will be accessible in this way.
"""

from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404
from django.shortcuts import redirect
from django.utils import translation
from django.utils.http import urlencode
from djangoplicity.privacy.utils import privacy_accepted
from djangoplicity.translation.models import get_language_from_path, \
        get_path_for_language, get_querystring_from_request


LANGUAGE_COOKIE_NAME = 'preferred_language'

if hasattr(settings, 'DP_SET_NOCACHE_LANG_REDIRECT'):
    NO_CACHE = settings.DP_SET_NOCACHE_LANG_REDIRECT
else:
    NO_CACHE = False


def _is_just_media(path):
    return path.startswith(settings.MEDIA_URL) or path.startswith(settings.STATIC_URL)


def get_preferred_language(request):
    if not privacy_accepted(request) :
        # Don't read the preferred language if privacy notice wasn't accepted
        return None

    return request.COOKIES.get(LANGUAGE_COOKIE_NAME)


def set_preferred_language(request, response):
    '''
    Set the preferred language cookie
    '''
    cookie_age = getattr(settings, 'PREFERRED_LANGUAGE_COOKIE_AGE', 31536000)  # 1 year

    response.set_cookie(LANGUAGE_COOKIE_NAME, request.PREFERRED_LANGUAGE,
        max_age=cookie_age, domain=settings.SESSION_COOKIE_DOMAIN)


class LocaleMiddleware(object):
    '''
    Middleware to set LANGUAGE_CODE based on user's preferred language or path
    '''
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        response = self.get_response(request)

        response = self.process_response(request, response)

        return response

    def process_request( self, request ):
        """
        Set the language based on the prefered language (set in cookie) or
        request path and fake the request path to the standard language.

        E.g. /public/denmark/news/ will set the language to Danish, and
        rewrites the URL as though the user requested /public/news/.
        """
        if settings.USE_I18N and not _is_just_media(request.path):
            # Check if the user has a preferred language
            preferred_language = get_preferred_language(request)
            preferred_language_modified = False

            path_language, prefix, path = get_language_from_path( request.path )

            # If a preferred language was manually selected (through ?lang=)
            # we update the preferred_language
            if 'lang' in request.GET:

                # If we are in the admin we ignore ?lang as it might be
                # a simple filtering parameter from an admin list view
                try:
                    app_name = resolve(path).app_name
                except Resolver404:
                    app_name = '404'

                if app_name != 'admin':
                    language = request.GET['lang']

                    # If lang is given without value we take the language from the URL
                    if language == '':
                        preferred_language = path_language
                        preferred_language_modified = True
                    elif language in [ x[0] for x in settings.LANGUAGES ]:
                        # Check that the given language is valid
                        preferred_language = language
                        preferred_language_modified = True

            # If ?nolang is passed we use the language based on the path,
            # This is for admin/debug only and is not meant to be discoverable
            if 'nolang' in request.GET:
                preferred_language = path_language

            # If we don't have a preferred language then use the one from
            # the current path
            if not preferred_language:
                preferred_language = path_language
                preferred_language_modified = True

            request.path_info = path
            translation.activate( preferred_language )
            request.LANGUAGE_CODE = translation.get_language()
            request.MINISITE_PREFIX = prefix
            request.PATH_LANGUAGE = path_language
            request.PREFERRED_LANGUAGE = preferred_language
            request.PREFERRED_LANGUAGE_MODIFIED = preferred_language_modified

    def process_view( self, request, view_func, view_args, view_kwargs ):
        """
        We have three kind of paths:
            1. Fully translated path and models (Translate: True)
            2. Translated path, but page itself is not translated (Translate: False)
            3. No translation at all (default) (no Translate kwarg)

        In case 1. and 2. we make sure that the correct URL is being accessed
        otherwise we redirect
        """
        if settings.USE_I18N and not _is_just_media(request.path):
            preferred_language = request.PREFERRED_LANGUAGE

            # We translate all pages except if they are explicitely disabled
            # e.g. for djangoplicity.archives.contrib.security.views.serve_static_file

            if 'translate' in view_kwargs:
                translate = view_kwargs['translate']
                del view_kwargs['translate']

                # If the path language is different than the preferred one
                # we redirect to the preferred language version
                if request.PATH_LANGUAGE != preferred_language:
                    path = request.path_info
                    querystring = get_querystring_from_request(request)

                    if NO_CACHE and 'nocache' not in request.GET:
                        nocache_query = urlencode({'nocache': 'true'})
                    else:
                        nocache_query = ''

                    if querystring:
                        # Add query string to redirect path if any
                        path += '?' + querystring + nocache_query
                    elif nocache_query:
                        path += '?' + nocache_query

                    return redirect(get_path_for_language(preferred_language, path))

                if not translate:
                    # The URL is not translated, so we set a variable that can
                    # be used to display a message in the template if the
                    # default language is not in the same family as the current
                    # preferred language
                    if not preferred_language.startswith(settings.LANGUAGE_CODE):
                        request.NO_TRANSLATION = True
                    translate = True

    def process_response(self, request, response):
        """
        Ensures that the content language is included in the HTTP headers.
        """
        if settings.USE_I18N and not _is_just_media(request.path):
            if request.PREFERRED_LANGUAGE_MODIFIED and privacy_accepted(request):
                # Set the preferred language only if DJP privacy is not
                # enabled, or if is and the privacy notice has been accepted
                set_preferred_language(request, response)
            language = translation.get_language()
            translation.deactivate()
            if 'Content-Language' not in response:
                response['Content-Language'] = language
        return response
