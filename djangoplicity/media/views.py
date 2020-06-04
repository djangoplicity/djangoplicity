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

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template import loader

from djangoplicity.archives.utils import FormatTokenGenerator
from djangoplicity.archives.views import GenericDetailView
from djangoplicity.media.models import Image, ImageProxy
from djangoplicity.archives.contrib.security.views import serve_file


class ZoomableDetailView( GenericDetailView ):
    """
    View class for generating a detail page showing a
    zoomify image.
    """
    def vary_on( self, request, model, obj, state, admin_rights, **kwargs ):
        return ['zoomable']

    def render( self, request, model, obj, state, admin_rights, **kwargs ):
        template_loader = loader
        template_names = ['archives/detail_zoomable.html']

        t = template_loader.select_template( template_names )

        # Request context setup
        context = {
            'object': obj,
        }

        return t.render( context, request )


class ImageComparisonFullscreenDetailView( GenericDetailView ):
    """
    View class for generating a detail page showing a fullscreen
    image comparison.
    """
    def vary_on( self, request, model, obj, state, admin_rights, **kwargs ):
        return ['fullscreen']

    def render( self, request, model, obj, state, admin_rights, **kwargs ):
        template_loader = loader
        template_names = ['archives/detail_fullscreen.html']

        t = template_loader.select_template( template_names )

        # Request context setup
        context = {
            'object': obj,
        }

        return t.render( context, request )


def image_passthrough( request, token='', format='', id='', ext='', **kwargs ):
    """
    Serve a static image if token is correct.
    This is only needed when links to the image
    is not already public.
    """
    try:
        if FormatTokenGenerator.check_token( token, format, id ):
            try:
                im = Image.objects.get(pk=id)
            except Image.DoesNotExist:
                # Let's check if we're trying to access an image translation
                im = get_object_or_404( ImageProxy, pk=id )
                im = im.source

            # Get resource and its url
            res = getattr( im, "resource_%s" % format )
            if res:
                url = res.url

                if url.startswith(settings.MEDIA_URL):
                    url = url.replace(settings.MEDIA_URL, '')

                if url.startswith('http') or url.startswith('//'):
                    return HttpResponseRedirect(url)
                else:
                    return serve_file(request, url)
    except Exception:
        pass

    raise Http404
