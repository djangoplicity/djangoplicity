# -*- coding: utf-8 -*-
#
# djangoplicity
# Copyright (c) 2007-2015, European Southern Observatory (ESO)
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

from django.conf import settings
from django.db import models
from django.forms import fields

from djangoplicity.contentserver.tasks import sync_content_server


logger = logging.getLogger(__name__)


def _get_content_server_choices():
    '''
    Returns the list of content servers from the settings that will be used by
    the models, the default is '', which is a dummy server
    '''
    return getattr(
        settings,
        'MEDIA_CONTENT_SERVERS_CHOICES',
        (('none', 'Default'), )
    )


def _get_default_content_server():
    return getattr(
        settings,
        'DEFAULT_MEDIA_CONTENT_SERVER',
        'none'
    )


class ContentServerField(models.CharField):
    '''
    Custom field to avoid having choices caught by makemigrations
    '''

    def formfield(self, **kwargs):
        return fields.ChoiceField(
            required=False,
            choices=_get_content_server_choices,
            initial=_get_default_content_server(),
        )


class ContentDeliveryModel(models.Model):
    '''
    Base class that archive that use a content server must inherit from
    '''
    content_server = ContentServerField(max_length=255, blank=True,
        default=_get_default_content_server)
    content_server_ready = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def sync_content_server(self, formats=None, delay=False):
        '''
        Synchronise the given formats (default if None) with the content server
        If delay is True the requests will be store and run in batch.
        '''
        # The Django class can't be serialised, so we send instead the
        # module path and class name
        sync_content_server.delay(self.__module__, self.__class__.__name__,
            self.pk, formats, delay)

    @classmethod
    def content_server_changed(cls, sender, instance, raw, **kwargs):
        '''
        If content_server has changed, we set a flag to call sync_resources for
        the selected content server in the instance post_save
        '''
        if raw:
            # The call doesn't run in raw mode
            return

        if not hasattr(instance, 'content_server'):
            return

        try:
            orig = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            # instance is new, nothing to do
            return

        # Check if the content server has changed
        if orig.content_server != instance.content_server:
            instance.content_server_ready = False
            instance.run_content_server_sync = True

    @classmethod
    def sync_archive_to_content_server(cls, sender, instance, raw, **kwargs):
        '''
        Callback for post_save signal
        '''
        if hasattr(instance, 'run_content_server_sync') and instance.run_content_server_sync:
            instance.sync_content_server()
            del instance.run_content_server_sync

    @classmethod
    def sync_archive_on_rename(cls, sender, old_pk, new_pk, **kwargs):
        '''
        Callback for post_rename signal
        '''
        # TODO: this should be improved to remove the old content using old_pk
        logger.info('Sync archive after rename from "%s" to "%s"', old_pk, new_pk)

        # We first turn of the content server while we sync the archives
        try:
            instance = cls.objects.get(id=new_pk)
            # We don't want to trigger signals when setting content_server_ready,
            # so we use a hack to bypass it instead of using instance.save():
            cls.objects.filter(pk=instance.pk).update(content_server_ready=False)

            instance.sync_content_server()
        except cls.DoesNotExist:
            logger.warning('Could not find archive "%s" (%s)', new_pk, cls)
