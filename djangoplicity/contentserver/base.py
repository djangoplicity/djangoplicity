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
from requests.exceptions import ConnectionError

from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible

from djangoplicity.contentserver.cdn77_tasks import purge_prefetch


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


class CDN77ContentServer(ContentServer):
    '''
    Content Server to be used with cdn77.com
    Note: Rsync is used to upload directorie (such as zoomify files), and this
    requires the server to have their client SSH keys configured in the CDN
    storage
    '''

    def __init__(self, name, formats=None, url='', url_bigfiles='', remote_dir='', host='', username='', password='',
                 api_login='', api_password='', apiv3_token='', cdn_id='', cdn_id_bigfiles='', cdnv3_id='',
                 cdnv3_id_bigfiles=''):
        super(CDN77ContentServer, self).__init__(name, formats, url, remote_dir)
        self.url_bigfiles = url_bigfiles
        self.api_url = 'https://api.cdn77.com/v2.0/'
        self.apiv3_url = 'https://api.cdn77.com/v3/'
        self.bigfiles_limit = 2147483648  # Files larger than 2GB are served by url_bigfiles
        self.host = host
        self.username = username
        self.password = password
        self.api_login = api_login
        self.api_password = api_password
        self.apiv3_token = apiv3_token
        self.cdn_id = cdn_id
        self.cdn_id_bigfiles = cdn_id_bigfiles
        self.cdnv3_id = cdnv3_id
        self.cdnv3_id_bigfiles = cdnv3_id_bigfiles
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
        headers = {
            'Authorization': 'Bearer {}'.format(self.apiv3_token)
        }
        r = requests.post(
            #  self.api_url + method,
            self.apiv3_url + method,
            data=json.dumps(params),
            headers=headers
        )

        if not r.ok:
            logger.error('Failed API call for "%s" with params: %s', method, params)
            logger.error(u'ERROR {}: {}'.format(r.status_code, r.text))
            return None

        result = r.json()

        if result is None:
            raise Exception('Failed API call: "%s"' % method)

        # if result['status'] == 'error':
        #     raise Exception('Failed API call "%s" "%s" "%s"' %
        #         method, params, result)

        logger.info('Started %s for %s on %s, "%s", request: %s',
            method, self.name, self.cdn_id, result['description'], result['request_id'])

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
                (instance.Archive.Meta.resource_fields_prefix, fmt), None)

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
                params['paths'] = urls_chunk
                method = 'cdn/{}/job/{}'.format(self.cdnv3_id, action)
                self._api(method, params)

        # If necessary also purge/prefetch the large files onto the secondary CDN
        if self.url_bigfiles and urls_bigfiles:
            logger.debug('Will %s urls_bigfiles: %s', action, ', '.join(urls_bigfiles))
            #params['cdn_id'] = self.cdn_id_bigfiles

            for urls_chunk in chunks(urls_bigfiles, 1800):
                logger.info('%s %d URLs', action, len(urls_chunk))
                params['paths'] = urls_chunk
                method = 'cdn/{}/job/{}'.format(self.cdnv3_id_bigfiles, action)
                self._api(method, params)

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
                resource = getattr(instance, '%s%s' % (instance.Archive.Meta.resource_fields_prefix, fmt), None)

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
            resource = getattr(instance, '%s%s' % (instance.Archive.Meta.resource_fields_prefix, fmt), None)

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
