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
from django.utils import timezone
from importlib import import_module

from django.conf import settings
from django.core.mail import send_mail
from djangoplicity.archives.loading import get_archives
from djangoplicity.celery.serialtaskset import str_keys
from djangoplicity.media.consts import MEDIA_CONTENT_SERVERS
from django.contrib.contenttypes.models import ContentType
from djangoplicity.archives.utils import get_all_possible_instance_formats, get_instance_checksum, initialize_resource
import os
import shutil

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
        logger.info('Found instance %s with id %s', cls, instance_id)
    except cls.DoesNotExist:
        logger.warning('Could not find archive "%s" (%s)', instance_id, cls)
        return

    if hasattr(instance, 'content_server') and instance.content_server:
        try:
            content_server = MEDIA_CONTENT_SERVERS[instance.content_server]
            content_server.sync_resources(instance, formats, delay, prefetch, purge)
            # Ensure to get the last updates to the instance, because the content server might have updated it but in the same transaction
            instance.refresh_from_db()
            sync_content_server_resources_model(module_path, cls_name, instance_id)
        except KeyError:
            logger.warning('Unknown content server: "%s" for %s: "%s"',
                instance.content_server, cls, instance.id)

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task(*args, **str_keys(kwargs))
    
    
@task
def rename_resources_in_content_server(module_path, cls_name, old_pk, new_pk):

    from djangoplicity.contentserver.models import ContentServerResource
    # Dynamically import the class
    module = import_module(module_path)
    cls = getattr(module, cls_name)

    content_type = ContentType.objects.get_for_model(cls)
    old_resources = ContentServerResource.objects.filter(
        content_type=content_type,
        object_id=old_pk
    )

    logger.info('Found %s resources with old_pk %s', len(old_resources), old_pk)

    if not old_resources:
        logger.info('No resources found with old_pk %s', old_pk)
        return

    for resource in old_resources:
        try:
            if hasattr(resource, 'content_server') and resource.content_server:
                content_server = MEDIA_CONTENT_SERVERS[resource.content_server]
                if content_server:
                    old_path = resource.content_server_path
                    new_path = old_path.replace(str(old_pk), str(new_pk), 1)

                    content_server.rename_resource(old_path, new_path)

                    # Update the resource in the database
                    resource.object_id = new_pk
                    resource.content_server_path = new_path
                    resource.save() 

                    logger.info('Renamed resource with old_pk %s: %s -> %s', old_pk, old_path, new_path)
        except Exception as e:
            logger.warning('Failed to rename resource %s: %s, format: %s', old_path, e, resource.format)
    
    # In case that something wrong happen during the rename process, we delete the resources with the old pk
    # because after this task, the instance execute another task called sync_content_server and this task
    # will create the resources with the new pk (ContentServerResource Model) and sync them to the content server
    deleted, _ = ContentServerResource.objects.filter(
        content_type=content_type,
        object_id=old_pk
    ).delete()

    logger.info('Deleted %s resources with old_pk %s', deleted, old_pk)


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
                                size = content_server.get_file_size(resource, nocache=True)
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
                            is_public = None
                            try:
                                is_public = content_server.is_publicly_accessible(resource)
                            except Exception:
                                is_public = None

                            defaults = {
                                'format': format,
                                'resource_size': size,
                                'checksum': get_instance_checksum(instance, format),
                                'content_server': instance.content_server,
                                'is_directory': is_directory,
                                'is_active': True,
                            }
                            if is_public is not None:
                                defaults['is_public'] = is_public

                            ContentServerResource.objects.update_or_create(
                                content_type=content_type,
                                object_id=instance.pk,
                                content_server_path=resource_path,
                                defaults=defaults
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


@task(name="contentserver.update_resource_privacy", ignore_result=True)
def update_resource_privacy(app_label, model_name, pk):
    from django.apps import apps

    try:
        logger.info(f"Updating resource privacy for {app_label}.{model_name} ({pk})")
        model_class = apps.get_model(app_label, model_name)
        instance = model_class.objects.get(pk=pk)
        # Ensure the instance has the update_resource_privacy method as ArchiveModel
        if hasattr(instance, 'update_resource_privacy'):
            instance.update_resource_privacy()
    except Exception as e:
        logger.warning("Exception: %s." % e)


@task()
def cleanup_old_local_resources_task():
    local_resources_cleanup_weeks = getattr(settings, 'LOCAL_RESOURCES_CLEANUP_WEEKS', 4)
    logger.info(f"Cleaning up local resources older than {local_resources_cleanup_weeks} weeks")

    deleted_count = cleanup_old_local_resources(weeks=local_resources_cleanup_weeks)
    logger.info(f"Local resources cleanup completed. Deleted {deleted_count} resources")


def cleanup_old_local_resources(weeks=4):
    from djangoplicity.media.models import Image, Video
    
    cutoff_date = timezone.now() - timedelta(weeks=weeks)
    media_root = os.path.normpath(settings.MEDIA_ROOT)
    
    allowed_content_types = {
        ContentType.objects.get_for_model(Image),
        ContentType.objects.get_for_model(Video),
    }
    
    allowed_dirs = [
        os.path.join(media_root, "archives", "videos"),
        os.path.join(media_root, "archives", "images"),
    ]

    deleted_count = 0
    
    for allowed_dir in allowed_dirs:
        for dirpath, dirnames, filenames in os.walk(allowed_dir):
            
            if dirpath == allowed_dir:
                continue
            
            format = os.path.basename(dirpath)
            logger.info(f"Processing directory: {dirpath}, format: {format}")

            if format == "zoomable":
                ids = list(dirnames)
                resources_map = _get_resources_map(cutoff_date, allowed_content_types, ids, format)
                deleted_count += _process_entries(dirpath, dirnames, resources_map, is_dir=True)

                dirnames.clear()  # Don't traverse into zoomable directories
            else:
                ids = [os.path.splitext(f)[0] for f in filenames]
                resources_map = _get_resources_map(cutoff_date, allowed_content_types, ids, format)
                
                deleted_count += _process_entries(dirpath, filenames, resources_map)                   

    return deleted_count


def _process_entries(dirpath, entries, resources_map, is_dir=False):
    """Iterate entries, delete those with a valid resource. Returns deleted count."""
    deleted_count = 0

    for entry in entries:
        entry_id = entry if is_dir else os.path.splitext(entry)[0]

        resource = resources_map.get(entry_id)
        logger.info(f"Checking entry: {entry}, resource found: {bool(resource)}")
        if not resource:
            continue

        if _try_delete_path(resource, os.path.join(dirpath, entry), is_dir=is_dir):
            deleted_count += 1

    return deleted_count


def _try_delete_path(resource, path, is_dir=False):
    """Attempt to delete a file from disk. Returns True if deleted."""
    try:
        content_server = MEDIA_CONTENT_SERVERS[resource.content_server]
    except KeyError:
        logger.warning(f"Unknown content server '{resource.content_server}' for resource {resource.object_id}, skipping")
        return False

    if not _is_ready_for_deletion(resource, content_server, is_dir=is_dir):
        return False

    try:
        if is_dir:
            shutil.rmtree(path)
        else:
            os.remove(path)
        logger.info(f"Deleted local resource {resource.object_id}: {path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to delete {path} for resource {resource.object_id}: {e}")
        return False


def _get_resources_map(cutoff_date, allowed_content_types, ids, format):
    """Fetch matching resources for a format."""
    from djangoplicity.contentserver.models import ContentServerResource

    qs = ContentServerResource.objects.filter(
        object_id__in=ids,
        format=format,
        content_type__in=allowed_content_types,
        created_at__lt=cutoff_date,
        updated_at__lt=cutoff_date,
    ).select_related('content_type').iterator(chunk_size=1000)

    resources_map = {}
    for r in qs:
        resources_map[r.object_id] = r
    
    return resources_map


def _is_ready_for_deletion(resource, content_server, is_dir=False):
    related_object = resource.content_object

    if not related_object:
        logger.warning(f"Resource {resource.id} has no related object, skipping")
        return False

    # 1. Check content ready
    if hasattr(related_object, 'content_server_ready') and not related_object.content_server_ready:
        logger.info(f"Related object {related_object.id} is not ready for content server, skipping resource {resource.id}")
        return False

    # 2. Check file exists in S3
    s3_path = content_server.to_s3_path(resource.content_server_path)
    if is_dir:
        if not content_server.directory_exists(s3_path):
            logger.warning(f"Directory resource {resource.id} does not exist in S3 at '{s3_path}', skipping")
            return False
    else:   
        if not content_server.file_exists(s3_path):
            logger.warning(f"Resource {resource.id} does not exist in S3 at '{s3_path}', skipping")
            return False

    return True


@task
def refresh_resource_privacy_task(app_label, model_name, pk):
    from django.apps import apps
    try:
        model = apps.get_model(app_label, model_name)
        resource = model.objects.get(pk=pk)

        content_server = MEDIA_CONTENT_SERVERS[resource.content_server]

        if not content_server or not hasattr(content_server, 'is_publicly_accessible'):
            return

        is_public = content_server.is_publicly_accessible(resource)

        if is_public is None:
            return

        resource.is_public = is_public
        resource.save(update_fields=['is_public'])
        logger.info(f"Refreshed privacy for #{pk} Content Server Resource with Object ID {resource.object_id}: is_public={is_public}")

    except Exception as e:
        logger.warning(f"Error refreshing privacy for #{pk} Content Server Resource: {e}")


@task
def set_access_tag_for_resource_task(app_label, model_name, pk, access_tag):
    from django.apps import apps

    try:
        model = apps.get_model(app_label, model_name)
        resource = model.objects.get(pk=pk)

        content_server = MEDIA_CONTENT_SERVERS[resource.content_server]

        if (
            not content_server or 
            not hasattr(content_server, 'is_publicly_accessible') or 
            not hasattr(content_server, '_set_access_tag_for_key') or 
            not hasattr(content_server, '_set_access_tag_for_key_in_dir')
        ):
            return

        if resource.format == 'zoomable':
            content_server._set_access_tag_for_key_in_dir(resource.content_server_path, access_tag)
            logger.info(f"Set access tag: {access_tag} for zoomable directory resource #{pk} with Object ID {resource.object_id}")
            
        else:
            content_server._set_access_tag_for_key(resource.content_server_path, access_tag)
            logger.info(f"Set access tag: {access_tag} for #{pk} Content Server Resource with Object ID {resource.object_id}")

        is_public = content_server.is_publicly_accessible(resource)

        if is_public is None:
            return

        resource.is_public = is_public
        resource.save(update_fields=['is_public'])

    except Exception as e:
        logger.warning(f"Error setting access tag: {access_tag} for #{pk} Content Server Resource: {e}")


def _delete_resource_from_content_server(resource):
    '''
    Delete a single ContentServerResource from its content server and from the
    database. Returns True if the resource was deleted, False otherwise
    '''
    try:
        content_server = MEDIA_CONTENT_SERVERS[resource.content_server]
    except KeyError:
        logger.warning(f"Unknown content server '{resource.content_server}' for #{resource.pk} Content Server Resource, skipping")
        return False

    if not content_server or not hasattr(content_server, 'delete_resource_from_content_server'):
        return False

    # Keep a copy of the values for the logs, as the record is deleted below
    pk = resource.pk
    object_id = resource.object_id
    content_server_path = resource.content_server_path

    try:
        content_server.delete_resource_from_content_server(resource)
    except Exception as e:
        # We keep the record in the database so the deletion can be retried,
        # otherwise we would lose track of an orphan file in the content server
        logger.warning(f"Error deleting #{pk} Content Server Resource from content server: {e}")
        return False

    resource.delete()
    logger.info(f"Deleted #{pk} Content Server Resource with Object ID {object_id} and its content in the content server: {content_server_path}")
    return True


@task
def delete_resource_from_content_server_task(app_label, model_name, pk):
    from django.apps import apps

    try:
        model = apps.get_model(app_label, model_name)
        resource = model.objects.get(pk=pk)
    except Exception as e:
        logger.warning(f"Could not find #{pk} Content Server Resource: {e}")
        return

    _delete_resource_from_content_server(resource)


@task
def delete_archive_from_content_server_task(app_label, model_name, pk):
    '''
    Delete an archive and all of its resources from the content server.
    The resources are deleted first, as deleting the archive cascades to the
    ContentServerResource records and we would lose track of their paths
    '''
    from django.apps import apps

    try:
        model = apps.get_model(app_label, model_name)
        instance = model.objects.get(pk=pk)
    except Exception as e:
        logger.warning(f"Could not find archive '{pk}' ({app_label}.{model_name}): {e}")
        return

    if not hasattr(instance, 'content_server_resources'):
        logger.warning(f"Archive '{pk}' ({app_label}.{model_name}) has no content server resources, skipping")
        return

    # We use the generic relation instead of ContentServerResource.get_resources_for_model()
    # as the latter skips the resources marked as inactive, which do still
    # exist in the content server
    resources = list(instance.content_server_resources.all())

    failed = 0
    for resource in resources:
        if not _delete_resource_from_content_server(resource):
            failed += 1

    if failed:
        # We keep the archive so the action can be retried, otherwise we would
        # lose track of the orphan files in the content server
        logger.warning(f"Could not delete {failed} of {len(resources)} resource(s) from the content server for archive '{pk}', the archive is kept")
        return

    instance.delete()
    logger.info(f"Deleted archive '{pk}' ({app_label}.{model_name}) and its {len(resources)} content server resource(s)")
