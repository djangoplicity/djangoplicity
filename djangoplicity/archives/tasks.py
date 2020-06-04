# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from __future__ import with_statement
import glob
import hashlib
import os
import shutil
import time

from celery import current_app
from celery import task
from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from djangoplicity.archives.contrib.security import StaticFilesProtectorCache
from djangoplicity.archives.resources import ResourceManager
from djangoplicity.celery.serialtaskset import str_keys


@task( name="archives.move_file" )
def move_file( src, dst, overwrite=True, sendtask_callback=None, sendtask_tasksetid=None ):
    """
    Celery task for moving a file on a local file system.
    """
    logger = move_file.get_logger()

    logger.info( "Source: %s" % dst )
    logger.info( "Destination: %s" % dst )

    try:
        if not os.path.exists( src ):
            raise Exception( "Source %s does not exist" % src )

        if os.path.exists( dst ):
            if not overwrite:
                raise Exception( "Destination %s already exists" % dst )
            logger.info( "Removing existing file %s at destination" % dst )
            os.remove( dst )
        else:
            dirname = os.path.dirname( dst )
            if not os.path.exists( dirname ):
                os.makedirs( dirname )

        shutil.move( src, dst )
    except Exception, e:
        logger.warning( unicode( e ) )

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task( *args, **str_keys( kwargs ) )


@task( name="archives.move_resources" )
def move_resources( src, dst, overwrite=True, archive_id=None, exclude=[], sendtask_callback=None, sendtask_tasksetid=None ):
    """
    Celery task for moving resources on a local file system.
    """
    logger = move_resources.get_logger()

    if not os.path.exists( src ):
        raise Exception( "Source %s does not exist" % src )

    if not os.path.isdir( src ):
        raise Exception( "Source %s is not a directory" % src )

    if not os.path.exists( dst ):
        raise Exception( "Destination %s does not exist" % dst )

    if not os.path.isdir( dst ):
        raise Exception( "Destination %s is not a directory" % dst )

    srcdirs = _get_dirs( src )
    dstdirs = _get_dirs( dst )

    _create_missing( srcdirs, dstdirs, dst )

    error = None

    for s in srcdirs:
        if s not in exclude:
            try:
                _move_resource( os.path.join( src, s ), os.path.join( dst, s ), archive_id )
            except Exception, e:
                error = e
                logger.exception( "Error moving format %s" % s )
        else:
            logger.info( "Excluding format %s" % s )

    if error:
        raise error

    if archive_id is None:
        # Remove source directory
        shutil.rmtree( src )

    # send_task callback
    if sendtask_callback:
        # We sleep for 30s to give enough time for NFS to catch up in case
        # subsequent task will run on a different server, otherwise we have the risk
        # of getting the information from the placeholder file
        time.sleep(30)

        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task( *args, **str_keys( kwargs ) )


@task( name="archives.delete_resources", ignore_result=True )
def delete_resources( app_label, module_name, object_id, resources, sendtask_callback=None, sendtask_tasksetid=None ):
    """
    Delete specific resource from a model object.
    """
    logger = delete_resources.get_logger()
    obj = None

    try:
        obj = apps.get_model( app_label, module_name ).objects.get( id=object_id )
        logger.debug( "Found %s.%s with id %s " % ( app_label, module_name, object_id ) )
    except ObjectDoesNotExist:
        logger.warning( "Could not find model object %s.%s:%s" % ( app_label, module_name, object_id ) )

    if obj:
        for r in resources:
            if not hasattr( obj, 'resource_%s' % r ):
                continue

            res = getattr( obj, 'resource_%s' % r )
            try:
                if res is not None:
                    if os.path.isdir( res.path ):
                        shutil.rmtree( res.path )
                    else:
                        os.remove( res.path )
            except Exception:
                logger.error( "Error while deleting resource %s for model object %s.%s:%s" % ( r, app_label, module_name, object_id ) )

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task( *args, **str_keys( kwargs ) )


def _get_dirs( path ):
    """ Get all subdirectories in path """
    files = os.listdir( path )
    return filter( lambda x: os.path.isdir( os.path.join( path, x ) ), files )


