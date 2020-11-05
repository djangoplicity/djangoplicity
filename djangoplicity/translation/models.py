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
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERW lISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

from builtins import filter
from builtins import str
import inspect
import re
from datetime import datetime

import django
from django.conf import settings
from django.core.exceptions import (
    ImproperlyConfigured, ObjectDoesNotExist, ValidationError
)
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse as django_reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.utils.translation import ugettext_lazy as _

from djangoplicity.translation.consts import MAIN_LANGUAGES_LIST, COUNTRIES_LIST, \
    LANGUAGE_CODES
from djangoplicity.translation.fields import LanguageField, \
    TranslationForeignKey
from djangoplicity.translation.manager import TranslationSourceManager, \
    TranslationOnlyManager

LANGUAGE_PREFIX = getattr( settings, 'LANGUAGE_PREFIX', {} )
DEFAULT_PREFIX = getattr( settings, 'DEFAULT_PREFIX', "/" )

LANG_SLUG_RE = re.compile( r"^[-\w]+-(%s)$" % "|".join(LANGUAGE_CODES) )


UPDATED_FOR = (2, 2)
if django.VERSION[:2] > UPDATED_FOR:
    raise ImproperlyConfigured('''
The current Django version is different than the one djangoplicity.translation
support: {}.
Make sure that fields.py and related_descriptors.py are updated based on the
code of Django {}, run py.test and update the value of the UPDATED_FOR constant
'''.format(UPDATED_FOR, django.__version__))


def get_language_from_path( path ):
    """
    Determine language based on a URL path prefix. Next rewrite the
    request path to the default language.

    Returns a tuple ( lang, prefix, rewritten path )
    """
    for prefix in list(LANGUAGE_PREFIX.keys()):
        if path.startswith( prefix ):
            return ( LANGUAGE_PREFIX[prefix], prefix, path.replace( prefix, DEFAULT_PREFIX ) )

    return ( settings.LANGUAGE_CODE, DEFAULT_PREFIX, path )


def get_path_for_language( language, path ):
    """
    Rewrite a URL path to a specific language.
    """
    for p, l in LANGUAGE_PREFIX.items():
        if l == language:
            return path.replace( DEFAULT_PREFIX, p, 1 )
    return path


def get_querystring_from_request( request ):
    """
    Return a query string from request.GET while removing
    any ?lang parameter
    """
    query = request.GET.copy()
    if 'lang' in query:
        del query['lang']

    return query.urlencode()


def translation_reverse(viewname, urlconf=None, args=None, kwargs=None, current_app=None, lang=None ):
    """
    Replacement for django's reverse that determines the
    correct URL for a given URL.
    """
    path = django_reverse( viewname, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app )
    if settings.USE_I18N:
        return get_path_for_language( settings.LANGUAGE_CODE if not lang else lang, path )
    else:
        return path


def _get_defaut_lang():
    return settings.LANGUAGE_CODE


