# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
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

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
if settings.USE_I18N:
    from django.utils import translation
from django.views.generic import DetailView

from djangoplicity.newsletters.models import Newsletter, NewsletterType


class NewsletterDetailView(DetailView):

    model = Newsletter

    def get_object(self):
        '''
        Returns the newsletter matching the pk if its type matches the slug
        '''
        slug = self.kwargs.get('category_slug')
        pk = self.kwargs.get('pk')
        newsletter_type = get_object_or_404(NewsletterType, slug=slug, archive=True)

        try:
            obj = Newsletter.objects.get(type=newsletter_type, pk=pk)
        except Newsletter.DoesNotExist:
            raise Http404

        if settings.USE_I18N:
            lang = translation.get_language()
            if lang != settings.LANGUAGE_CODE:
                try:
                    obj = obj.translations.get(lang=lang)
                except Newsletter.DoesNotExist:
                    # We don't have a translation, so we just pass and default
                    # to the original
                    pass

        return obj

    def get(self, request, *args, **kwargs):
        '''
        Check that the current user has permissions if the newsletter is
        not yet published
        '''
        self.object = self.get_object()

        if not self.object.published and not (request.user.is_superuser or request.user.is_staff):
            if request.user.is_authenticated():
                raise Http404
            else:
                return redirect_to_login(self.request.path)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        '''
        Adds the NewsletterType to the context
        '''
        slug = self.kwargs.get('category_slug')
        newsletter_type = get_object_or_404(NewsletterType, slug=slug, archive=True)
        context = super(NewsletterDetailView, self).get_context_data(**kwargs)

        nl = self.object
        if settings.USE_I18N and nl.is_translation():
            # We only care about the translation in the embed view
            nl = nl.source

        context.update({
            'newsletter_type': newsletter_type,
            'object': nl,
        })
        # If the archive is restricted to internal access only we return a 404
        # if the client is outside the internal network
        if newsletter_type.internal_archive:
            if not (self.request and "REMOTE_ADDR" in self.request.META and self.request.META["REMOTE_ADDR"] in settings.INTERNAL_IPS):
                raise Http404
        return context


class NewsletterEmbedView(NewsletterDetailView):
    '''
    The Newsletter HTML is stored including the full page, in ordre to
    add custom header etc we display the newsletter content in an iframe,
    hence we split the newsletter content and the wrapper in two views
    '''

    def render_to_response(self, context, **response_kwargs):
        newsletter_data = self.object.render( {}, store=False )

        # We want the links in the Newsletter to open in the iframe's parent
        # so we add a base to the head
        content = newsletter_data['html']
        content = content.replace('<head>', '<head><base target="_blank" />')

        return HttpResponse(content)

    def get_context_data(self, **kwargs):
        '''
        No context needed
        '''
        return {}
