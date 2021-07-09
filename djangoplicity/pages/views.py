# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
# The source code in this file is originally based on source code from
# the django.contrib.flatpages.views django application licensed under the BSD License.
# -------------------------------------------------------------------------------
# Copyright (c) 2005, the Lawrence Journal-World
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of Django nor the names of its contributors may be used
#       to endorse or promote products derived from this software without
#       specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from django.template import engines
from django.template.loader import select_template
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect
from django.conf import settings
from django.utils import translation
from django.utils.safestring import mark_safe
from django.core.cache import cache

import logging

from djangoplicity.pages.models import PageGroup
from djangoplicity.archives.utils import is_internal
from djangoplicity.archives.contrib.info.defaults import admin_edit_for_site
from djangoplicity.pages.models import Page, PageProxy, CACHE_KEY, \
    build_page_key_index, build_urlindex
from djangoplicity.translation.models import get_path_for_language, get_querystring_from_request


logger = logging.getLogger(__name__)


class PageNotFoundError( Exception ):
    """
    Error signaling that a page could not be found. This could
    be because the
        * page doesn't exists
        * page is inactive
        * page is unpublished (start/end publishing)
    """
    pass


class PageAuthorizationError( Exception ):
    """
    Error signaling that the current users does not have
    privileges to see this page.
    """
    pass


def _authorize_pageview( request, page, no_unpublished=False ):
    """
    Check authorization of a request for a given page.

        * Staff users with permissions pages.can_view_inactive can
        view all pages. Even inactive and unpublished ones.
        * Some pages requires logged in users.
        * Some pages are unpublished.
    If no_unpublished is True unpublished pages will only be authorized if
    the 'preview' GET parameter is passed '''
    """
    # Page Protection
    # ---------------
    # Authentication and active pages.
    #  - Staff users with 'pages.can_view_inactive' permissions can view pages online
    #    even if they are inactive (this is a preview functionality).

    if not ( request.user.is_staff and request.user.has_perm('pages.can_view_inactive') ):
        # If not active, page should not be found
        if not page.is_online():
            raise PageNotFoundError
        # If registration is required for accessing this page, and the user isn't
        # logged in, redirect to the login page.
        if page.login_required and not request.user.is_authenticated():
            raise PageAuthorizationError
            # User tests passed
    else:
        # Fri Feb 21 15:27:07 CET 2014 - Mathias
        # Not sure why we clear the cache if an admin views the page...
        if not page.is_online():
            if no_unpublished and 'preview' not in request.GET:
                raise PageNotFoundError
            if page.embedded:
                cache.delete( CACHE_KEY['embedded_pages'] + page.id )
            else:
                for url in page.url_set.all():
                    cache.delete( '%s_%s_internal' % (CACHE_KEY['pages'], str(url.url.__hash__())) )
                    cache.delete( '%s_%s_external' % (CACHE_KEY['pages'], str(url.url.__hash__())) )


def embed_page_key( request, page_key, no_unpublished=False ):
    """
    Wrapper for embed_page, that looks up the page id for a given
    key.
    If no_unpublished is True unpublished pages will only be embedded if the
    'preview' GET parameter is passed '''
    """
    index = cache.get( CACHE_KEY['embedded_page_keys'] )

    if index is None:
        index = build_page_key_index()

    if index is not None and page_key in index:
        return embed_page( request, index[page_key], no_unpublished=no_unpublished )
    else:
        raise PageNotFoundError()


