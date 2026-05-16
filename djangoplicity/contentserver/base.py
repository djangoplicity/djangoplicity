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

from builtins import range
from builtins import object
import json
import logging
import os
import pika
import pysftp
import requests
import subprocess
import time
import boto3
from botocore.config import Config as BotocoreConfig
from requests.exceptions import ConnectionError

from django.conf import settings
from django.core.cache import cache
from six import python_2_unicode_compatible

from djangoplicity.contentserver.cdn77_tasks import purge_prefetch
from djangoplicity.contentserver.constants import AccessTagControl
from urllib.parse import urlparse, urlunparse


logger = logging.getLogger(__name__)

__all__ = ('ContentServer', 'CDN77ContentServer')


def chunks(l, n):
    '''
    Takes a list l, and yields lists of size n
    '''
    for i in range(0, len(l), n):
        yield l[i:i + n]


@python_2_unicode_compatible
class ContentServer(object):
    requires_local_files = True # Wether the content server requires the local copy of the files or not, this is not the case for S3 which can work if the local files exists or not
    has_resource_protection_capabilities = False 

    def __init__(self, name, formats=None, url='', remote_dir=''):
        '''
        * name: Human friendly name of the Content server
        * formats: List of formats to be served by the server
        * url: Base URL of the server
        * remote_dir: Base path used when uploading files to the server
        '''
        if formats is None:
            formats = {}
        self.name = name
        # We convert the list to sets for faster lookups
        self.formats = dict(
            [(key, set(values)) for key, values in list(formats.items())]
        )
        self.url = url
        self.remote_dir = remote_dir
        # Set to True if the files are served through a different archive:
        self.remote_archive = False

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def get_url(self, resource, format_name):
        '''
        In some cases we might used different URLs based one e.g. file size, etc.
        '''
        return self.url

    def get_file_size(self, resource, nocache=False):
        """
        Dummy method for getting file size. Should be overridden by subclasses if needed.
        """
        return None

    def get_resource_privacy(self, resource):
        """
        Return a boolean indicating whether the resource is private in the
        content server. Returns None if privacy cannot be determined.
        """
        return None

    def sync_resources(self, instance, formats=None, delay=False, prefetch=True, purge=True):
        '''
        Synchronise the resources of the given instance to the content server
        if necessary.
        If formats is specified only the given formats are synchronised
        At least it must set instance.content_server_ready to True
        '''
        # We don't want to trigger signals when setting content_server_ready,
        # so we use a hack to bypass it instead of using instance.save():
        instance.__class__.objects.filter(pk=instance.pk).update(content_server_ready=True)
        logger.info('Enabled content_server_ready for %s: %s', instance.id, self.name)

    def check_content_server_resources(self, instance, formats=None):
        '''
        Check that the resources for the given instance do exist in the CDN.
        Returns a list of URLs which returned an error
        '''
        return []

    def delete_resource(self, path):
        """
        Delete a resource from the content server.
        """
        pass
    
    def rename_resource(self, old_path, new_path):
        """
        Rename a resource on the content server.
        """
        pass


