# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

"""
Restrict access to an archives static resources

Generates and caches a list of protected resources, access is then checked by
djangoplicity and serving the files themselves is done by NGINX using
X-Accel-Redirect

Install
=======
The ArchiveOptions class for an archive is expected to have
a class defined like this::

    from djangoplicity.archives.contrib import security

    class SomeArchiveOptions( ArchiveOptions ):
        # ...

        class ResourceProtection( object ):
            unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
            staging = ( StagingQuery, security.STAGING_PERMS )
            embargo = ( EmbargoQuery, security.EMBARGO )
            # <name> = ( <ArchiveQuery>, <security level> )

The class must be named ResourceProtection, and each defined
field should be a two-tuple of an archive query and a security level.

A security level should only be defined once per archive.

Lastly make sure that the archives is listed in settings.ARCHIVES::

    ARCHIVES = (
        # ...
        ('djangoplicity.media.models.Image','djangoplicity.media.options.ImageOptions'),
    )


Usage
=====
To update the current static files protection cache run:

    from djangoplicity.archives.contrib.security import StaticFilesProtectorCache
    StaticFilesProtectorCache.run()

This will be done automatically in post_save of any objects inheriting from
ArchiveBase
"""

from builtins import object
from django.conf import settings
from django.core.cache import cache
from djangoplicity.archives.contrib.security.tasks import update_static_files_protection_cache
import logging
import os
import re

logger = logging.getLogger('djangoplicity')

UNPUBLISHED_PERMS = 2
STAGING_PERMS = 3
EMBARGO = 1

PROTECTED_PATH_KEY = '%s:static_protected_paths' % settings.SHORT_NAME
TIMEOUT = 1200


class StaticFilesProtectorCache(object):
    @classmethod
    def run_async(cls):
        """
        Call a background task to do the job instead.
        """
        update_static_files_protection_cache.delay()

    @classmethod
    def run(cls):
        '''
        Generate a dict with path prefix as keys (e.g.: 'images', 'videos')
        and a list of compiled regex as values (e.g.: ur'^videos/[^/]+/ann18036a..*$')
        '''
        protected_paths = {}

        for (model_string, option_string) in settings.ARCHIVES:
            mdl = _do_import(model_string)
            opt = _do_import(option_string)

            # Get directory for current model:
            protected_path = mdl.Archive.Meta.root
            if protected_path[-1] == os.path.sep:
                protected_path = protected_path[:-1]

            # Should only append to protected_path if we actually have some objects to protect
            protected_resources = cls.run_model(mdl, opt, protected_path)
            if protected_resources:
                protected_paths[protected_path] = protected_resources

        # Remove empty values from protected_paths
        protected_paths = {k: v for k, v in protected_paths.items() if v is not None}

        cache.set(PROTECTED_PATH_KEY, protected_paths, TIMEOUT)
        return protected_paths

    @classmethod
    def run_model(cls, model, options, protected_path):
        """
        Run static file protection for one archive
        """

        if not hasattr(options, 'ResourceProtection'):
            return

        # Find all attributes defined on the ResourceProtection class.
        attributes = []
        for attr in dir(options.ResourceProtection):
            if not attr.startswith("__"):
                try:
                    val = getattr(options.ResourceProtection, attr)
                    if len(val) == 2:
                        attributes.append(val)
                except TypeError:
                    pass

        # Get list of allowed IP addresses if resource is restricted
        # TODO?
        # if hasattr(options, 'ResourceInternalOnly'):
            # ips = options.ResourceInternalOnly.ips
        # else:
            # ips = ''

        # Collect queries for each security level
        queries_dict = {}
        for query, security_level in attributes:
            access_level = cls.access_level(security_level)
            if access_level:
                if access_level not in queries_dict:
                    queries_dict[access_level] = []
                queries_dict[access_level].append(query)

        protected_resources = []

        # Loop over found queries to protect
        for query, security_level in attributes:
            qs, _tmp = query(browsers=(None,)).queryset(model, options, None, only_source=True)

            # Eliminate duplicates and generate regular expressions for quick
            # string matching
            for pk in set(qs.all().values_list('id', flat=True)):
                protected_resources.append((re.compile(r'^%s/[^/]+/%s\..*$' % (protected_path, pk)), security_level))

        return protected_resources

    @classmethod
    def access_level(cls, perm):
        """
        Translate an archive security level into access group.
        """
        if perm in [ UNPUBLISHED_PERMS, STAGING_PERMS ]:
            return '2'
        elif perm == EMBARGO:
            return '1'
        else:
            logger.warning("Access choice could not be determined. Got %s", perm)
            return None


#
# Helper methods
#
def _do_import(s):
    """
    Import a an archive model defined by a string - e.g. "djangoplicity.media.models.Image".
    """
    (name, _dot, cls) = s.rpartition('.')
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return getattr(mod, cls)