def embed_page( request, page_id, no_unpublished=False ):
    """
    Utility function for embedding pages into other views. The function
    will render the content of a page and SafeString with the HTML, ready
    to be inserted into another template.

    The function raises a PageNotFoundError in case the pages is not marked
    embedded, or is not published yet.
    The function raises a PageAuthorizationError in case the user is not
    authorized to view the page.

    The function has the following features:
    * Authentication::
        * Staff users with pages.can_view_inactive permissions can see all pages
        (inactive as well as login protected)
        * Pages can be require login/authentication
    * Caching::
        * For static pages the entire page content is cached.
        * For dynamic pages the compiled template is cached.
    * Dynamic content::
        * By default only MEDIA_URL is available as variable, beside the normal
        template markup.
    * Pages can be embedded cannot be viewed through this view, but should
        use the embed_page view.
    If no_unpublished is True unpublished pages will only be embedded if
    the 'preview' GET parameter is passed '''
    """
    #
    # Initial loading of cache
    #
    page_id = str(page_id)

    cache_key = CACHE_KEY['embedded_pages'] + page_id

    if settings.USE_I18N:
        cache_key += '_%s' % translation.get_language()

    page_cache = cache.get( cache_key )

    if page_cache is not None:
        page = page_cache['page']
    else:
        try:
            page = get_object_or_404( Page, pk=page_id, embedded__exact=1 )
        except Http404:
            # ReCast a Http404 to a PageNotFoundError
            raise PageNotFoundError

    if settings.USE_I18N:
        lang = translation.get_language()

        if lang != page.lang:
            # Next we check if we have a translation for the page, in which
            # case we use it, othewise we use the original version
            try:
                trans = page.translations.get(lang=lang)
                if trans.published and trans.translation_ready:
                    page = trans
            except Page.DoesNotExist:
                # We use the original
                pass

    try:
        _authorize_pageview(request, page, no_unpublished=no_unpublished)
    except PageNotFoundError:
        # Page is not found or not online
        return ''

    #
    # Rendering
    #

    # We don't want to cache the page with the link to the admin page
    # so if the user has edit access we don't use the cache
    if page_cache is not None and not request.user.has_perm('pages.change_page'):
        # Cache
        if 'template' not in page_cache:
            # We already have a fully rendered content so return it.
            return page.content
        else:
            # We only have a compiled template, so we need to render the page
            ctpl = page_cache['template']
    else:
        # No cache

        try:
            pgroups = getattr(request.user, 'pgroups')
        except AttributeError:
            pgroups = PageGroup.objects.filter(
                groups__in=request.user.groups.all()
            )
            request.user.pgroups = pgroups

        full_access = any([ x.full_access for x in pgroups ])

        user_has_perm = False
        if request.user.is_superuser or full_access:
            user_has_perm = True
        else:
            for pgroup in page.groups.all():
                if pgroup in pgroups:
                    user_has_perm = True

        #  # If we don't have any configured PageGroup we assume
        #  # standard permissions apply:
        #  if PageGroup.objects.count() == 0:
        #      user_has_perm = True

        #  if request.user.has_perm('pages.change_page'):
        if user_has_perm and request.user.has_perm('pages.change_page'):
            tpl_string = '{% include "pages/embed-edit.html" %}'
        else:
            tpl_string = ''

        tpl_string += page.content
        ctpl = engines['django'].from_string(tpl_string)

    page.content = mark_safe(ctpl.render({
            'admin_edit': admin_edit_for_site('admin_site', translation_proxy=PageProxy)(page),
        }, request)
    )

    # Cache page (either entire page, or only compiled content template)
    # Note: Inactive pages are never cached
    if page_cache is None and page.is_online() and not request.user.has_perm('pages.change_page'):
        if page.dynamic:
            cache.set( cache_key, {'page': page, 'template': ctpl } )
        else:
            cache.set( cache_key, {'page': page } )

    return page.content


