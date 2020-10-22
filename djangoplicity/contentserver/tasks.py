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

logger = get_task_logger(__name__)


import django
if django.VERSION >= (2, 2):
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

    if settings.SITE_ENVIRONMENT != 'prod':
        logger.info('%s only runs on a production system', sync_content_server.__name__)
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
        except KeyError:
            logger.warning('Unkown content server: "%s" for %s: "%s"',
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
