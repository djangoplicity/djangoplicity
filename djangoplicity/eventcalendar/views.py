# -*- coding: utf-8 -*-
#
# djangoplicity-eventcalendar
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

from djangoplicity.simplearchives.views import CategoryListView
from djangoplicity.eventcalendar.models import Event, EventType
from djangoplicity.archives.browsers import select_template
from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
import os


class EventTypeListView( CategoryListView ):
    model = Event
    model_category_field = 'type'
    queryset = Event.objects.filter( published=True ).order_by( '-start_date' )
    category_model = EventType

    def get_category( self, queryset=None ):
        '''
        We override CategoryListView's get_category() as it doesn't support
        translated objects
        '''
        try:
            queryset = EventType.objects.fallback(translation.get_language())
            slug = self.kwargs.get( 'category_slug', None )
            slug_field = self.get_category_slug_field()
            queryset = queryset.filter( **{slug_field: slug} )
            return queryset.get()
        except EventType.DoesNotExist:
            raise Http404( _( u"No %(verbose_name)s found matching the query" ) %
                            {'verbose_name': queryset.model._meta.verbose_name} )

    def get_queryset( self, ongoing=False ):
        # We use the parent get_category() as we need the source
        # category and not the translations
        category = super(EventTypeListView, self).get_category()

        queryset = super( CategoryListView, self ).get_queryset()

        model_category_field = self.get_model_category_field()
        queryset = queryset.filter( **{ model_category_field: category } )

        # If the current language is different than the sytem one filters
        # the events where the country matches the current language
        # Note: for Special Events this is only the case for Chile
        lang = translation.get_language()
        if category.slug == 'press-evt' and lang != 'en':
            # For press events we show local events and English events
            # (i.e.: the default queryset)
            pass
        elif not (category.slug == 'special-evt' and lang != 'es-cl'):
            if lang != settings.LANGUAGE_CODE:
                country = lang
                # Extract the country from the language code if necessary
                # e.g.: at for de-at
                if '-' in country:
                    country = country.split('-')[1]
                queryset = queryset.filter(Q(country__isocode=country) | Q(country__isnull=True))

        # Set the translated category
        self.category = self.get_category()

        if ongoing:
            return queryset.exclude(ongoing=False)
        else:
            return queryset.exclude(ongoing=True)

    def get_context_data( self, **kwargs ):
        context = super( EventTypeListView, self ).get_context_data( **kwargs )
        context['ongoing_object_list'] = self.get_queryset(ongoing=True)
        context['archive_title'] = self.category.name

        # Events are not a subclass of TranslationModel, so we can't
        # just use archive.browsers.lang_template. Instead we have a simple
        # version to generate language specific template names we will extend from

        names = self.get_template_names()
        lang = translation.get_language()
        lang_template_names = []

        for tpl in names:
            ( base, ext ) = os.path.splitext( tpl )
            lang_template_names.append( "%s_base.%s%s" % ( base, lang, ext ) )
        for tpl in names:
            ( base, ext ) = os.path.splitext( tpl )
            lang_template_names.append( "%s_base%s" % ( base, ext ) )

        base_template = select_template(lang_template_names + names)

        context['base_template'] = base_template

        return context

category_view = EventTypeListView.as_view()