def view_page( request, url ):
    """
    View for rendering pages. The view can either be called through
    the PageFallbackMiddleware or add the following line as the last entry
    in urls.py (a catch all pattern):

    {{{
        ( r'^(?P<url>.*)', iaumemberdb.views.test_view )
    }}}

    The difference between the middleware and the URL matching method, is that
    the with the URL method it wall always be this view that returns a 404
    response, while with the fallback middleware, the middleware will return the
    original 404 response in case no page was found.

    The view has the following features:
    * Authentication::
        * Staff users with pages.can_view_inactive permissions can see all pages
        (inactive as well as login protected)
        * Pages can be require login/authentication
    * Caching::
        * For static pages the entire HTML document is cached.
        * For dynamic pages the compiled template is cached.
    * Dynamic content::
        * By default only MEDIA_URL is available as variable, beside the normal
        template markup.
    * Pages can be embedded cannot be viewed through this view, but should
        use the embed_page view.
    * URL lookup is done through a cached URL index, if possible.
    """
    if not url.startswith('/'):
        url = "/" + url

    is_embed = url.endswith('/embed/') and hasattr(settings, 'EMBED_TEMPLATE')

    if is_embed:
        url = url.replace('embed/','')

    if settings.USE_I18N:
        lang = translation.get_language()
    else:
        lang = None

    # Generate cache key
    if request.user.is_staff and request.user.has_perm('pages.can_view_inactive') and 'preview' in request.GET:
        # We don't cache if user has permissions and in preview mode
        cache_key = None
    else:
        cache_key = '%s_%s' % (CACHE_KEY['pages'], str(url.__hash__()))
        if lang:
            cache_key += '_%s' % lang

        if is_internal(request):
            cache_key += '_internal'
        else:
            cache_key += '_external'

    if cache_key:
        page_cache = cache.get( cache_key )
    else:
        page_cache = None

    if page_cache is not None:
        page = page_cache['page']
    else:
        # Use precompiled index of urls for the site.
        index = cache.get( CACHE_KEY['urlindex'] )
        if index is None:
            index = build_urlindex()

        if url in index:
            page = Page.objects.get(embedded__exact=0, pk=index[url])
        elif settings.USE_I18N and request.path in index:
            # If we use translations let's check if the page exists with a full
            # URL, e.g.: /public/chile/about-eso/
            page = Page.objects.filter(embedded__exact=0, pk=index[request.path]).get()
        else:
            # If the URL doesn't exist let's check if it does exist with
            # a trailing /
            if not url.endswith('/') and url + '/' in index:
                return redirect(request.path + '/')

            raise Http404

        # The current preferred language is different than the page's,
        # If the page was not originally accessed through the "translated"
        # URL then we redirect the user:
        language_path = get_path_for_language(lang, request.path_info)

        if request.path != language_path:
            querystring = get_querystring_from_request(request)

            if querystring:
                # Add query string to redirect path if any
                language_path += '?' + querystring

            return redirect(language_path)

        if settings.USE_I18N and lang != page.lang:
            # Next we check if we have a translation for the page, in which
            # case we use it, othewise we use the original version but set
            # a variable to be used in the template
            try:
                trans = page.translations.get(lang=lang)
                if trans.published and trans.translation_ready:
                    page = trans
                else:
                    request.NO_TRANSLATION = True
            except Page.DoesNotExist:
                # There are not translations in the preferred language, next we
                # check if the source is in the same language family, if not
                # we display a sorry message
                if lang[:2] != page.lang[:2]:
                    request.NO_TRANSLATION = True

    # Page Protection
    # ---------------
    # Authentication and active pages.
    #  - Staff users with 'pages.can_view_inactive' permissions can view pages online
    #    even if they are inactive (this is a preview functionality).
    try:
        _authorize_pageview( request, page )
    except PageNotFoundError:
        raise Http404
    except PageAuthorizationError:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login( request.path )

    # If the page has a redirect_url set we return a HTTP 301 permanent redirection
    if page.redirect_url:
        return HttpResponsePermanentRedirect(page.redirect_url)

    #
    # Rendering
    #
    htmlkey = 'html%s' % '-admin' if request.user.is_superuser else ''
    ctpl = None

    # We don't want to cache the page with the link to the admin page
    # so if the user has edit access we don't use the cache
    if page_cache is not None and not request.user.has_perm('pages.change_page'):
        # Cache
        if htmlkey in page_cache:
            # We already have a fully rendered page so return it.
            return HttpResponse( page_cache[htmlkey] )
        elif 'template' in page_cache:
            # We only have a compiled template, so we need to render the page
            ctpl = page_cache['template']

    if ctpl is None:
        # No cache
        ctpl = engines['django'].from_string( page.content )

    # Render content
    page.title = mark_safe( page.title )
    page.content = mark_safe( ctpl.render( {}, request ) )

    # Render entire page
    template_names = (page.template_name, page.section.template)

    if is_embed:
        template = select_template([settings.EMBED_TEMPLATE])
    else:
        template = select_template([x for x in template_names if x])

    html = template.render({
            'page': page,
            'translations': page.get_translations(),
            'admin_edit': admin_edit_for_site('admin_site', translation_proxy=PageProxy)(page),
        }, request
    )

    # Cache page (either entire page, or only compiled content template)
    # Note: Inactive pages and pages viewed by users with admin access
    # are never cached
    if cache_key:
        if page.is_online() and not request.user.has_perm('pages.change_page'):
            if page.dynamic and page_cache is None:
                cache.set( cache_key, {'page': page, 'template': ctpl } )
            else:
                if not page_cache:
                    page_cache = {'page': page }

                page_cache[htmlkey] = html
                cache.set( cache_key, page_cache )

    return HttpResponse( html )
