# -*- coding: utf-8 -*-
#
# djangoplicity-media
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


# Provides a youtube apiclient that can be used as described in
# https://developers.google.com/youtube/v3/docs/

from future import standard_library
standard_library.install_aliases()
import os
import random
import time

import http.client
import httplib2
from ssl import SSLError

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.file import Storage

from django.conf import settings


YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube.force-ssl'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
    http.client.IncompleteRead, http.client.ImproperConnectionState,
    http.client.CannotSendRequest, http.client.CannotSendHeader,
    http.client.ResponseNotReady, http.client.BadStatusLine)

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10


class YouTubeInvalidToken(Exception):
    pass


class YouTubeInvalidPrivacyStatus(Exception):
    pass


class YouTubeUnknownID(Exception):
    pass


class YouTubeUploadError(Exception):
    pass


def _youtube():
    try:
        if not os.path.exists(settings.YOUTUBE_TOKEN):
            return None
    except AttributeError:
        return None

    storage = Storage(settings.YOUTUBE_TOKEN)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        if settings.DEBUG:
            return
        raise YouTubeInvalidToken('Invalid token provided by %s' %
                settings.YOUTUBE_TOKEN)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()),
        cache_discovery=False,
    )


# Variable to check if YouTube tokens are properly configured
youtube_configured = _youtube() is not None


# Tue Oct 13 12:11:26 CEST 2015 - Mathias André
# The reason we use custom wrapper to each YouTube API call
# is that it makes it easier to retry upon SSL errors which happen
# frequently with ESO's current firewall.
# In the long term they might not be necessary

def ssl_error_wrapper(func):
    '''
    This decorator catches SSLErrors and retry up to n times to bypass random
    errors with the firewall which generates these errors
    '''
    def wrapper(*args, **kwargs):
        count = 0
        while True:
            try:
                return func(*args, **kwargs)
            except SSLError:
                if count >= 20:
                    break
                count += 1

    return wrapper


@ssl_error_wrapper
def youtube_captions_insert(part, body, media_body):
    response = _youtube().captions().insert(
        part=part,
        body=body,
        media_body=media_body
    ).execute()

    return response


@ssl_error_wrapper
def youtube_captions_list(part, video_id):
    response = _youtube().captions().list(
        part=part,
        videoId=video_id
    ).execute()

    return response


@ssl_error_wrapper
def youtube_captions_update(part, body, media_body):
    response = _youtube().captions().update(
        part=part,
        body=body,
        media_body=media_body
    ).execute()

    snippet = response['snippet']
    if 'reason' in snippet and snippet['reason'] == 'failed':
        raise Exception('Failed: %s' % snippet['failureReason'])

    return response


@ssl_error_wrapper
def youtube_playlistitems_insert(playlist_id, video_id):
    response = _youtube().playlistItems().insert(
        part='snippet',
        body=dict(
            snippet=dict(
                playlistId=playlist_id,
                resourceId=dict(
                    kind='youtube#video',
                    videoId=video_id
                )
            )
        ),
    ).execute()

    return response


@ssl_error_wrapper
def youtube_playlistitems_list(playlist_id):
    response = {'items': []}

    params = dict(
        part='snippet',
        playlistId=playlist_id,
        maxResults=50,
    )

    while True:
        r = _youtube().playlistItems().list(**params).execute()
        response['items'] += r['items']

        try:
            params['pageToken'] = r['nextPageToken']
        except KeyError:
            break

    return response


@ssl_error_wrapper
def youtube_playlists_list():
    response = _youtube().playlists().list(
        part='snippet',
        mine=True,
        maxResults=50
    ).execute()

    return response


@ssl_error_wrapper
def youtube_thumbnails_set(video_id, path):
    response = _youtube().thumbnails().set(
        videoId=video_id,
        media_body=path
    ).execute()

    return response


@ssl_error_wrapper
def youtube_videos_insert(body, media_path):
    response = _youtube().videos().insert(
        part=','.join(list(body.keys())),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(media_path, chunksize=-1, resumable=True)
    )

    return response


@ssl_error_wrapper
def youtube_videos_list(id, part):
    response = _youtube().videos().list(
        id=id,
        part=part
    ).execute()

    return response


@ssl_error_wrapper
def youtube_videos_resumable_upload(insert_request, logger):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            logger.info('Uploading to YouTube...')
            _status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    logger.info('Video id "%s" was successfully uploaded.',
                                response['id'])
                    return response['id']
                else:
                    raise YouTubeUploadError(
                            'The upload failed with an unexpected response: %s'
                            % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = 'A retriable HTTP error %d occurred:\n%s' % \
                            (e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = 'A retriable error occurred: %s' % e

        if error is not None:
            logger.warning(error)
            retry += 1
            if retry > MAX_RETRIES:
                raise YouTubeUploadError('No longer attempting to retry.')

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            logger.warning('Sleeping %f seconds and then retrying...' %
                            sleep_seconds)
            time.sleep(sleep_seconds)


@ssl_error_wrapper
def youtube_videos_update(part, body):
    response = _youtube().videos().update(
        part=part,
        body=body
    ).execute()

    return response
