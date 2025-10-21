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

from celery import task
from celery import current_app
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from importlib import import_module

from django.conf import settings
from django.core.mail import send_mail
from djangoplicity.archives.loading import get_archives
from djangoplicity.celery.serialtaskset import str_keys
from djangoplicity.media.consts import MEDIA_CONTENT_SERVERS
from django.contrib.contenttypes.models import ContentType
from djangoplicity.archives.utils import get_all_possible_instance_formats, get_instance_checksum, initialize_resource


logger = get_task_logger(__name__)


import django
if django.VERSION >= (2, 0):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse

@task
def sync_content_server(module_path, cls_name, instance_id, formats=None,
    delay=False, prefetch=True, purge=True, sendtask_callback=None,
    sendtask_tasksetid=None):
    '''
    Task that will synchronise the resources from the given archive onto
    the content server
    Django Classes can't be serialized easily, so we pass instead the module
    path and class names and import them dynamically
    '''

    if not getattr(settings, 'DEFAULT_MEDIA_CONTENT_SERVER', None):
        logger.info('%s skipping: settings.DEFAULT_MEDIA_CONTENT_SERVER not enabled', sync_content_server.__name__)
        return

    # Dynamically import the class
    module = import_module(module_path)
    cls = getattr(module, cls_name)

    try:
        instance = cls.objects.get(id=instance_id)
    except cls.DoesNotExist:
        logger.warning('Could not find archive "%s" (%s)', instance_id, cls)
        return

    if hasattr(instance, 'content_server') and instance.content_server:
        try:
            content_server = MEDIA_CONTENT_SERVERS[instance.content_server]
            content_server.sync_resources(instance, formats, delay, prefetch, purge)
            sync_content_server_resources_model(module_path, cls_name, instance_id)
        except KeyError:
            logger.warning('Unknown content server: "%s" for %s: "%s"',
                instance.content_server, cls, instance.id)

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task(*args, **str_keys(kwargs))


@task
def download_from_content_server(module_path, cls_name, instance_id, formats=None, include_directories=False, 
    sendtask_callback=None, sendtask_tasksetid=None):
    '''
    Task that will download the resources from the content server (S3) to the local directories
    if they don't exist locally. This is the opposite of sync_content_server.
    Directory resources (like zoomable) are skipped by default unless include_directories=True.
    Django Classes can't be serialized easily, so we pass instead the module
    path and class names and import them dynamically
    '''

    if not getattr(settings, 'DEFAULT_MEDIA_CONTENT_SERVER', None):
        logger.info('%s skipping: settings.DEFAULT_MEDIA_CONTENT_SERVER not enabled', download_from_content_server.__name__)
        return

    # Dynamically import the class
    module = import_module(module_path)
    cls = getattr(module, cls_name)

    try:
        instance = cls.objects.get(id=instance_id)
    except cls.DoesNotExist:
        logger.warning('Could not find archive "%s" (%s)', instance_id, cls)
        return

    if hasattr(instance, 'content_server') and instance.content_server:
        try:
            content_server = MEDIA_CONTENT_SERVERS[instance.content_server]
            content_server.download_resources(instance, formats, include_directories)
        except KeyError:
            logger.warning('Unknown content server: "%s" for %s: "%s"',
                instance.content_server, cls, instance.id)

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task(*args, **str_keys(kwargs))

