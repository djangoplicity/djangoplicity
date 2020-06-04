from __future__ import unicode_literals

from djangoplicity.archives.contrib.security import StaticFilesProtectorCache, \
    PROTECTED_PATH_KEY, EMBARGO, STAGING_PERMS, UNPUBLISHED_PERMS

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseBadRequest, BadHeaderError
from django.utils.encoding import filepath_to_uri

import logging


logger = logging.getLogger(__name__)


def serve_static_file(request, path):
    '''
    This function will check whether or not the requested path is protected
    and delegate the actual serving of the file
    '''
    protected_paths = cache.get(PROTECTED_PATH_KEY)

    if protected_paths is None:
        logger.info('Cache empty for %s', PROTECTED_PATH_KEY)
        protected_paths = StaticFilesProtectorCache.run()

    # If ARCHIVE_ROOT is defined we need to take it into account in the prefix
    if settings.ARCHIVE_ROOT and path.startswith(settings.ARCHIVE_ROOT):
        prefix = settings.ARCHIVE_ROOT + path.split('/')[1]
    else:
        prefix = path.split('/')[0]

    try:
        protected_archives = protected_paths[prefix]
    except KeyError:
        # path prefix is not protected
        return serve_file(request, path)

    for (regexp, security_level) in protected_archives:
        if regexp.match(path):
            # Resource is protected
            if security_level == UNPUBLISHED_PERMS:
                if not request.user.is_staff:
                    return HttpResponseRedirect('%s?next=%s%s' % (settings.LOGIN_URL, settings.MEDIA_URL, path))
            elif security_level == STAGING_PERMS:
                if not request.user.is_staff:
                    return HttpResponseRedirect('%s?next=%s%s' % (settings.LOGIN_URL, settings.MEDIA_URL, path))
            elif security_level == EMBARGO:
                if not request.user.is_active:
                    return HttpResponseRedirect('%s?next=%s%s' % (settings.LOGIN_URL, settings.MEDIA_URL, path))
            else:
                # This shouldn't happen
                logger.warning('Unkown security_level (%s) for path: "%s"', security_level, path)
            break

    return serve_file(request, path)


def serve_file(request, path):
    '''
    Actually serve the file using NGINX's X-Accel-Redirect'
    '''
    response = HttpResponse()
    response['Content-Type'] = ''
    if not path.startswith('/'):
        path = '/' + path

    # This ensures that unicode characters are encoded correctly
    path = filepath_to_uri(path)

    try:
        response['X-Accel-Redirect'] = '/protected_archives%s' % path
    except BadHeaderError as e:
        # This happens if the path is invalid (typically strange utf characters
        # are passed)
        logger.info('BadHeaderError: %s', e)
        return HttpResponseBadRequest()

    return response
