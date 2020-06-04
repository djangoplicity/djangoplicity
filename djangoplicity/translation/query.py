# -*- coding: utf-8 -*-
#
# djangoplicity-translation
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
from django.core.exceptions import FieldError
from django.db.models.query import QuerySet
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django.utils import translation


class TranslationQuerySet( QuerySet ):
    """
    QuerySet that knows how to
    """
    def __init__(self, model=None, query=None, lang=None, **kwargs ):
        #assert lang in [x[0] for x in settings.LANGUAGES], "Language is not defined."
        if lang is None:
            lang = translation.get_language()
            if lang is None:
                lang = settings.LANGUAGE_CODE
        self._lang = lang

        super( TranslationQuerySet, self ).__init__( model, query, **kwargs )

    def _traverse_tree( self, q_object, negate=False ):
        """
        Helper function that traverse a Q tree object,
        replacing filter expression involving the primary key
        and other fields not present on the Translation object
        """

        # List of model fields directly accessible from Translation objects
        direct_fields = self.model.Translation.fields + self.model.Translation.excludes + ['lang', 'source']
        # Let's add the sacred trinity; we don't want to mess with those guys
        direct_fields += ['published', 'release_date', 'embargo_date']

        new_children = []

        # Iterate over children and generate a new list of children
        # - if a child contains a filter expression with the primary key
        #   it's replaced.
        for child in q_object.children:
            # A tree node is a Q object - so traverse it with a recursive call
            if isinstance( child, Q ):
                new_children.append( self._traverse_tree( child, negate) )
            # A leaf node is tuple: (filter expression, value)
            else:
                arg, value = child
                # Split filter expression
                parts = arg.split( LOOKUP_SEP )
                if not parts:
                    raise FieldError("Cannot parse keyword query %r" % arg)

                # Check if we're filter expression involves the primary key
                field = parts.pop(0)

                # If it's a negated expression we bypass the inclusion of source__pk
                if not negate:

                    # If the query concerns the private key we also look in the
                    # source, to match e.g.: 'ann1401' and 'ann1401de'
                    if field == 'pk' or field == self.model._meta.pk.name:
                        new_children.append( Q( **{ arg: value } ) | Q( **{ LOOKUP_SEP.join( ['source', 'pk'] + parts ): value } ) )
                        continue

                    if field not in direct_fields:
                        # The field is not directly stored in the model (i.e.: it's a foreign
                        # key or many to many), so we check if the relation is a "Translation" one

                        field_type = ''
                        # Get FieldType name
                        try:
                            field_type = self.model._meta.get_field(field).get_internal_type()
                        except AttributeError:
                            if hasattr(self.model, field + '_set'):
                                field_type = getattr(self.model, field + '_set').related.field.get_internal_type()

                        if field_type.startswith('Translation'):
                            # Field is translated and not directly accessible so
                            # we access the one from the source instead
                            # Note: this (can) create massive SQL JOINs (at least as of
                            # Django 1.5). Ideally this could be replaced by something
                            # smarter, for example by using directly the source_pk in
                            # the ForeignKey to remove an extra JOIN
                            #  new_children.append( Q( **{ LOOKUP_SEP.join( ['source', field] + parts ): value } ) )
                            new_children.append( Q( **{ arg: value } ) | Q( **{ LOOKUP_SEP.join( ['source', field] + parts ): value } ) )
                            continue

                new_children.append( child )

        q_object.children = new_children
        return q_object

    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        Overrides the behaviour of filter/exclude to only return
        source and translation objects for a specific language.

        It does this by rewriting any filter expression involving
        the primary key.

        Example::

            pk__in=[1,2] AND name='test' AND lang='da'

        is rewritten to::

            (pk__in=[1,2] OR source__in=[1,2]) AND name='test' AND lang='da'

        Hence queries are using the primary keys of the source objects to find
        the object. The translations primary keys are not used.

        It also ensures Django DP API calls (filter, exclude) on Translation objects
        work as expected, using the same rewriting strategy.
        """
        q_object = self._traverse_tree( Q( *args, **kwargs ), negate)
        return super( TranslationQuerySet, self )._filter_or_exclude( negate, q_object )

    def _clone(self, *args, **kwargs):
        """
        Override _clone to preserve language information.
        """
        clone = super( TranslationQuerySet, self )._clone( *args, **kwargs )
        clone._lang = getattr( self, '_lang', None )
        return clone


class TranslationSourceQuerySet( QuerySet ):
    pass