@task
def sync_content_server_resources_model(module_path, cls_name, instance_id, sendtask_callback=None, sendtask_tasksetid=None):
    '''
    This task will create or update the records in the ContentServerResource model 
    which is used to know which files are available in the content server, 
    and also the extensions, file sizes, etc
    '''
    from djangoplicity.contentserver.models import ContentServerResource

    # Dynamically import the class
    module = import_module(module_path)
    cls = getattr(module, cls_name)

    try:
        instance = cls.objects.get(id=instance_id)
    except cls.DoesNotExist:
        logger.warning('Could not find archive "%s" (%s)', instance_id, cls)
        return

    if hasattr(instance, 'content_server') and instance.content_server and instance.content_server_ready:
        try:
            content_server = MEDIA_CONTENT_SERVERS[instance.content_server]
            if not content_server.requires_local_files:
                content_type = ContentType.objects.get_for_model(instance)
                formats = get_all_possible_instance_formats(instance)

                for format in formats:
                    # Create or update ContentServerResource record for future use
                    try:
                        resource_manager = getattr(instance.Archive, format, None)
                        resource_path = None
                        is_directory = False
                        # Try all extensions to know if the file with the extension already exist in the content server
                        for content_server_ext in resource_manager.exts:
                            resource = initialize_resource(instance, format, content_server_ext)
                            if content_server.resource_exists(resource):
                                resource_path = content_server.to_content_server_path(resource.path)
                                size = content_server.get_file_size(resource)
                                break
                        else:
                            # Fallback to check if directory exists, like for zoomable
                            resource = initialize_resource(instance, format)
                            if content_server.resource_exists(resource):
                                resource_path = content_server.to_content_server_path(resource.path)
                                size = 0
                                is_directory = True
                        
                        if resource_path:
                            # Create or update the ContentServerResource
                            ContentServerResource.objects.update_or_create(
                                content_type=content_type,
                                object_id=instance.pk,
                                content_server_path=resource_path,
                                defaults={
                                    'format': format,
                                    'resource_size': size,
                                    'checksum': get_instance_checksum(instance, format),
                                    'content_server': instance.content_server,
                                    'is_directory': is_directory,
                                    'is_active': True
                                }
                            )
                        
                    except Exception as e:
                        print(f"Could not create/update ContentServerResource: {e}")
        except KeyError:
            logger.warning('Unknown content server: "%s" for %s: "%s"',
                instance.content_server, cls, instance.id)

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task(*args, **str_keys(kwargs))


@task
def check_content_server_resources(last=40):
    '''
    Verify that the resources for the last "last" resources where the CDN
    is enabled do exist in the CDN for all the resourcs which inherit from
    ContentDeliveryModel
    '''
    if settings.SITE_ENVIRONMENT != 'prod':
        logger.info('%s only runs on a production system', check_content_server_resources.__name__)
        return

    from djangoplicity.contentserver.models import ContentDeliveryModel

    # Get list of CDNs which use a remote archive
    cdns = [c for c in list(settings.MEDIA_CONTENT_SERVERS.values()) if c.remote_archive]

    # Get list of Archive models which inherit from ContentDeliveryModel
    models = [m for m, _o in get_archives() if issubclass(m, ContentDeliveryModel)]

    one_week = datetime.now() + timedelta(days=7)

    message = u''

    for cdn in cdns:
        for model in models:
            # Check that the model is configured for the given CDN and inherits
            # from ContentDeliveryModel
            archive_class_name = '%s.%s' % (model.__module__, model.__name__)

            if archive_class_name not in cdn.formats or not issubclass(model, ContentDeliveryModel):
                continue

            # We're interested in the last "last" resources, with
            # a release_date less than a week in the future
            for instance in model.objects.filter(content_server=cdn.name,
                    content_server_ready=True,
                    release_date__lte=one_week).order_by('-last_modified')[:last]:

                failed, size_mismatch = cdn.check_content_server_resources(instance)

                admin_url = 'https://%s%s?q=%s' % (
                    settings.SITE_DOMAIN,
                    reverse('admin_site:media_%s_changelist' % model.__name__.lower()),
                    instance.pk
                )

                if failed:
                    message += '\nMissing in CDN "%s", %s: %s\n' % (
                        cdn.name, model.__name__, admin_url)
                    for resource in failed:
                        message += ' - %s\n' % resource.url

                if size_mismatch:
                    message += '\nSize mismatch in CDN "%s", %s: %s\n' % (
                        cdn.name, model.__name__, admin_url)
                    for resource, size in size_mismatch:
                        message += ' - %s\n' % resource.url
                        message += '   Expected: %d, Got: %d\n' % (resource.size, size)

    if message and hasattr(settings, 'ADMINS'):
        try:
            to = settings.ADMINS[0][1]
            send_mail(
                'Found missing files on CDNs remote archive',
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
                [to]
            )
        except IndexError:
            # Could not find not admin email in settings
            pass