class TranslationModel( models.Model ):
    """
    Base class for models that needs multilingual capabilities. It adds two
    fields needed internally, a model manager to properly work with
    the data in the model and a custom save method.

    Note, you must ensure that the save method is called even in cases
    where your model overrides the save method or inherit a save method
    from another base class. The save method will be default call its
    base class save method, but this can be prevented as well in such cases.

    The base class also requires you to specify which fields in your model
    are to be translated, which are to be inherited and which are not to be
    translated nor inherited.

    Example::

    class SomeModel( SomeMoreImportantModel, TranslationModel ):
        ...
        title = ...
        template = ...
        release_date = ...
        ...

        class Translation:
            fields = ['title',]
            excludes = ['template',]

    Above example specifies that title is to be translated, template not, and
    that release_date is inherited from the source.
    """

    #
    # Fields
    #
    lang = LanguageField( verbose_name=_( 'Language' ), max_length=7, default=_get_defaut_lang, db_index=True )
    source = TranslationForeignKey( 'self', verbose_name=_('Translation source'), related_name='translations', null=True, blank=True, only_sources=False, limit_choices_to={ 'source__isnull': True }, on_delete=models.CASCADE )
    translation_ready = models.BooleanField(default=False, help_text=_('When you check this box and save this translation, an automatic notification email will be sent.'))

    #
    # Manager
    #

    # Object manager to all source objects
    #
    # Note, the default manager *must* be a TranslationSourceManager
    # or a subclass thereof which limits choices to *only* source
    # objects. The reason for this is that forward/reverse relationship
    # managers uses the default manager as base class - thus this ensures
    # that you can only make relations to source objects, which is normally
    # what you want (i.e. the ForeignKey/ManyToManyField is an inherited
    # relation).
    objects = TranslationSourceManager()

    translation_objects = TranslationOnlyManager()

    #
    # Methods
    #
    def save( self, propagate=True, **kwargs ):
        """
        Save method that ensures the translations are in sync with their source.

        Note, if `propagate=False` the super class' save method is not
        called. It just does the update of the translations. This is useful
        if you Model class is inheriting from several classes and you want to
        call this save method, but don't want it to propagate.

        Note, if you source object has not been saved, it will automatically
        be saved first, since all translations *must* have a source.
        """
        # Language must be set - using default language if
        # nothing has been set.
        if not self.lang:
            self.lang = settings.LANGUAGE_CODE

        # Propagate inherited properties and foreign keys
        # from source to translations.
        source = self.source

        if settings.USE_I18N:
            if source:
                # Save source if it hasn't already been saved.
                if not source.pk:
                    source.save()
                    self.source = source

                # Translation object
                self._update_from_source()
            else:
                # Source
                self._update_translations()

        if propagate:
            super( TranslationModel, self ).save( **kwargs )

        # Source objects get the cache cleared in the post_save, but
        # for translations we do it here:
        if source and hasattr(self, 'clear_cache'):
            self.clear_cache()

    def _excludes( self, exclude=None ):
        """
        Return a list of all fields local to the model that is
        not to be inherited from the source object.
        """
        if exclude is None:
            exclude = []
        return ['source', 'lang', 'translation_ready', str(self._meta.pk.name) ] + self.Translation.fields + self.Translation.excludes + exclude

    def _update_translations( self ):
        """
        Update inherited properties and foreign keys in translations
        using the source. The update is done in one query and it
        doesn't hit the save method of the translations.
        """
        # Only sources are allowed to call this method.
        # and, we must be updating the source, not adding it.
        try:
            if not self.source and self.pk:  # TODO: Tricky - actually self.pk might not be none for a new object
                # Get all fields to exclude and setup list of values to update.
                values = {}
                all_excludes = self._excludes()

                # Build list inherited properties and foreign keys to save.
                for field in self._meta.local_fields:
                    if field.name not in all_excludes:
                        try:
                            values[field.name] = getattr( self, field.name )
                        except ObjectDoesNotExist:
                            pass

                # Update all translations if there is anything to update.
                if values:
                    self.translations.all().update( **values )
        except ObjectDoesNotExist:
            pass

    def _update_from_source( self ):
        """
        Copy all inherited properties from the source
        ( old data will be overwritten ).
        """
        if self.source:
            # Get all fields to excludes.
            all_excludes = self._excludes()

            # Get value from source.
            for field in self._meta.fields:
                if field.name not in all_excludes:
                    setattr( self, field.name, getattr( self.source, field.name ) )

    def is_translation(self):
        """
        Determine if this instance is a translation or source object.
        """
        return self.source_id is not None

    def is_source(self):
        """
        Determine if this instance is a translation or source object.
        """
        return self.source_id is None

    def get_source(self):
        """
        Returns the source object, regardless of whether this instance is a translation or a source object.
        """
        return self if self.is_source() else self.source

    def validate_unique( self, exclude=None ):
        """
        Validate that translation language is *not* identical to source language,
        and that the source id is not matching the a language id pattern (<id>-<code>).
        """
        # Validate if translation language equals source language
        if self.is_translation() and self.source.lang == self.lang:
            raise ValidationError({ 'lang': ["Translation language must not be identical to translation source language."] } )

        # Validate source id prefix matches the language
        if self.is_source() and self.pk:
            try:
                m = LANG_SLUG_RE.match( self.pk )
                if m and self.lang != m.group( 1 ):
                    raise ValidationError("Language doesn't match ID prefix '-%s'." % m.group( 1 ))
            except TypeError:
                pass  # In case of non char id's, just ignore this error.

        super( TranslationModel, self ).validate_unique( exclude=exclude )

    def get_missing_translations( self, *args, **kwargs ):
        """
        Get a list of missing languages
        """
        data = self.get_translations( *args, **kwargs )

        def missing_filter( x ):
            try:
                if (hasattr(settings, 'LANGUAGE_DISABLE_TRANSLATIONS') and x[0] in settings.LANGUAGE_DISABLE_TRANSLATIONS) or x[0] == settings.LANGUAGE_CODE:
                    return False
                return not data['translations'][x[0]].translation_ready
            except KeyError:
                return True
        return list(filter( missing_filter, settings.LANGUAGES ))

    def get_translations( self, filter_kwargs=None, include_self=False ):
        """
        Get a dictionary of translations organised by:

        1) Countries: List of countries - each element in the list represents a country, and
            is a list of languages in that country (i.e. its a lists of lists of dictionaries)::

                [ <country>, ... ] where <country> is a list like [ <language >, ... ] where
                language is a dictionary like with the following keys: object, country, name, lang

        2) Main languages:
        """
        if filter_kwargs is None:
            filter_kwargs = { 'published': True, 'translation_ready': True }

        data = {
            'languages': [],
            'countries': [],
            'translations': {},
        }

        def _ctx_for_translation( t, lang, ctry, name, code ):
            return {
                'object': t,
                'country': ctry,
                'name': name,
                'lang': lang,
                'full_code': code,
            }

        # Retrieve all translations for this object (including the source language)
        if self.is_translation():
            translations = list( self.source.translations.filter( **filter_kwargs ) ) + [self.source]
        else:
            translations = list( self.translations.filter( **filter_kwargs ) ) + [self]

        # Make a search dictionary (include source language, and exclude it's own language).
        searchmap = dict([(t.lang, t) for t in translations if include_self or t.lang != self.lang])
        data['translations'] = searchmap

        # Make list of main languages
        for lang, ctry, name, code in MAIN_LANGUAGES_LIST:
            if code in searchmap:
                data['languages'].append( _ctx_for_translation( searchmap[code], lang, ctry, name, code ) )

        # Make list of countries
        for ctry, langs in COUNTRIES_LIST:
            tmp = []
            for lang, name, code in langs:
                if code in searchmap:
                    # Mon Aug 12 10:56:07 CEST 2013 - Mathias Andre
                    # We auto-generate english translations for e.g. USA, IRELAND,
                    # but we don't want these linked on the websites, so we skip them
                    # from the translation list
                    if code.startswith('en') and code != 'en':
                        continue
                    tmp.append( _ctx_for_translation( searchmap[code], lang, ctry, name, code ) )

            if tmp:
                data['countries'].append( tmp )

        return data

    def generate_duplicate_id( self, lang ):
        """
        Returns a new id including the given language code
        """
        if self.source:
            return '%s-%s' % (self.source.pk, lang)
        else:
            return '%s-%s' % (self.pk, lang)

    @classmethod
    def send_notification_mail( cls, sender, instance, raw=False, **kwargs ):
        """
        Send a notification email to a specified address once a translation is ready.
        """
        if raw:
            return
        if instance.translation_ready:
            from_email = settings.DEFAULT_FROM_EMAIL

            #  For http://www.djangoplicity.org/bugs/view.php?id=19639
            #  We only send notifications for 'main' languages if they
            #  are defined in the settings:
            notification_langs = getattr( settings, 'LANGUAGE_ENABLE_NOTIFICATIONS', [])
            if not notification_langs:
                return

            # Check whether the 'translation ready' flag has just been set:
            try:
                old = sender.objects.get( pk=instance.pk )
                if old.translation_ready:
                    return
            except sender.DoesNotExist:
                pass

            # Disable signals to prevent loops
            models.signals.pre_save.disconnect( cls.send_notification_mail, sender=cls )

            for lang in notification_langs:
                if not instance.lang.startswith(lang):
                    continue
                for code, email in settings.LANGUAGES_CONTACTS.items():
                    if code.startswith(lang) and code != instance.lang:

                        # Check if a translation already exists:
                        try:
                            cls.objects.get(source=instance.source, lang=code)
                            # If there is a translation we continue
                            continue
                        except cls.DoesNotExist:
                            kwargs = {
                                'pk': instance.generate_duplicate_id(code),
                                'source': instance.source,
                                'lang': code,
                                'created': datetime.today(),
                                'translation_ready': True,
                                'published': instance.published,
                            }
                            translation = cls(**kwargs)
                            copy_family_translation_fields(instance, translation)
                            translation.save()

                            if not email:
                                continue

                            try:
                                from django.contrib.sites.models import Site
                                domain = Site.objects.get_current().domain
                            except ImportError:
                                domain = ''

                            subject = "%s translation %s ready" % ( str(translation._meta.verbose_name), translation.pk )
                            html_body = render_to_string('archives/ready_email.html', {'type': translation._meta.verbose_name, 'source': instance, 'translation': translation, 'site_url': domain})
                            text_body = strip_tags( html_body )

                            # Send
                            if subject and html_body and from_email:
                                try:
                                    msg = EmailMultiAlternatives( subject, text_body, from_email, [email] )
                                    msg.attach_alternative( html_body, 'text/html' )
                                    msg.send()
                                except Exception:
                                    # Just ignore error if SMTP server is down.
                                    pass

            # Re-enable signals
            models.signals.pre_save.connect( cls.send_notification_mail, sender=cls )

    def update_family_translations(self, **kwargs):
        '''
        Generate/update translations of similar languages
        e.g.: de-ch -> de, de-at
        '''
        if not settings.USE_I18N:
            return

        main_language = self.lang
        if '-' in main_language:
            main_language = main_language.split('-')[0]

        # Get list of languages in the same family
        languages = []
        for code, dummy_name in settings.LANGUAGES:
            if code.startswith(main_language) and code != self.lang:
                languages.append(code)

        # Search for corresponding Proxy class
        if self.is_source():
            module = inspect.getmodule(self)
            proxymodel_name = '%sProxy' % self.__class__.__name__

            if not hasattr(module, proxymodel_name):
                return
            proxymodel = getattr(module, proxymodel_name)
            source = self
        else:
            proxymodel = self.__class__
            source = self.source

        # Disable signals to prevent loops
        models.signals.pre_save.disconnect( self.__class__.send_notification_mail, sender=self )

        for lang in languages:
            try:
                translation = proxymodel.objects.get(source=self.pk, lang=lang)
            except ObjectDoesNotExist:
                kwargs = {
                    'pk': self.generate_duplicate_id(lang),
                    'source': source,
                    'lang': lang,
                    'created': datetime.today(),
                    'translation_ready': True,
                    'published': self.published,
                }
                translation = proxymodel(**kwargs)

            copy_family_translation_fields(self, translation)
            translation.published = self.published  # Carry over 'published' status
            translation.save()

        # Re-enable signals
        models.signals.pre_save.connect( self.__class__.send_notification_mail, sender=self )

    class Translation:
        fields = []  # Translated fields - should be overwritten in subclass.
        excludes = []  # Non-inherited fields - should be overwritten in subclass.
        set_deep_copy = []  # 1-to-N relationships that will be cloned for same-family languages

        # If set to False we don't show the original version if there is no
        # translation and the original is in a different language than the site
        # default (e.g.: Don't show 'es-cl' announcements on 'en' announcements list
        non_default_languages_in_fallback = True

    class Meta:
        abstract = True
        unique_together = ( 'lang', 'source' )


def copy_family_translation_fields(instance, translation):
    for field in instance.Translation.fields:
        setattr(translation, field, getattr(instance, field))
    if hasattr(instance.Translation, 'set_deep_copy'):
        for set_field in instance.Translation.set_deep_copy:
            set_data = getattr(instance, set_field).all()
            for set_item in set_data:
                set_item.pk = None
                set_item.id = None
                getattr(translation, set_field).add(set_item)