def _get_missing( src, dst ):
    """ Get all source directories which is not already on destination """
    src = set( src )
    dst = set( dst )
    return list( src - dst )


def _create_missing( srcdirs, dstdirs, dst ):
    """ Create source directories which are not in destination already """
    missing = _get_missing( srcdirs, dstdirs )
    for m in missing:
        os.makedirs( os.path.join( dst, m ) )


def _move_resource( srcpath, dstpath, archive_id ):
    """
    Move all files related to a resource in source path to destination path.
    Will overwrite existing versions on destination.
    """
    try:
        if archive_id is None:
            files = os.listdir( srcpath )
        else:
            files = glob.glob( os.path.join( srcpath, archive_id + '.*' ) )
            if os.path.exists( os.path.join( srcpath, archive_id ) ):
                files.append( os.path.join( srcpath, archive_id ) )

        # Copy all files/folders in source
        for f in files:
            _d, ff = os.path.split(f)

            fsrcpath = os.path.join( srcpath, ff )
            fdstpath = os.path.join( dstpath, ff )

            # Remove already existing files on destination
            if os.path.exists( fdstpath ):
                if os.path.isdir( fdstpath ):
                    shutil.rmtree( fdstpath )
                else:
                    os.remove( fdstpath )

            # Move source to dst

            shutil.move( fsrcpath, fdstpath )
    except Exception, e:
        raise e


@task(name="archives.clear_cache", ignore_result=True)
def clear_archive_list_cache():
    '''
    Clear the cache for all archive list views
    '''
    global_keylist_key = 'global_cache_keys'
    cache_keys = cache.get(global_keylist_key)
    if cache_keys:
        cache.delete_many(cache_keys)
        cache.delete(global_keylist_key)
    StaticFilesProtectorCache.run_async()


@task
def embargo_release_date_task(app_label, module_name, object_id, typ):
    '''
    Check if the object's class has release_date_action defined and execute it
    typ should be 'embargo' or 'release'
    '''
    logger = get_task_logger(__name__)

    try:
        obj = apps.get_model(app_label, module_name).objects.get(pk=object_id)
    except ObjectDoesNotExist:
        logger.warning("Could not find model object %s.%s:%s" % (app_label, module_name, object_id))
        return

    action = '%s_date_action' % typ

    if hasattr(obj, action):
        logger.info('Will run %s action for %s (%s)', typ, app_label, object_id)
        getattr(obj, action)()


@task
def compute_checksums(app_label, module_name, pk, min_size=104857600,
        formats=None, sendtask_callback=None, sendtask_tasksetid=None):
    '''
    Computes sha256 checksum for resources files of at least min_size
    If a list of formats is given then only these checkums are updated
    '''
    logger = get_task_logger(__name__)

    cls = apps.get_model(app_label, module_name)

    try:
        instance = cls.objects.get(pk=pk)
    except ObjectDoesNotExist:
        logger.warning("Could not find model object %s.%s:%s" % (app_label, module_name, pk))
        return

    if formats:
        checksums = instance.checksums
    else:
        checksums = {}

    for r_name in dir(instance.Archive):
        if not isinstance(getattr(instance.Archive, r_name), ResourceManager):
            continue

        if formats and r_name not in formats:
            continue

        resource = getattr(instance, 'resource_%s' % r_name)

        # Skip non-file resources (e.g. zoomable):
        if not resource or not os.path.isfile(resource.path):
            continue

        # Skip files smaller than min_size
        if resource.size < min_size:
            continue

        h = hashlib.sha256()

        with open(resource.path) as f:
            while True:
                buf = f.read(2**20)  # Read 1MB at a time
                if not buf:
                    break
                h.update(buf)

        checksums[r_name] = h.hexdigest()
        logger.info('Computed checksum for "%s (%s)": %s', pk, r_name, checksums[r_name])

    cls.objects.filter(pk=pk).update(checksums=checksums)
    if settings.USE_I18N:
        # Normally this would be done automatically in TranslationModel.save()
        # But we use update to avoid an infinite task loop
        cls.objects.filter(source=pk).update(checksums=checksums)

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task(*args, **str_keys(kwargs))
