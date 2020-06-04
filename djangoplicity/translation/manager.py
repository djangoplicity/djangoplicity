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
from django.db.models import Manager, Q
from djangoplicity.translation.query import TranslationSourceQuerySet, TranslationQuerySet


class TranslationSourceManager(Manager):
    """
    Manager for accessing source objects.
    """
    def get_queryset(self):
        """
        """
        return TranslationSourceQuerySet(self.model).filter(source__isnull=True)

    def language(self, lang):
        '''
        Filters the objects in the given language
        '''
        return TranslationQuerySet(self.model).filter(lang=lang).select_related('source')

    def fallback(self, lang):
        '''
        If no translation for the given language exist look for an original version

        The query returns all the in the given language, or the source objects,
        and we then exclude the objects for which we do have a translation
        in the given language
        '''
        # For some archives we don't want to show original in non-default
        # language if we don't have a translation in the current language,
        # e.g.: We don't show es-cl announcements in the de announcements list

        if getattr(self.model.Translation, 'non_default_languages_in_fallback', True):
            params = Q(lang=lang) | Q(source__isnull=True)
        else:
            params = Q(lang=lang) | Q(source__isnull=True, lang=settings.LANGUAGE_CODE)

        excludes = self.model.objects.filter(params).filter(source__isnull=True,
            translations__lang=lang)

        return TranslationQuerySet(self.model).filter(params).exclude(
            pk__in=excludes
        ).prefetch_related('source')


class TranslationOnlyManager(Manager):
    """
    Manager for accessing translation objects.
    """
    def get_queryset(self):
        """
        """
        return TranslationSourceQuerySet(self.model).filter(source__isnull=False)
