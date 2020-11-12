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

from builtins import object
from django.db import router
from django.db.models.fields.related_descriptors import \
    ForwardManyToOneDescriptor, ReverseManyToOneDescriptor, \
    ManyToManyDescriptor, create_reverse_many_to_one_manager, \
    create_forward_many_to_many_manager
from django.utils.functional import cached_property
import django


class TranslationDescriptor(object):
    """
    Common descriptor for related objects descriptors.

    The descriptors are responsible for creating the related object
    managers - i.e. if you access item.image_set, then the descriptors
    __get__ method will be invoked. The __get__ method will return a manager
    capable of retrieving related objects.

    See more on Python descriptors here:
    http://docs.python.org/reference/datamodel.html#implementing-descriptors
    """
    def is_multilingual_model(self, model):
        """ Check if a model is a multilingual model. """
        return True if getattr(model, 'is_translation', False) else False

    def is_multilingual_object(self, object):
        """ Check if a object is an instance of a multilingual model. """
        return self.is_multilingual_model(object.__class__)

    def get_manager_base_class(self, related_model=None):
        """
        Determine which of the model's model managers to use
        to retrieve objects.

        If the relation is only involving sources, then use the default
        manager (which only returns source objects), otherwise use the
        plain _base_manager which returns both source or translation objects.
        """
        rel_model = related_model if related_model is not None else self.rel.related_model
        result = _get_manager_base_class(rel_model, only_sources=self.only_sources)
        return result

    def get_instance_pk(self, instance):
        """
        Determine which primary key to query for related objects.

        In most cases this is just the primary key of the instance. However, there
        exists one special case (documented in the __init__.py file): When the instance
        is a translation object you shouldn't use the translation object's primary key
        but its source primary key to query for related objects in a multilingual
        model when only connection to source objects are allowed.
        """
        if self.only_sources and (self.is_multilingual_object(instance) and instance.is_translation()):
            return instance.source.pk
        else:
            return instance.pk

    def get_instance(self, instance):
        """
        Determine if translation or source should be used to query for related objects.

        See get_instance_pk for more details.
        """
        if self.only_sources and (self.is_multilingual_object(instance) and instance.is_translation()):
            return instance.source
        else:
            return instance


