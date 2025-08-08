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
import os

from django.conf import settings
from django.db import models
from django.forms import fields
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator

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


class ContentServerResource(models.Model):
    """
    Generic model to track content server resources that can be linked to any model.
    
    This model stores metadata about resources stored in content servers including:
    - Format (original, thumbs, screen, ultra_hd), resource size, checksum
    - Generic foreign key to link to any model
    - Creation and modification timestamps
    """
    
    # Core resource information
    format = models.CharField(max_length=30, help_text="The archive format (e.g. original, thumbs, screen, ultra_hd)")
    extension = models.CharField(max_length=20, blank=True, help_text="File extension (e.g., .tif, .png, .mp4)")
    resource_size = models.BigIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Resource size in bytes"
    )
    checksum = models.CharField(max_length=128, blank=True, null=True, help_text="Resource checksum (MD5/SHA256)")
    
    # Content server information
    content_server = ContentServerField(max_length=255, blank=True, default=_get_default_content_server)
    content_server_path = models.CharField(max_length=500, help_text="Full path on content server")
    
    # Generic foreign key to link to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.SlugField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Resource type
    is_directory = models.BooleanField(default=False, help_text="Whether this resource is a directory")
    
    # Status and tracking
    is_active = models.BooleanField(default=True, help_text="Whether the resource is currently active")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_at = models.DateTimeField(null=True, blank=True, help_text="When the resource was uploaded")
    
    class Meta:
        verbose_name = 'Content Server Resource'
        verbose_name_plural = 'Content Server Resources'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['format']),
            models.Index(fields=['is_directory']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['content_server_path', 'is_active']),
        ]
    
    def __str__(self):
        resource_type = "Directory" if self.is_directory else "File"
        return f"{resource_type} ({self.format}) - {self.content_server_path}"
    
    def save(self, *args, **kwargs):        
        # Auto-extract extension from content_server_path if not provided
        if not self.extension and self.content_server_path and not self.is_directory:
            _, ext = os.path.splitext(self.content_server_path)
            if ext:
                self.extension = ext.lower()[1:]  # Remove the leading dot
        
        print(f"Saving ContentServerResource: format={self.format}, path={self.content_server_path}, size={self.resource_size}, checksum={self.checksum}")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_resources_for_model(cls, model_instance):
        """
        Get all content server resources for a given model instance
        """
        content_type = ContentType.objects.get_for_model(model_instance)
        return cls.objects.filter(
            content_type=content_type,
            object_id=model_instance.pk,
            is_active=True
        )
    
    @classmethod
    def get_resources_by_format(cls, model_instance, format_type):
        """
        Get content server resources for a given model instance and format
        """
        content_type = ContentType.objects.get_for_model(model_instance)
        return cls.objects.filter(
            content_type=content_type,
            object_id=model_instance.pk,
            format=format_type,
            is_active=True
        )
    
    @classmethod
    def get_files_for_model(cls, model_instance):
        """
        Get file resources for a given model instance
        """
        content_type = ContentType.objects.get_for_model(model_instance)
        return cls.objects.filter(
            content_type=content_type,
            object_id=model_instance.pk,
            is_directory=False,
            is_active=True
        )
    
    @classmethod
    def get_directories_for_model(cls, model_instance):
        """
        Get directory resources for a given model instance
        """
        content_type = ContentType.objects.get_for_model(model_instance)
        return cls.objects.filter(
            content_type=content_type,
            object_id=model_instance.pk,
            is_directory=True,
            is_active=True
        )
    
    def mark_as_deleted(self):
        """Mark the resource as deleted (soft delete)"""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def reactivate(self):
        """Reactivate a deleted resource"""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class ContentDeliveryModel(models.Model):
    '''
    Base class that archive that use a content server must inherit from
    '''
    content_server = ContentServerField(max_length=255, blank=True,
        default=_get_default_content_server)
    content_server_ready = models.BooleanField(default=False)
    content_server_resources = GenericRelation(ContentServerResource)

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