class S3ContentServer(ContentServer):
    supports_all_formats = True
    requires_local_files = False
    name = 'S3'
    resource_size_cache_timeout = 60 * 5  # seconds
    resource_size_cache_negative_timeout = 60 * 3  # seconds for failures/missing
    has_resource_protection_capabilities = True

    def __init__(self, bucket, base_url=None, bigfiles_base_url=None, bigfiles_limit=None, access_key_id=None, access_key_secret=None, region_name=None, always_public_formats=None):
        config = None
        if region_name:
            config = BotocoreConfig(region_name=region_name)
        self.s3_client = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=access_key_secret, config=config)
        self.bucket = bucket
        self.base_url = base_url
        self.bigfiles_base_url = bigfiles_base_url
        self.bigfiles_limit = bigfiles_limit if bigfiles_limit else 50_000_000_000 # 50GB as default
        self.always_public_formats = always_public_formats if always_public_formats else [] # Void list by default

    def get_file_size(self, resource, nocache=False):
        from djangoplicity.contentserver.models import ContentServerResource
        """
        Get the file size from cache/DB/S3 for the given resource.
        Returns the file size in bytes, or None if not found.
        """
        s3_path = self.to_s3_path(resource.path)
        cache_key = f"s3_resource_size:{self.bucket}:{s3_path}"
        if not nocache:
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                if cached_value == -1:
                    return None
                return cached_value

            # Try DB first
            resource_size = ContentServerResource.objects.filter(
                content_server_path=s3_path, is_active=True
            ).values_list('resource_size', flat=True).first()

            if resource_size is not None:
                cache.set(cache_key, resource_size, timeout=self.resource_size_cache_timeout)
                return resource_size

        # Fall back to S3 HEAD request
        try:
            logger.info(f"S3 REMOTE FILE SIZE?: {s3_path}")
            response = self.s3_client.head_object(Bucket=self.bucket, Key=s3_path)
            size = response['ContentLength']
            cache.set(cache_key, size, timeout=self.resource_size_cache_timeout)
            return size
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not get S3 file size for {s3_path}: {e}")
            # Negative cache to avoid repeated DB/S3 calls for a while
            cache.set(cache_key, -1, timeout=self.resource_size_cache_negative_timeout)
            return None

    def get_url(self, resource, format_name):
        # Resources like zoomable are directories, so they doesn't have resource.size, that's this is tested first
        resource_size = None
        if resource and not self.is_directory(resource):
            # For common image formats that are known to be small, avoid the remote size lookup
            try:
                _, extension = os.path.splitext(resource.path or '')
            except Exception:
                extension = ''
            extension = extension.lower()
            if extension not in ('.jpg', '.png'):
                resource_size = self.get_file_size(resource)
        if resource_size and self.bigfiles_base_url and resource_size > self.bigfiles_limit:
            return self.bigfiles_base_url
        if self.base_url:
            return self.base_url
        
        return 'https://%s.s3.amazonaws.com/media' % (self.bucket,)

    def is_directory(self, resource):
        s3_path = self.to_s3_path(resource.path)
        # If the s3_path does not have an extension, treat it as a directory
        return '.' not in s3_path.split('/')[-1]

    def resource_exists(self, resource):
        s3_path = self.to_s3_path(resource.path)
        print('S3 RESOURCE EXISTS?: ' + s3_path)
        if self.is_directory(resource):
            return self.directory_exists(s3_path)
        return self.file_exists(s3_path)

    def file_exists(self, s3_path):
        """
        Check if a file exists in the S3 bucket at the given s3_path.
        Returns True if the file exists, False otherwise.
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=s3_path)
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception:
            # For any other error (e.g., forbidden, etc.), treat as not found
            return False
        
    def directory_exists(self, dir):
        if not dir.endswith('/'):
            dir += '/'
        
        response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=dir, MaxKeys=1)
        return 'Contents' in response

    def to_content_server_path(self, local_path):
        return self.to_s3_path(local_path)

    def to_s3_path(self, local_path):
        remote_path = local_path.replace(settings.BASE_DIR, '')
        if remote_path.startswith('/'):
            remote_path = remote_path[1:]
        return remote_path

    def get_resource_privacy(self, resource):
        """
        Return a boolean indicating whether the resource is private in the
        content server. Returns None if privacy cannot be determined.
        """
        path = None
        if hasattr(resource, 'path'):
            path = resource.path
        
        if not path and hasattr(resource, 'content_server_path'):
            path = resource.content_server_path

        remote_path = self.to_s3_path(path)
        if not remote_path:
            return None

        try:
            tagging = self.s3_client.get_object_tagging(Bucket=self.bucket, Key=remote_path)
            for tag in tagging.get('TagSet', []):
                if tag.get('Key') == 'Access':
                    return tag.get('Value').lower()
        except self.s3_client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            logger.warning('S3ContentServer: Could not read privacy tag for %s: %s', remote_path, e)
            return None

        return None
    
    def is_publicly_accessible(self, resource):
        """Return True if the resource is public, False otherwise."""
        return self.get_resource_privacy(resource) == AccessTagControl.PUBLIC.value.lower()

    def sync_resources(self, instance, formats=None, *args, **kwargs):
        from djangoplicity.archives.utils import get_all_possible_instance_formats

        archive_formats = get_all_possible_instance_formats(instance)
        formats = formats or archive_formats

        for fmt in formats:
            # Get the local resource (if any)
            resource = getattr(instance, '%s%s' % (instance.Archive.Meta.resource_fields_prefix, fmt + '_only_local_files'), None)

            if not resource:
                continue

            # Skip the resource if it's a file with size 0
            if os.path.isfile(resource.path) and resource.size == 0:
                logger.warning('S3ContentServer: Skipping empty file: %s', resource.path)
                continue
            
            remote_path = self.to_s3_path(resource.path)
            # There are some archive types that are directories, like the zoomable and the virtualtours
            if os.path.isdir(resource.path):
                logger.info('S3ContentServer: Uploading directory %s to %s:%s', resource.name, self.bucket, remote_path)
                
                # Make sure that we won't rsync to the root:
                if remote_path == instance.Archive.Meta.root or remote_path == '/' or remote_path == '':
                    raise Exception('S3ContentServer: remote_path is in root: %s', remote_path)

                for root, dirs, files in os.walk(resource.path):
                    for filename in files:
                        local_path = os.path.join(root, filename)
                        self.s3_client.upload_file(local_path, self.bucket, self.to_s3_path(local_path))
            else:
                logger.info('S3ContentServer: Uploading %s to bucket %s:%s', resource.name, self.bucket, remote_path)
                # TODO: Improve content type detection
                content_type = 'application/octet-stream'
                if resource.name.endswith('.jpg') or resource.name.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif resource.name.endswith('.png'):
                    content_type = 'image/png'
                elif resource.name.endswith('.gif'):
                    content_type = 'image/gif'
                elif resource.name.endswith('.mp4'):
                    content_type = 'video/mp4'

                access_tag = instance.get_access_tag_for_format(fmt).value
                
                if access_tag:
                    logger.info('S3ContentServer: Setting tag Access=%s for %s', access_tag, instance)
                else:
                    logger.warning('S3ContentServer: No access tag found for %s', instance)

                extra_args = {'ContentType': content_type, 'Tagging': f'Access={access_tag}'}

                # upload the file with the tag included
                self.s3_client.upload_file(resource.path, self.bucket, remote_path, ExtraArgs=extra_args)


        # We set the content server to ready as soon as the files are
        # synchronised, we don't have to wait until it's purged/prefetched
        # We don't want to trigger signals when setting content_server_ready,
        # so we use update instead of using instance.save():
        instance.__class__.objects.filter(pk=instance.pk).update(
            content_server_ready=True)
        logger.info('S3ContentServer: Enabled content_server_ready for %s %s',
            instance.__class__.__name__, instance.id)
    
    def update_resource_privacy(self, instance):
        """
        Update the access tag for this object to sync with S3
        This handles both local files and tracked resources in ContentServerResource.
        """
        from djangoplicity.archives.utils import get_all_possible_instance_formats
        from djangoplicity.contentserver.models import ContentServerResource
        from django.contrib.contenttypes.models import ContentType

        logger.info("S3ContentServer: Updating access tag for: %s", instance)
        
        if not hasattr(instance, 'get_access_tag'):
            logger.warning('S3ContentServer: No access tag found for %s', instance)
            return
        
        formats = get_all_possible_instance_formats(instance)
        content_type = ContentType.objects.get_for_model(instance)
        
        processed_paths = set()

        # Step 1: Update tags for local files that still exist
        for fmt in formats:
            resource = getattr(instance, '%s%s' % (instance.Archive.Meta.resource_fields_prefix, fmt + '_only_local_files'), None)

            if not resource:
                continue

            remote_path = self.to_s3_path(resource.path)
            
            # Exclude directories (e.g. zoomable and virtualtours)
            if not os.path.isdir(resource.path):

                access_tag = instance.get_access_tag_for_format(fmt).value
                logger.info('S3ContentServer: Setting tag Access=%s for %s - format: %s', access_tag, instance, fmt)
                self.s3_client.put_object_tagging(
                    Bucket=self.bucket, 
                    Key=remote_path, 
                    Tagging={'TagSet': [{'Key': 'Access', 'Value': access_tag}]}
                )

                try:
                    is_public = access_tag.lower() == AccessTagControl.PUBLIC.value.lower()
                    ContentServerResource.objects.filter(
                        content_type=content_type,
                        object_id=instance.pk,
                        content_server_path=remote_path,
                        content_server=instance.content_server,
                        is_active=True
                    ).update(is_public=is_public)
                    processed_paths.add(remote_path)
                except Exception as e:
                    logger.warning('S3ContentServer: Could not update ContentServerResource privacy record for %s: %s', remote_path, e)

        # Step 2: Update privacy for all tracked resources in ContentServerResource
        # This handles resources that may no longer exist locally but are still tracked
        try:
            tracked_resources = ContentServerResource.objects.filter(
                content_type=content_type,
                object_id=instance.pk,
                content_server=instance.content_server,
                is_active=True,
            )

            logger.info(f"S3ContentServer: Found {tracked_resources.count()} tracked resources for {instance}")

            for resource in tracked_resources:
                try:
                    remote_path = resource.content_server_path
                    
                    if remote_path in processed_paths:
                        logger.info('S3ContentServer: Already processed resource %s, skipping: %s', resource, remote_path)
                        continue

                    access_tag = instance.get_access_tag_for_format(resource.format).value
                    logger.info('S3ContentServer: Setting tag Access=%s for tracked resource %s - format: %s', access_tag, resource, resource.format)
                    self.s3_client.put_object_tagging(
                        Bucket=self.bucket, 
                        Key=remote_path, 
                        Tagging={'TagSet': [{'Key': 'Access', 'Value': access_tag}]}
                    )

                    is_public = access_tag.lower() == AccessTagControl.PUBLIC.value.lower()
                    ContentServerResource.objects.filter(
                        pk=resource.pk
                    ).update(is_public=is_public)
                    
                except Exception as e:
                    logger.warning('S3ContentServer: Could not update privacy for tracked resource %s: %s', resource, e)
        except Exception as e:
            logger.warning(f"S3ContentServer: Error processing tracked resources for {instance}: {e}")

    def download_resources(self, instance, formats=None, include_directories=False, *args, **kwargs):
        """
        Download resources from S3 to local directories if they don't exist locally.
        This is the opposite of sync_resources.
        
        Args:
            instance: The archive instance
            formats: List of formats to download (default: all formats)
            include_directories: Whether to download directory resources (default: False)
        """
        from djangoplicity.archives.utils import get_all_possible_instance_formats

        archive_formats = get_all_possible_instance_formats(instance)
        formats = formats or archive_formats

        for fmt in formats:
            # Get the local resource (if any)
            attr_name = f"{instance.Archive.Meta.resource_fields_prefix}{fmt}"
            resource = getattr(instance, attr_name, None)

            if not resource:
                continue

            # Skip if the local file already exists
            if os.path.isfile(resource.path) or os.path.isdir(resource.path):
                logger.info('S3ContentServer: Local file/directory already exists, skipping download: %s', resource.path)
                continue

            remote_path = self.to_s3_path(resource.path)
            
            # Check if the resource exists in S3
            if not self.resource_exists(resource):
                logger.warning('S3ContentServer: Resource does not exist in S3, skipping: %s', remote_path)
                continue

            # Skip directory resources by default unless explicitly requested
            if self.is_directory(resource):
                if not include_directories:
                    logger.info('S3ContentServer: Skipping directory resource (use include_directories=True to download): %s', remote_path)
                    continue
                else:
                    logger.info('S3ContentServer: Downloading directory %s from %s:%s', resource.name, self.bucket, remote_path)
                    self._download_directory_from_s3(remote_path, resource.path)
            else:
                # Create local directory if it doesn't exist
                local_dir = os.path.dirname(resource.path)
                if local_dir and not os.path.exists(local_dir):
                    os.makedirs(local_dir, exist_ok=True)
                    logger.info('S3ContentServer: Created local directory: %s', local_dir)
                
                logger.info('S3ContentServer: Downloading file %s from bucket %s:%s', resource.name, self.bucket, remote_path)
                self._download_file_from_s3(remote_path, resource.path)

        logger.info('S3ContentServer: Completed downloading resources for %s %s',
            instance.__class__.__name__, instance.id)

    def _download_file_from_s3(self, s3_path, local_path):
        """
        Download a single file from S3 to local path.
        """
        try:
            self.s3_client.download_file(self.bucket, s3_path, local_path)
            logger.info('S3ContentServer: Successfully downloaded file: %s', local_path)
        except Exception as e:
            logger.error('S3ContentServer: Failed to download file %s: %s', local_path, str(e))
            raise

    def _download_directory_from_s3(self, s3_prefix, local_dir):
        """
        Download a directory from S3 to local directory.
        """
        try:
            # Ensure local directory exists
            os.makedirs(local_dir, exist_ok=True)
            
            # List all objects with the given prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=s3_prefix)
            
            downloaded_files = 0
            for page in pages:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    
                    # Skip if it's just the directory marker
                    if s3_key.endswith('/'):
                        continue
                    
                    # Calculate local file path
                    relative_path = s3_key[len(s3_prefix):].lstrip('/')
                    local_file_path = os.path.join(local_dir, relative_path)
                    
                    # Create subdirectories if needed
                    local_file_dir = os.path.dirname(local_file_path)
                    if local_file_dir and not os.path.exists(local_file_dir):
                        os.makedirs(local_file_dir, exist_ok=True)
                    
                    # Download the file
                    self.s3_client.download_file(self.bucket, s3_key, local_file_path)
                    downloaded_files += 1
            
            logger.info('S3ContentServer: Successfully downloaded directory with %d files: %s', downloaded_files, local_dir)
            
        except Exception as e:
            logger.error('S3ContentServer: Failed to download directory %s: %s', local_dir, str(e))
            raise
    
    def get_signed_url(self, resource, format, expires_in=3600):
        logger.info("S3ContentServer: Generating signed URL for %s", resource.path)
        try:
            s3_path = self.to_s3_path(resource.path)
            # Get signed url
            signed_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': s3_path},
                ExpiresIn=expires_in
            )

            return signed_url

            # # Parse signed url to get the path
            # parsed_url = urlparse(signed_url)

            # # Get base url
            # base_url = self.get_url(resource, format)

            # # Parse base url
            # base_url_parsed = urlparse(base_url)

            # # Create new signed url replacing schema and netlock with base url
            # new_signed_url = urlunparse((
            #     base_url_parsed.scheme or parsed_url.scheme,
            #     base_url_parsed.netloc,
            #     parsed_url.path,
            #     parsed_url.params,
            #     parsed_url.query,
            #     parsed_url.fragment,
            # ))

            # return new_signed_url
        except Exception as e:
            logger.error('S3ContentServer: Failed to generate signed URL for %s: %s', resource.path, str(e))
            raise
    
    def delete_resource(self, path):
        """
        Delete a resource from the content server.
        """
        try:
            if not path:
                return
            self.s3_client.delete_object(Bucket=self.bucket, Key=path)
            logger.info('S3ContentServer: Deleted %s from S3', path)
        except Exception as e:
            logger.error('S3ContentServer: Failed to delete %s: %s', path, str(e))
            raise
    
    def rename_resource(self, old_path, new_path):
        """
        Rename a resource in the content server using copy and delete.
        Handles both single files and directories (S3 prefixes).
        """
        try:
            if not old_path or not new_path:
                return
            
            _, ext = os.path.splitext(old_path)

            if old_path.endswith('/') or not ext:
                self._rename_directory(old_path, new_path)
            else:
                self._rename_single_resource(old_path, new_path)

        except Exception as e:
            logger.error('S3ContentServer: Failed to rename %s to %s: %s', old_path, new_path, str(e))
            raise
    
    def _rename_single_resource(self, old_path, new_path):
        '''
        Rename a single file in S3
        '''
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket,
                CopySource={'Bucket': self.bucket, 'Key': old_path},
                Key=new_path
            )
            self.s3_client.delete_object(Bucket=self.bucket, Key=old_path)
            logger.info('S3ContentServer: Renamed file %s -> %s', old_path, new_path)
        except Exception as e:
            logger.error('S3ContentServer: Failed to rename %s to %s: %s', old_path, new_path, str(e))
            raise
    
    def _rename_directory(self, old_path, new_path):
        '''
        Rename a directory in S3
        '''
        if not old_path.endswith('/'):
            old_path = old_path + '/'
        if not new_path.endswith('/'):
            new_path = new_path + '/'
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=old_path)

            for page in pages:
                for obj in page.get('Contents', []):
                    old_key = obj['Key']
                    suffix = old_key[len(old_path):]
                    new_key = new_path + suffix

                    self.s3_client.copy_object(
                        Bucket=self.bucket,
                        CopySource={'Bucket': self.bucket, 'Key': old_key},
                        Key=new_key
                    )
                    self.s3_client.delete_object(Bucket=self.bucket, Key=old_key)
                    logger.info('S3ContentServer: Renamed %s -> %s', old_key, new_key)
        except Exception as e:
            logger.error('S3ContentServer: Failed to rename directory %s to %s: %s', old_path, new_path, str(e))
            raise


class CDN77ContentServer(ContentServer):
    '''
    Content Server to be used with cdn77.com
    Note: Rsync is used to upload directorie (such as zoomify files), and this
    requires the server to have their client SSH keys configured in the CDN
    storage
    '''
    def __init__(self, name, formats=None, url='', url_bigfiles='',
            remote_dir='', host='', username='', password='', api_login='',
            api_password='', cdn_id='', cdn_id_bigfiles=''):
        super(CDN77ContentServer, self).__init__(name, formats, url, remote_dir)
        self.url_bigfiles = url_bigfiles
        self.api_url = 'https://api.cdn77.com/v2.0/'
        self.bigfiles_limit = 2147483648  # Files larger than 2GB are served by url_bigfiles
        self.host = host
        self.username = username
        self.password = password
        self.api_login = api_login
        self.api_password = api_password
        self.cdn_id = cdn_id
        self.cdn_id_bigfiles = cdn_id_bigfiles
        # Set to True if the files are served through a different archive
        self.remote_archive = True
        self.purge_queue = 'cdn77-purge'
        self.prefetch_queue = 'cdn77-prefetch'

    def _api(self, method, params):
        '''
        Make a 'method' API call with the given parameters
        Returns a json dictionnary with the call's result, or None if the
        call fails
        e.g.:
            method = '/cdn-resource/list'
            params = {
                'login': 'login@example.com',
                'passwd': 'password',
            }
        '''
        r = requests.post(self.api_url + method, data=params)

        if r.status_code != requests.codes.ok:
            logger.error('Failed API call for "%s" with params: %s', method, params)
            return None

        result = r.json()

        if result is None:
            raise Exception('Failed API call: "%s"' % method)

        if result['status'] == 'error':
            raise Exception('Failed API call "%s" "%s" "%s"' %
                method, params, result)

        logger.info('Started %s for %s on %s, "%s", request: %s',
            method, self.name, self.cdn_id, result['description'],
            result['request_id'])

        return result

#
#       if urls:
#           if purge:
#               # Purge the URLs first
#               result = self._api('data/purge', params)
#               if result is None:
#                   # API call failed
#                   return False
#
#               if result['status'] == 'error':
#                   logger.error('Failed purge for %s on %s: "%s"',
#                       instance.id, self.name, result)
#                   return False
#
#               logger.info('Started purge for %s on %s(%s), %s: "%s", request: %s',
#                   instance.id, self.name, self.cdn_id, urls, result['description'], result['request_id'])
#
#           result = self._api('data/prefetch', params)
#
#           if result is None:
#               # API call failed
#               return False
#
#           if result['status'] == 'error':
#               logger.error('Failed prefetch for %s on %s: "%s"',
#                   instance.id, self.name, result)
#               return False
#
#           logger.info('Started prefetch for %s on %s(%s), %s: "%s", request: %s',
#               instance.id, self.name, self.cdn_id, urls, result['description'], result['request_id'])
#
#       # If necessary also prefetch the large files onto the secondary CDN
#       if self.url_bigfiles and urls_bigfiles:
#           params['url[]'] = urls_bigfiles
#           params['cdn_id'] = self.cdn_id_bigfiles

    def get_url(self, resource, format_name):
        # If a large file URL is specified and the resource is > 2GB
        # we serve it through url_bigfiles
        if format_name == 'zoomable':
            # Zoomable are a special case as they don't have a resource.size
            return self.url
        if self.url_bigfiles and resource.size > self.bigfiles_limit:
            return self.url_bigfiles
        else:
            return self.url

    def _get_rabbitmq_connection(self):
        '''
        Returns the connection and channel to RabbitMQ, also makes sure
        that both queues exist
        '''
        connection = pika.BlockingConnection(pika.URLParameters(
            settings.CELERY_BROKER_URL))
        channel = connection.channel()

        channel.queue_declare(self.purge_queue, durable=True)
        channel.queue_declare(self.prefetch_queue, durable=True)

        return connection, channel

    def _queue_purge_prefetch(self, instance, formats, delay, prefetch, purge):
        '''
        Add the URLs to the purge/prefetch queue, if delay is False call
        the celery task to consume the queue
        '''
        # Build a list of remote URLs
        urls = []
        urls_bigfiles = []
        for fmt in formats:
            # Get the local resource (if any)
            resource = getattr(instance, '%s%s' %
                (instance.Archive.Meta.resource_fields_prefix, fmt + '_only_local_files'), None)

            if not resource:
                continue

            # Build the url
            if resource.name.startswith(instance.Archive.Meta.root):
                url = os.path.join('/', resource.name)
            else:
                url = os.path.join('/', instance.Archive.Meta.root, resource.name)

            if fmt == 'zoomable':
                # We skip zoomable as we can't prefetch a directory and we would
                # have to prefetch every single files one by one
                continue

            if self.url_bigfiles and resource.size > self.bigfiles_limit:
                urls_bigfiles.append(url)
            else:
                urls.append(url)

        message = json.dumps({
            'urls': urls,
            'urls_bigfiles': urls_bigfiles,
        })

        logger.debug('Will queue message: %s', message)

        # Queue the requests
        connection, channel = self._get_rabbitmq_connection()
        properties = pika.BasicProperties(
            content_type='application/json',
            delivery_mode=2,  # delivery_mode 2 is persistent
        )

        if purge:
            channel.basic_publish(
                exchange='',
                routing_key=self.purge_queue,
                body=message,
                properties=properties,
            )

        # We don't prefetch files larger than 2GB, so we recreate message
        # without urls_bigfiles
        message = json.dumps({
            'urls': urls,
            'urls_bigfiles': [],
        })

        channel.basic_publish(
            exchange='',
            routing_key=self.prefetch_queue,
            body=message,
            properties=properties,
        )

        connection.close()

        # If called with delay=False we start the task to actually purge/prefetch
        if delay is False:
            purge_prefetch.delay()

    def purge_prefetch(self, action):
        '''
        Purge/prefetch
        '''
        urls = []
        urls_bigfiles = []

        connection, channel = self._get_rabbitmq_connection()

        if action == 'purge':
            queue = self.purge_queue
        else:
            queue = self.prefetch_queue

        # Get all the messages from the queue
        while True:
            method_frame, _header_frame, message = channel.basic_get(queue)

            if not method_frame:
                # No more messages in queue
                break

            logger.debug('Fetched message %d, left: %d',
                method_frame.delivery_tag, method_frame.message_count)

            channel.basic_ack(method_frame.delivery_tag)
            message = json.loads(message)
            urls += message['urls']
            urls_bigfiles += message['urls_bigfiles']

        connection.close()

        # Build POST parameters
        params = {
            'login': self.api_login,
            'passwd': self.api_password,
            'cdn_id': self.cdn_id,
        }

        # There is a limit of 2000 URLs per requests so we split the URLs
        # in smaller batches if necessary

        if urls:
            logger.debug('Will %s urls: %s', action, ', '.join(urls))
            for urls_chunk in chunks(urls, 1800):
                logger.info('%s %d URLs', action, len(urls_chunk))
                params['url[]'] = urls_chunk
                self._api('data/%s' % action, params)

        # If necessary also purge/prefetch the large files onto the secondary CDN
        if self.url_bigfiles and urls_bigfiles:
            logger.debug('Will %s urls_bigfiles: %s', action, ', '.join(urls_bigfiles))
            params['cdn_id'] = self.cdn_id_bigfiles

            for urls_chunk in chunks(urls_bigfiles, 1800):
                logger.info('%s %d URLs', action, len(urls_chunk))
                params['url[]'] = urls_chunk
                self._api('data/%s' % action, params)

    def sync_resources(self, instance, formats=None, delay=False, prefetch=True, purge=True):
        '''
        Synchronise the instance onto the CDN network
        '''
        try:
            archive_class_name = '%s.%s' % (instance.__module__, instance.__class__.__name__)
            archive_formats = self.formats[archive_class_name]
        except KeyError:
            logger.error('No content server formats defined for "%s"', archive_class_name)
            return

        logger.info('Will run sync_resources for %s %s, formats: %s', instance.__class__.__name__, instance.pk, formats)

        formats = formats or archive_formats

        # TODO: should set content_server_ready to false while we sync.

        with pysftp.Connection(self.host, username=self.username, password=self.password) as sftp:
            for fmt in formats:
                if fmt == 'zoomify':
                    # The photoshop server calls 'zoomable' 'zoomify'
                    fmt = 'zoomable'

                # We only upload formats supported by the content Server
                # (in case specific formats are specified in the method call)
                if fmt not in archive_formats:
                    continue

                # Get the local resource (if any)
                resource = getattr(instance, '%s%s' % (instance.Archive.Meta.resource_fields_prefix, fmt + '_only_local_files'), None)

                if not resource:
                    continue

                # Skip the resource if it's a filewith size 0
                if os.path.isfile(resource.path) and resource.size == 0:
                    logger.warning('Skipping empty file: %s', resource.path)
                    continue

                # Build the remote path on the server

                # Resource name can include Archive.Meta.root depending on whether
                # it's already been uploaded to the CDN, so we add it conditionally:
                if resource.name.startswith(instance.Archive.Meta.root):
                    remote_path = os.path.join(self.remote_dir, resource.name)
                else:
                    remote_path = os.path.join(self.remote_dir, instance.Archive.Meta.root, resource.name)

                # Check that the remote directory exists, and create it if necessary
                remote_dir = os.path.dirname(remote_path)
                if not sftp.exists(remote_dir):
                    logger.info('Creating missing directory: %s:%s', self.host, remote_dir)
                    sftp.makedirs(remote_dir)

                # CD to the correct directory and upload the file
                with sftp.cd():
                    sftp.cwd(remote_dir)
                    if os.path.isdir(resource.path):
                        logger.info('Uploading directory %s to %s:%s', resource.name, self.host, remote_path)
                        # We don't use sftp.put_r to upload directories as even though pysftps' doc
                        # says that it will not complain if the target dir already exists, in practice it
                        # raises an IOError

                        # Make sure that we won't rsync to the root:
                        if remote_path == self.remote_dir:
                            raise Exception('remote_path is equal to root dir: %s', remote_path)

                        cmd = [
                            'rsync',
                            '-a',
                            '--delete',
                            '%s/' % resource.path,
                            '%s@%s:%s/' % (self.username, self.host, remote_path),
                        ]

                        # In case there is an error with rsync we retry up to
                        # 50 times
                        i = 0
                        while True:
                            retcode = subprocess.call(cmd)
                            if retcode == 0:
                                break

                            if i < 50:
                                logger.info('Rsync exited with code %d, trying again.', retcode)
                                time.sleep(2)
                            else:
                                raise Exception('Rsync exited with code %d, check logs', retcode)

                            i += 1
                    else:
                        logger.info('Uploading %s to %s:%s', resource.name, self.host, remote_dir)
                        attempts = 0
                        while True:
                            # In case the sftp fails we try again up to 10x
                            try:
                                sftp.put(resource.path)
                                break
                            except IOError as e:
                                logger.info('IOError on %d attempt, retrying sftp.put()', attempts)
                                attempts += 1
                                if attempts > 10:
                                    raise e

        # We set the content server to ready as soon as the files are
        # synchronised, we don't have to wait until it's purged/prefetched
        # We don't want to trigger signals when setting content_server_ready,
        # so we use update instead of using instance.save():
        instance.__class__.objects.filter(pk=instance.pk).update(
            content_server_ready=True)
        logger.info('Enabled content_server_ready for %s %s: %s',
            instance.__class__.__name__, instance.id, self.name)

        if prefetch or purge:
            self._queue_purge_prefetch(instance, formats, delay, prefetch, purge)

    def download_resources(self, instance, formats=None, include_directories=False, *args, **kwargs):
        """
        Dummy implementation for CDN77ContentServer.
        CDN77ContentServer does not support downloading resources as it's designed
        to serve files from a remote archive without requiring local copies.
        """
        logger.info('CDN77ContentServer: download_resources called but not supported for %s %s - CDN77 serves files remotely', 
                   instance.__class__.__name__, instance.id)
        logger.info('CDN77ContentServer: Skipping download operation (CDN77ContentServer does not support local file downloads)')

    def check_content_server_resources(self, instance, formats=None):
        '''
        Check that the resources for the given instance do exist in the CDN.
        Returns a list of URLs which returned an error
        '''
        try:
            archive_class_name = '%s.%s' % (instance.__module__, instance.__class__.__name__)
            archive_formats = self.formats[archive_class_name]
        except KeyError:
            logger.error('No content server formats defined for "%s"', archive_class_name)
            return

        failed = []
        size_mismatch = []
        formats = formats or archive_formats

        for fmt in formats:
            if fmt == 'zoomable':
                # We skip zoomable as we can't prefetch a directory and we would
                # have to prefetch every single files one by one
                continue

            # Get the local resource (if any)
            resource = getattr(instance, '%s%s' % (instance.Archive.Meta.resource_fields_prefix, fmt + '_only_local_files'), None)

            if not resource:
                continue

            # Skip empty resources
            if resource.size == 0:
                continue

            i = 0
            while True:
                # Try up to 50 times in care there is a temporary server problem
                try:
                    r = requests.head(resource.url)
                    break
                except ConnectionError as e:
                    if i < 50:
                        time.sleep(2)
                    else:
                        raise Exception(e)

                i += 1

            # Check that the file exists in the CDN
            if r.status_code != requests.codes.ok:
                failed.append(resource)
            elif 'content-length' in r.headers:
                # Check that the file size matches
                size = int(r.headers['content-length'])
                if size != resource.size:
                    size_mismatch.append((resource, size))

            # Close the resource to avoid "Too many open files"
            resource.close()

        return (failed, size_mismatch)