class TranslationForwardManyToOneDescriptor(ForwardManyToOneDescriptor, TranslationDescriptor):
    def __init__(self, field_with_rel, only_sources=True):
        '''
        Set only_sourced
        '''
        self.only_sources = only_sources
        super(TranslationForwardManyToOneDescriptor, self).__init__(field_with_rel)

    def __set__(self, instance, value):
        # See: https://github.com/djangoplicity/djangoplicity/wiki/Django-2-Upgrades#translationforwardmanytoonedescriptor-object-has-no-attribute-cache_name
        if django.VERSION >= (2, 0):
            '''
            Copied and updated from ForwardManyToOneDescriptor 2.2 (two ADDED sections)
            '''
            # An object must be an instance of the related class.
            if value is not None and not isinstance(value, self.field.remote_field.model._meta.concrete_model):
                raise ValueError(
                    'Cannot assign "%r": "%s.%s" must be a "%s" instance.' % (
                        value,
                        instance._meta.object_name,
                        self.field.name,
                        self.field.remote_field.model._meta.object_name,
                    )
                )
            elif value is not None:
                if instance._state.db is None:
                    instance._state.db = router.db_for_write(instance.__class__, instance=value)
                if value._state.db is None:
                    value._state.db = router.db_for_write(value.__class__, instance=instance)
                if not router.allow_relation(value, instance):
                    raise ValueError('Cannot assign "%r": the current database router prevents this relation.' % value)
            
            remote_field = self.field.remote_field
            # If we're setting the value of a OneToOneField to None, we need to clear
            # out the cache on any old related object. Otherwise, deleting the
            # previously-related object will also cause this object to be deleted,
            # which is wrong.
            if value is None:
                # Look up the previously-related object, which may still be available
                # since we've not yet cleared out the related field.
                # Use the cache directly, instead of the accessor; if we haven't
                # populated the cache, then we don't care - we're only accessing
                # the object to invalidate the accessor cache, so there's no
                # need to populate the cache just to expire it again.
                related = self.field.get_cached_value(instance, default=None)

                # If we've got an old related object, we need to clear out its
                # cache. This cache also might not exist if the related object
                # hasn't been accessed yet.
                if related is not None:
                    remote_field.set_cached_value(related, None)

                for lh_field, rh_field in self.field.related_fields:
                    setattr(instance, lh_field.attname, None)

            # Set the values of the related field.
            else:
                for lh_field, rh_field in self.field.related_fields:
                    setattr(instance, lh_field.attname, getattr(value, rh_field.attname))

            # ADDED: If value is translation object, then use the source
            if self.only_sources and self.is_multilingual_object(value) and value.is_translation():
                value = value.source
            # ADDED (end)

            # Set the related instance cache used by __get__ to avoid an SQL query
            # when accessing the attribute we just set.
            self.field.set_cached_value(instance, value)

            # If this is a one-to-one relation, set the reverse accessor cache on
            # the related object to the current instance to avoid an extra SQL
            # query if it's accessed later on.
            if value is not None and not remote_field.multiple:
                remote_field.set_cached_value(value, instance)
        else:
            '''
            Copied and updated from ForwardManyToOneDescriptor 1.11 (two ADDED sections)
            '''
            # An object must be an instance of the related class.
            if value is not None and not isinstance(value, self.field.remote_field.model._meta.concrete_model):
                raise ValueError(
                    'Cannot assign "%r": "%s.%s" must be a "%s" instance.' % (
                        value,
                        instance._meta.object_name,
                        self.field.name,
                        self.field.remote_field.model._meta.object_name,
                    )
                )
            elif value is not None:
                if instance._state.db is None:
                    instance._state.db = router.db_for_write(instance.__class__, instance=value)
                elif value._state.db is None:
                    value._state.db = router.db_for_write(value.__class__, instance=instance)
                elif value._state.db is not None and instance._state.db is not None:
                    if not router.allow_relation(value, instance):
                        raise ValueError('Cannot assign "%r": the current database router prevents this relation.' % value)

            # If we're setting the value of a OneToOneField to None, we need to clear
            # out the cache on any old related object. Otherwise, deleting the
            # previously-related object will also cause this object to be deleted,
            # which is wrong.
            if value is None:
                # Look up the previously-related object, which may still be available
                # since we've not yet cleared out the related field.
                # Use the cache directly, instead of the accessor; if we haven't
                # populated the cache, then we don't care - we're only accessing
                # the object to invalidate the accessor cache, so there's no
                # need to populate the cache just to expire it again.
                related = getattr(instance, self.cache_name, None)

                # If we've got an old related object, we need to clear out its
                # cache. This cache also might not exist if the related object
                # hasn't been accessed yet.
                if related is not None:
                    setattr(related, self.field.remote_field.get_cache_name(), None)

                for lh_field, rh_field in self.field.related_fields:
                    setattr(instance, lh_field.attname, None)

            # Set the values of the related field.
            else:
                for lh_field, rh_field in self.field.related_fields:
                    setattr(instance, lh_field.attname, getattr(value, rh_field.attname))

            # ADDED: If value is translation object, then use the source
            if self.only_sources and self.is_multilingual_object(value) and value.is_translation():
                value = value.source
            # ADDED (end)

            # Set the related instance cache used by __get__ to avoid an SQL query
            # when accessing the attribute we just set.
            setattr(instance, self.cache_name, value)

            # If this is a one-to-one relation, set the reverse accessor cache on
            # the related object to the current instance to avoid an extra SQL
            # query if it's accessed later on.
            if value is not None and not self.field.remote_field.multiple:
                setattr(value, self.field.remote_field.get_cache_name(), instance)

        # ADDED
        # If we're not dealing with the source field in a TranslationModel
        # we need to consider if we're working with a translation instance of
        # source instance. If a translation instance, then we must set the
        # value on the source instance as well.
        if not (self.field.name == 'source' and self.is_multilingual_model(self.field.remote_field.related_model)):
            if self.only_sources and self.is_multilingual_object(instance) and instance.is_translation():
                changed = False
                for lh_field, rh_field in self.field.related_fields:
                    val = getattr(instance, lh_field.attname)
                    if getattr(instance.source, lh_field.attname) != val:
                        setattr(instance.source, lh_field.attname, val)
                        changed = True
                try:
                    # FIXME: Added the try/except as workaround for ESO announcement,
                    # should be fixed properly
                    if getattr(instance.source, self.field.get_cache_name()) != value:
                        setattr(instance.source, self.field.get_cache_name(), value)
                        changed = True
                except AttributeError:
                    pass

                if changed:
                    instance.source.save()
        # ADDED (end)


