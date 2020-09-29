# -*- coding: utf-8 -*-
#
# djangoplicity-remotearchives
# Copyright (c) 2007-2016, European Southern Observatory (ESO)
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

import logging
import requests
from datetime import datetime

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.encoding import python_2_unicode_compatible

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class RemoteArchive(models.Model):
    url = ''  # URL of the remote Archive JSON, {pk} is a placeholder for the archive PK
    archive_title = None
    lang = None

    id = models.SlugField(_('ID of the remote Archive'), primary_key=True)
    published = models.BooleanField(default=False)
    data = JSONField(blank=True, null=True)
    last_fetch = models.DateTimeField(_('Last fetch'), blank=True, null=True)

    def __getattr__(self, name):
        '''
        If self.lang is set by using object|set_remote_lang:LANGUAGE_CODE in
        the template, then getattr will look for attribute in the data of
        the given lang, otherwise we use the default settings language
        '''
        lang = self.lang or settings.LANGUAGE_CODE

        try:
            return self.data[lang][name]
        except (TypeError, KeyError):
            raise AttributeError

    def __str__(self):
        return self.id

    def get_absolute_url(self):
        raise NotImplementedError('subclasses of RemoteArchive must provide a get_absolute_url() method')

    def get_url(self):
        return self.url.format(pk=self.pk)

    def fetch_data(self):
        '''
        Fetch and update the JSON data in each languages defined
        '''
        url = self.get_url()
        updated = False

        if not self.data:
            self.data = {}

        for lang, _ in settings.LANGUAGES:
            try:
                r = requests.get(url, timeout=10)
            except (requests.ConnectionError, requests.Timeout):
                logger.warning('Could not fetch JSON "%s"', url)
                continue

            if r.status_code != requests.codes.ok:
                logger.warning('Could not fetch JSON "%s", status: %s', url, r.status_code)
                continue

            self.data[lang] = r.json()
            updated = True

        if updated:
            self.last_fetch = datetime.now()
            self.save()

    class Meta:
        abstract = True
