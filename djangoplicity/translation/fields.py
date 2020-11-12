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
Multilingul relationship fields to setup relations from/to multilingual models.

The following fields are available:
  * TranslationForeignKey( RelatedModel, only_sources=True, ... )
  * TranslationManyToManyField( RelatedModel, only_sources=True, ... )
  * TranslationOneToOneField( RelatedModel, only_sources=True, ... )

.. todo: TranslationOneToOneField has not yet been implemented

They should be used for any relationship to/from a multilingual model, to ensure
proper behavior of the forward/reverse relationship managers.

All three fields support the same options as their non-multilingal counterpart,
and one additional option:
  * `only_sources`: Defines if the relation is *to* source instances only or if relations
    to all instances (i.e. source and translation instances) are allowed (default: true, i.e.
    relations are to source instances only).

.. warning:
   These methods must be kept in sync with Django. Unfortunately Django
   does not allow to override which descriptor to use, so the
   `contribute_to_class` and `contribute_to_related_class` had to be copied
   from the original django source and modfied (which basically amounts to
   changing the used descriptor class).
"""
from django.conf import settings
from django.db.models import CharField, ForeignKey, ManyToManyField
from django.db.models.fields.related import \
    create_many_to_many_intermediary_model, lazy_related_operation, RelatedField
from django.forms import fields
from django.utils.encoding import force_text
from django.utils.functional import curry

from djangoplicity.translation.related_descriptors import \
    TranslationForwardManyToOneDescriptor, TranslationManyToManyDescriptor, \
    TranslationReverseManyToOneDescriptor
import django

__all__ = ['TranslationForeignKey', 'TranslationManyToManyField']


class TranslationForeignKey(ForeignKey):
    related_accessor_class = TranslationReverseManyToOneDescriptor
    forward_related_accessor_class = TranslationForwardManyToOneDescriptor

    def __init__(self, *args, **kwargs):
        '''
        Add only_sources field
        '''
        self.only_sources = kwargs.pop('only_sources', True)
        super(TranslationForeignKey, self).__init__(*args, **kwargs)

    def set_cached_value(self, instance, value):
        if django.VERSION >= (2, 2):
            super(TranslationForeignKey, self).set_cached_value(instance, value)
        else:
            setattr(instance, self.get_cache_name(), value)

    def deconstruct(self):
        '''
        Handle only_sources
        '''
        name, path, args, kwargs = super(TranslationForeignKey, self).deconstruct()
        if self.only_sources is not True:
            kwargs['only_sources'] = self.only_sources
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        '''
        Copied from RelatedField.contribute_to_class and ForeignObject.contribute_to_class,
        ForwardManyToOneDescriptor is replaced by TranslationForwardManyToOneDescriptor and
        only_sources passed as argument
        '''
        super(RelatedField, self).contribute_to_class(cls, name, private_only=private_only, **kwargs)  # pylint: disable=E1003

        self.opts = cls._meta

        if not cls._meta.abstract:
            if self.remote_field.related_name:
                related_name = self.remote_field.related_name
            else:
                related_name = self.opts.default_related_name
            if related_name:
                related_name = force_text(related_name) % {
                    'class': cls.__name__.lower(),
                    'model_name': cls._meta.model_name.lower(),
                    'app_label': cls._meta.app_label.lower()
                }
                self.remote_field.related_name = related_name

            if self.remote_field.related_query_name:
                related_query_name = force_text(self.remote_field.related_query_name) % {
                    'class': cls.__name__.lower(),
                    'app_label': cls._meta.app_label.lower(),
                }
                self.remote_field.related_query_name = related_query_name

            def resolve_related_class(model, related, field):
                field.remote_field.model = related
                field.do_related_class(related, model)
            lazy_related_operation(resolve_related_class, cls, self.remote_field.model, field=self)

        setattr(cls, self.name, self.forward_related_accessor_class(self, only_sources=self.only_sources))  # Change

    def contribute_to_related_class(self, cls, related):
        '''
        Copied from ForeignObject.contribute_to_related_class and ForeignKey.contribute_to_related_class,
        only_sources is passed to self.related_accessor_class, itself set to TranslationReverseManyToOneDescriptor
        as a class attribute
        '''
        # Internal FK's - i.e., those with a related name ending with '+' -
        # and swapped models don't get a related descriptor.
        if not self.remote_field.is_hidden() and not related.related_model._meta.swapped:
            setattr(cls._meta.concrete_model, related.get_accessor_name(), self.related_accessor_class(related, only_sources=self.only_sources))  # Change
            # While 'limit_choices_to' might be a callable, simply pass
            # it along for later - this is too early because it's still
            # model load time.
            if self.remote_field.limit_choices_to:
                cls._meta.related_fkey_lookups.append(self.remote_field.limit_choices_to)

        if self.remote_field.field_name is None:
            self.remote_field.field_name = cls._meta.pk.name



class TranslationManyToManyField(ManyToManyField):
    '''
    ManyToMany field for setting up many-to-many relations to/from
    multilingual models.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Add only_sources field
        '''
        self.only_sources = kwargs.pop('only_sources', True)
        super(TranslationManyToManyField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        '''
        Handle only_sources
        '''
        name, path, args, kwargs = super(TranslationManyToManyField, self).deconstruct()
        if self.only_sources is not True:
            kwargs['only_sources'] = self.only_sources
        return name, path, args, kwargs


    def contribute_to_class(self, cls, name, **kwargs):
        '''
        Copied from ManyToManyField.contribute_to_class, ManyToManyDescriptor is replaced by
        TranslationManyToManyDescriptor and only_sources passed as argument
        '''
        # To support multiple relations to self, it's useful to have a non-None
        # related name on symmetrical relations for internal reasons. The
        # concept doesn't make a lot of sense externally ("you want me to
        # specify *what* on my non-reversible relation?!"), so we set it up
        # automatically. The funky name reduces the chance of an accidental
        # clash.
        if self.remote_field.symmetrical and (
                self.remote_field.model == "self" or self.remote_field.model == cls._meta.object_name):
            self.remote_field.related_name = "%s_rel_+" % name
        elif self.remote_field.is_hidden():
            # If the backwards relation is disabled, replace the original
            # related_name with one generated from the m2m field name. Django
            # still uses backwards relations internally and we need to avoid
            # clashes between multiple m2m fields with related_name == '+'.
            self.remote_field.related_name = "_%s_%s_+" % (cls.__name__.lower(), name)

        super(ManyToManyField, self).contribute_to_class(cls, name, **kwargs)  # pylint: disable=E1003

        # The intermediate m2m model is not auto created if:
        #  1) There is a manually specified intermediate, or
        #  2) The class owning the m2m field is abstract.
        #  3) The class owning the m2m field has been swapped out.
        if not cls._meta.abstract:
            if self.remote_field.through:
                def resolve_through_model(_, model, field):
                    field.remote_field.through = model
                lazy_related_operation(resolve_through_model, cls, self.remote_field.through, field=self)
            elif not cls._meta.swapped:
                self.remote_field.through = create_many_to_many_intermediary_model(self, cls)

        # Add the descriptor for the m2m relation.
        setattr(cls, self.name, TranslationManyToManyDescriptor(self.remote_field, reverse=False, only_sources=self.only_sources))  # Change

        # Set up the accessor for the m2m table name for the relation.
        self.m2m_db_table = curry(self._get_m2m_db_table, cls._meta)

    def contribute_to_related_class(self, cls, related):
        # Internal M2Ms (i.e., those with a related name ending with '+')
        # and swapped models don't get a related descriptor.
        if not self.remote_field.is_hidden() and not related.related_model._meta.swapped:
            setattr(cls, related.get_accessor_name(), TranslationManyToManyDescriptor(self.remote_field, reverse=True, only_sources=self.only_sources))  # Change

        # Set up the accessors for the column names on the m2m table.
        self.m2m_column_name = curry(self._get_m2m_attr, related, 'column')
        self.m2m_reverse_name = curry(self._get_m2m_reverse_attr, related, 'column')

        self.m2m_field_name = curry(self._get_m2m_attr, related, 'name')
        self.m2m_reverse_field_name = curry(self._get_m2m_reverse_attr, related, 'name')

        get_m2m_rel = curry(self._get_m2m_attr, related, 'remote_field')
        self.m2m_target_field_name = lambda: get_m2m_rel().field_name
        get_m2m_reverse_rel = curry(self._get_m2m_reverse_attr, related, 'remote_field')
        self.m2m_reverse_target_field_name = lambda: get_m2m_reverse_rel().field_name

# Thu  9 Aug 17:37:45 CEST 2018 - Mathias André
# If this hasn't caused problem in a few months
#
#   def _get_m2m_reverse_attr(self, related, attr):
#       '''
#       This method is copied from ManyToManyField._get_m2m_reverse_attr
#       related.model is changed to related.to
#       This is related to https://github.com/swisscom/cleanerversion/issues/56
#       Basically related.model is a cached property which returns related.to,
#       however during migrations Django deepcopies models, and returns a string
#       with the name of the class instead of the class itself, so we override
#       the method and call it if the parent method fails
#       TODO: check if this is still necessary since Django 1.9
#       '''
#       try:
#           return super(TranslationManyToManyField, self)._get_m2m_reverse_attr(related, attr)
#       except AttributeError:
#           cache_attr = '_m2m_reverse_%s_cache' % attr
#           if hasattr(self, cache_attr):
#               return getattr(self, cache_attr)
#           found = False
#           if self.remote_field.through_fields is not None:
#               link_field_name = self.remote_field.through_fields[1]
#           else:
#               link_field_name = None
#           for f in self.remote_field.through._meta.fields:
#               if f.is_relation and f.remote_field.model == related.to:  # Change
#                   if link_field_name is None and related.related_model == related.to:  # Change
#                       # If this is an m2m-intermediate to self,
#                       # the first foreign key you find will be
#                       # the source column. Keep searching for
#                       # the second foreign key.
#                       if found:
#                           setattr(self, cache_attr, getattr(f, attr))
#                           break
#                       else:
#                           found = True
#                   elif link_field_name is None or link_field_name == f.name:
#                       setattr(self, cache_attr, getattr(f, attr))
#                       break
#           return getattr(self, cache_attr)


class LanguageField(CharField):
    '''
    Custom field to avoid having choices caught by makemigrations
    '''
    def formfield(self, **kwargs):
        return fields.ChoiceField(choices=settings.LANGUAGES)