class TranslationReverseManyToOneDescriptor(ReverseManyToOneDescriptor, TranslationDescriptor):
    def __init__(self, rel, only_sources=True):
        '''
        Set only_sources, to_multilingual and from_multilingual
        '''
        self.only_sources = only_sources
        self.to_multilingual = self.is_multilingual_model(rel.model)
        self.from_multilingual = self.is_multilingual_model(rel.related_model)
        super(TranslationReverseManyToOneDescriptor, self).__init__(rel)

    @cached_property
    def related_manager_cls(self):
        '''
        Copied from ReverseManyToOneDescriptor.related_manager_cls,
        Replace self.rel.related_model._default_manager.__class__ by self.get_manager_base_class()
        '''
        return create_reverse_many_to_one_manager(
            self.get_manager_base_class(),  # CHANGE
            self.rel,
        )

    def __get__(self, instance, instance_type=None):
        """
        Get the related objects through the reverse relation.

        With the example above, when getting ``parent.children``:

        - ``self`` is the descriptor managing the ``children`` attribute
        - ``instance`` is the ``parent`` instance
        - ``instance_type`` in the ``Parent`` class (we don't need it)

        Note this closely follow the description given in package documentation
        under 'Relations and Multilingual Models' for one-to-many relations.
        """
        if instance is None:
            return self

        # ADDED/UPDATED

        # Create manager
        manager = self.related_manager_cls(instance)  # pylint: disable=too-many-function-args

        instance_or_source = self.get_instance(instance)

        # Take care of special case (see documentation in __init__ for precise documentation)
        if instance_or_source != instance:
            for key, value in list(manager.core_filters.items()):
                if value is instance:
                    manager.core_filters[key] = instance_or_source

            # Alter remove function to use the translation source instead of the translation
            if getattr(manager, 'remove', None):
                manager.remove = wrap_remove(instance.source, self.rel.field)

        return manager
        # ADDED/UPDATED end


class TranslationManyToManyDescriptor(ManyToManyDescriptor, TranslationDescriptor):
    def __init__(self, rel, reverse=False, only_sources=True):
        '''
        Set only_sources, to_multilingual, from_multilingual
        '''
        self.only_sources = only_sources
        try:
            self.to_multilingual = self.is_multilingual_model(rel.rel.model)
            self.from_multilingual = self.is_multilingual_model(rel.rel.related_model)
        except AttributeError:
            # When running migration in production for some reason rel.related is not set.
            self.to_multilingual = self.is_multilingual_model(rel.remote_field)
            self.from_multilingual = self.is_multilingual_model(rel.model)
        super(TranslationManyToManyDescriptor, self).__init__(rel, reverse)

    @cached_property
    def related_manager_cls(self):
        '''
        Copied from ManyToManyDescriptor.related_manager_cls,
        Replace model._default_manager.__class__ by self.get_manager_base_class(related_model=self.field.remote_field.to)
        '''
        return create_forward_many_to_many_manager(
            self.get_manager_base_class(related_model=self.field.remote_field.to),  # Updated
            self.rel,
            reverse=self.reverse,
        )

    def __get__(self, instance, instance_type=None):
        '''
        Copied from ReverseManyToOneDescriptor.__get__ and updated
        '''
        if instance is None:
            return self

        # ADDED: Choose whether to use translation or source object
        instance = self.get_instance(instance)
        # ADDED (end)

        # UPDATED:
        manager = self.related_manager_cls(instance)  # pylint: disable=too-many-function-args

        # ADDED
        manager = wrap_manager(manager, 'add', self.get_instance)
        manager = wrap_manager(manager, 'remove', self.get_instance)
        # ADDED (end)

        return manager


def _get_manager_base_class(related_model, only_sources=True):
    """
    Determine which of the model's model managers to use
    to retrieve objects.

    If the relation is only involving sources, then use the default
    manager (which only returns source objects), otherwise use the
    plain _base_manager which returns both source or translation objects.
    """
    if only_sources:
        return related_model._default_manager.__class__
    else:
        return related_model._base_manager.__class__


def wrap_manager(manager, funcname, get_instance):
    """
    Wrap ManyRelatedManager functions to be able to deal with
    translation objects in add/remove
    """
    func = getattr(manager, funcname, None)

    if func:
        def wrapper(*objs):
            if objs:
                objs = [ get_instance(obj) for obj in objs]
            return func(*objs)
        wrapper.alters_data = True

        setattr(manager, funcname, wrapper)
    return manager


def wrap_remove(instance, rel_field):
    """
    Wrap remove function for RelatedManager
    """
    def remove(*objs):
        val = getattr(instance, rel_field.rel.get_related_field().attname)
        for obj in objs:
            # Is obj actually part of this descriptor set?
            if getattr(obj, rel_field.attname) == val:
                setattr(obj, rel_field.name, None)
                obj.save()
            else:
                raise rel_field.rel.model.DoesNotExist("%r is not related to %r." % (obj, instance))

    remove.alters_data = True
    return remove
