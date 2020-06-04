# -*- coding: utf-8 -*-
#
# djangoplicity-simplearchives
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
Generic category view
"""

from django.views.generic import ListView
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import Http404
from django.utils.translation import ugettext_lazy as _


class CategoryListView( ListView ):
    category_slug_field = 'slug'
    category_model = None
    category_queryset = None
    model_category_field = 'category'
    category_context_object_name = 'category'

    def get_category( self, queryset=None ):
        """
        Returns the category object the view is displaying.

        By default this requires `self.queryset` and a `category_pk` or `category_slug` argument
        in the URLconf, but subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        if queryset is None:
            queryset = self.get_category_queryset()

        # Next, try looking up by primary key.
        pk = self.kwargs.get( 'category_pk', None )
        slug = self.kwargs.get( 'category_slug', None )
        if pk is not None:
            queryset = queryset.filter( pk=pk )

        # Next, try looking up by slug.
        elif slug is not None:
            slug_field = self.get_category_slug_field()
            queryset = queryset.filter( **{slug_field: slug} )

        # If none of those are defined, it's an error.
        else:
            raise AttributeError( u"Generic category view %s must be called with "
                                 u"either an object category_pk or a category_slug."
                                 % self.__class__.__name__ )

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404( _( u"No %(verbose_name)s found matching the query" ) %
                          {'verbose_name': queryset.model._meta.verbose_name} )

        return obj

    def get_category_slug_field( self ):
        """
        Get the name of a slug field to be used to look up by slug.
        """
        return self.category_slug_field

    def get_model_category_field( self ):
        """
        Get the name of a field to be used to look up by category.
        """
        return self.model_category_field

    def get_category_queryset( self ):
        """
        Get the list of items for this view. This must be an interable, and may
        be a queryset (in which qs-specific behavior will be enabled).
        """
        if self.category_queryset is not None:
            queryset = self.category_queryset
            if hasattr( queryset, '_clone' ):
                queryset = queryset._clone()
        elif self.category_model is not None:
            queryset = self.category_model._default_manager.all()
        else:
            raise ImproperlyConfigured( u"'%s' must define 'category_queryset' or 'category_model'"
                                       % self.__class__.__name__ )
        return queryset

    def get_queryset( self ):
        """
        Get the list of items for this view. This must be an iterable, and may
        be a queryset (in which qs-specific behavior will be enabled).
        """
        self.category = self.get_category()

        queryset = super( CategoryListView, self ).get_queryset()

        model_category_field = self.get_model_category_field()
        queryset = queryset.filter( **{ model_category_field: self.category } )

        return queryset

    def get_context_data( self, **kwargs ):
        context = super( CategoryListView, self ).get_context_data( **kwargs )
        # Add in the category
        if self.category_context_object_name is not None:
            context[self.category_context_object_name] = self.category
        return context

    def get_template_names( self ):
        """
        Returns a list of template names to be used for the request. Must return
        a list. May not be called if render is overridden.
        """
        names = super( CategoryListView, self ).get_template_names()

        if self.category and hasattr(self.object_list, 'model'):
            slug = getattr( self.category, self.get_category_slug_field() )
            if slug:
                opts = self.object_list.model._meta
                names.insert( 0 if self.template_name is None else 1, "%s/%s_%s%s.html" % ( opts.app_label, opts.object_name.lower(), slug, self.template_name_suffix ) )

        return names
